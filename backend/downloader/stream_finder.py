"""
stream_finder.py Ã¢â‚¬â€ TÃƒÂ¼rk anime/dizi sitelerinden gerÃƒÂ§ek video URL'si ÃƒÂ§Ã„Â±kar.

Strateji:
  1. CF korumalÃ„Â± site Ã¢â€ â€™ nodriver ile cf_clearance al (23 saat cache) Ã¢â€ â€™ curl-cffi ile sayfa ÃƒÂ§ek
  2. cookies.txt varsa Ã¢â€ â€™ requests + CF bypass Ã¢â€ â€™ iframe/embed URL ÃƒÂ§Ã„Â±kar
  3. JS-render gereken siteler Ã¢â€ â€™ Playwright fallback
  4. HiÃƒÂ§biri ÃƒÂ§alÃ„Â±Ã…Å¸mazsa Ã¢â€ â€™ orijinal episode URL'yi dÃƒÂ¶ndÃƒÂ¼r (yt-dlp denesin)

Desteklenen siteler:
  - dizibox.so/live   (nodriver CF bypass Ã¢â€ â€™ curl-cffi)
   - hdfilmcehennemi.* (site parser Ã¢â€ â€™ PW click + network interception)
   - dizigom.*         (site parser Ã¢â€ â€™ PW click + network interception)
   - sezonlukdizi.*    (site parser Ã¢â€ â€™ generic PW)
   - fullhdfilmizlesene.* (site parser Ã¢â€ â€™ generic PW)
   - tranimeizle.co    (nodriver CF bypass Ã¢â€ â€™ curl-cffi)
  - diziwatch.com     (cookies.txt)
  - turkanime.co/tv   (Playwright)
"""
import os
import re
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Cookies dosyalarÃ„Â± dizini
_COOKIES_DIR = Path(__file__).parent.parent.parent / "cookies"

# Playwright'Ã„Â±n MP4 URL'sine yaptÃ„Â±Ã„Å¸Ã„Â± isteÃ„Å¸in header'larÃ„Â± (CF cookie dahil)
# anime.py yt-dlp ÃƒÂ§aÃ„Å¸rÃ„Â±sÃ„Â±nda kullanÃ„Â±r; her find_stream_url ÃƒÂ§aÃ„Å¸rÃ„Â±sÃ„Â±nda sÃ„Â±fÃ„Â±rlanÃ„Â±r
# S-166: global dict YOK — ContextVar ile task-basina izole (paralel indirmede
# capraz kirlenme/yaris fix'i). anime.py ayni async task'ta okudugu icin gorunur.
import contextvars as _cv
_SESSION_HEADERS: _cv.ContextVar[dict] = _cv.ContextVar("kw_sess_headers", default={})
_SESSION_COOKIES: _cv.ContextVar[dict] = _cv.ContextVar("kw_sess_cookies", default={})


def _sess_headers() -> dict:
    return _SESSION_HEADERS.get()


def _sess_cookies() -> dict:
    return _SESSION_COOKIES.get()


def _sess_reset() -> None:
    _SESSION_HEADERS.set({})
    _SESSION_COOKIES.set({})

# CF bypass: nodriver ile alÃ„Â±nan cookie cache'i
# domain Ã¢â€ â€™ (cookies_dict, user_agent, timestamp)
_cf_cache: dict[str, tuple[dict, str, float]] = {}
_CF_CACHE_TTL = 23 * 3600  # 23 saat (CF cookie ÃƒÂ¶mrÃƒÂ¼ ~24 saat)

# Bu domainler nodriver cf_clearance + curl-cffi CF bypass gerektirir
# nodriver ilk seferde CF challenge'Ã„Â± ÃƒÂ§ÃƒÂ¶zer, cookie 23 saat cache'lenir
# curl-cffi cookie ile direkt sayfayÃ„Â± ÃƒÂ§eker (hÃ„Â±zlÃ„Â±, browsersÃ„Â±z)
_CF_SITES = {
    "dizibox.live",
    "dizibox.so",
    "hdfilmcehennemi.name", "hdfilmcehennemi.nl", "hdfilmcehennemi.art", "hdfilmcehennemi.tv",
    "hdfilmcehennemi.com", "hdfilmcehennemi.gg",
    "hdfilmcehennemi.ws", "hdfilmcehennemi.now",
    "dizigom.info", "dizigom.com", "dizigom.vip", "dizigom.net",
    "dizigom.love", "dizigom.tv", "dizigom1.com",
    "tranimeizle.co",
    "tranimeizle.io",
    "tranimeizle.xyz",
}

# nodriver Chromium binary yolu — platform-gercek cozumleyici (S-166 fix)
from backend.downloader.browser import resolve_chromium_bin
_CHROMIUM_BIN = resolve_chromium_bin()

# Bu domainlerden dÃƒÂ¶nen embed URL'leri ÃƒÂ¶lÃƒÂ¼/ÃƒÂ§alÃ„Â±Ã…Å¸mÃ„Â±yor kabul edilir
# (rotor URL'leri dÃƒÂ¶ndÃƒÂ¼ren eski/virman siteler iÃƒÂ§in)
_DEAD_EMBED_DOMAINS = ("aso1.net", "srv.aso1.net", "media.aso1.net")


def get_session_header_args(actual_url: str) -> list[str]:
    """Playwright'Ã„Â±n MP4 isteÃ„Å¸indeki header'larÃ„Â± yt-dlp --add-header listesi olarak dÃƒÂ¶ndÃƒÂ¼r."""
    headers = _sess_headers()
    if not headers:
        return []
    domain = _domain(actual_url)
    # Sadece bu URL domain'i iÃƒÂ§in yakalanmÃ„Â±Ã…Å¸sa kullan
    if headers.get("_domain") == domain:
        skip = {"_domain", "host", "content-length", "te", "accept-encoding", "range"}
        args: list[str] = []
        for k, v in headers.items():
            if k.startswith("_") or k in skip:
                continue
            args += ["--add-header", f"{k}:{v}"]
        return args
    return []

# Embed player URL'lerini tanÃ„Â±yan kalÃ„Â±plar (yt-dlp destekleri)
_EMBED_PATTERNS = [
    r"(https?://(?:www\.)?filemoon\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?vidmoly\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?doodstream\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?streamtape\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?gounlimited\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?mixdrop\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://(?:www\.)?upstream\.[a-z]+/[^\s\"'<>]+)",
    r"(https?://player\.[^\s\"'<>]+\.(?:m3u8|mp4)[^\s\"'<>]*)",
    r"(https?://[^\s\"'<>]+\.m3u8[^\s\"'<>]*)",
]

# Site Ã¢â€ â€™ cookies dosyasÃ„Â± adÃ„Â± mapping
_SITE_COOKIES = {
    "tranimeizle.co":     "tranimeizle_cookies.txt",
    "tranimeizle.io":     "tranimeizle_cookies.txt",
    "tranimeizle.xyz":     "tranimeizle_cookies.txt",
    "turkanime.co":       "turkanime_cookies.txt",
    "turkanime.tv":       "turkanime_cookies.txt",
    "turkanime.com.tr":   "turkanime_cookies.txt",
    "diziwatch.com":      "diziwatch_cookies.txt",
    "anizm.net":          "anizm_cookies.txt",
    "dizibox.live":       "dizibox_cookies.txt",
    "dizibox.so":         "dizibox_cookies.txt",
    "hdfilmcehennemi.nl": "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.art": "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.tv":  "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.com": "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.name": "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.gg":   "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.ws":   "hdfilmcehennemi_cookies.txt",
    "hdfilmcehennemi.now":  "hdfilmcehennemi_cookies.txt",
    "dizigom.info":  "dizigom_cookies.txt",
    "dizigom.com":   "dizigom_cookies.txt",
    "dizigom.vip":   "dizigom_cookies.txt",
    "dizigom.net":   "dizigom_cookies.txt",
    "dizigom.love":  "dizigom_cookies.txt",
    "dizigom.tv":    "dizigom_cookies.txt",
    "dizigom1.com":  "dizigom_cookies.txt",
}

# Bu domainler iframe olarak bulunsa bile atlanÃ„Â±r (lisanslÃ„Â± oynatÃ„Â±cÃ„Â±lar, reklam aÃ„Å¸larÃ„Â±)
_SKIP_IFRAME_DOMAINS = (
    "crunchyroll.com", "vrv.co", "funimation.com",
    "google", "dtscout", "adservice", "doubleclick", "googlesyndication",
)

# Bu domainler JS-render gerektirir Ã¢â‚¬â€ requests fetch atla, direkt Playwright'a git
_FORCE_PLAYWRIGHT = {
    "dizibox.live",
    "dizibox.so",
    "hdfilmcehennemi.name", "hdfilmcehennemi.nl", "hdfilmcehennemi.art", "hdfilmcehennemi.tv",
    "hdfilmcehennemi.com", "hdfilmcehennemi.gg",
    "hdfilmcehennemi.ws", "hdfilmcehennemi.now",
    "dizigom.info", "dizigom.com", "dizigom.vip", "dizigom.net",
    "dizigom.love", "dizigom.tv", "dizigom1.com",
    "turkanime.tv",
    "setfilmizle.uk", "setfilmizle.com",
    "animexe.com",
}

# Bu domainler Cloudflare Managed Challenge kullanÃ„Â±r Ã¢â€ â€™ nodriver (gerÃƒÂ§ek Chrome) gerekiyor
# Playwright kolayca algÃ„Â±lanÃ„Â±yor; nodriver CF'yi aÃ…Å¸Ã„Â±p JS-render edilmiÃ…Å¸ HTML alÃ„Â±yor
_NODRIVER_HTML_SITES = {
}

# Site-spesifik popup kapatma selector'larÃ„Â± (play butonundan Ãƒâ€“NCE kapatÃ„Â±lÃ„Â±r)
_POPUP_CLOSE_SELECTORS = {
    "turkanime.tv":     ["button.site-popup-close", ".popup-close", "#popup-close", ".modal-close"],
    "turkanime.com.tr": ["button.site-popup-close", ".popup-close", "#popup-close", ".modal-close"],
    "hdfilmcehennemi": [".modal-close", ".popup-close", "button.close", ".close-btn"],
    "dizigom": [".modal-close", ".popup-close", "button.close"],
    "setfilmizle": [".modal-close", ".popup-close", ".auth-modal-close", "#login-modal .close", ".show-register-modal .close"],
}

# Site-spesifik play butonu CSS selector'larÃ„Â± (Playwright iÃƒÂ§in)
_PLAY_BUTTON_SELECTORS = {
    "dizibox.live":       [".play-btn", "#play-btn", "[data-action='play']", "button.btn-play"],
    "dizibox.so":         [".play-btn", "#play-btn", "[data-action='play']", "button.btn-play"],
    "hdfilmcehennemi": [".play-that-video", "[aria-label='Play video']", ".play-button", "#play", ".jw-icon-playback"],
    "dizigom": [".player-area iframe", ".video-js", "#player iframe", ".film-player iframe"],
    # IndexIcerik AJAX Ã¢â€ â€™ iframe inject eder; ilk sunucu butonunu tÃ„Â±kla
    "turkanime.tv":       ["button.btn.btn-sm.btn-default", ".btn-server:first-child", "[data-video]:first-child"],
    "turkanime.com.tr":   ["button.btn.btn-sm.btn-default", ".btn-server:first-child", "[data-video]:first-child"],
    "tranimeizle.co":     [
        ".players a:first-child",
        ".eps-server:first-child a",
        ".serverList li:first-child a",
        "ul.servers li:first-child a",
        "#playerSezon .btn:first-child",
        ".player-options a:first-child",
        "[data-video]:first-child",
    ],
    # tranimaci.com: JS PoW challenge ÃƒÂ§ÃƒÂ¶zÃƒÂ¼ldÃƒÂ¼kten sonra player yÃƒÂ¼klenir
    "tranimaci.com": [
        ".source-btn:first-child",
        ".server-btn:first-child",
        ".btn-server:first-child",
        "ul.server-list li:first-child a",
        "[data-source]:first-child",
        ".player-source:first-child",
    ],
    # setfilmizle.uk: #fimcnt_pb play butonu Ã¢â€ â€™ AJAX Ã¢â€ â€™ iframe yÃƒÂ¼klenir
    "setfilmizle.uk": [
        "#fimcnt_pb",
        ".play-button",
        ".playex",
        ".idTabs.sourceslist li:first-child a",
        ".player_sist .idTabs li:first-child a",
        ".idTabs li:first-child a",
    ],
    "setfilmizle.com": [
        "#fimcnt_pb",
        ".play-button",
        ".playex",
        ".idTabs.sourceslist li:first-child a",
        ".player_sist .idTabs li:first-child a",
        ".idTabs li:first-child a",
    ],
}


def _domain(url: str) -> str:
    """URL'den ana domain ÃƒÂ§Ã„Â±kar."""
    host = urlparse(url).netloc.removeprefix("www.")
    return host


def _cookies_path(url: str) -> Optional[Path]:
    """Bu URL iÃƒÂ§in cookies.txt dosyasÃ„Â± var mÃ„Â±?"""
    domain = _domain(url)
    for site, fname in _SITE_COOKIES.items():
        if domain.endswith(site):
            p = _COOKIES_DIR / fname
            if p.exists():
                return p
    # Genel fallback
    generic = _COOKIES_DIR / "cookies.txt"
    if generic.exists():
        return generic
    return None


def _extract_embed_from_html(html: str) -> Optional[str]:
    """HTML iÃƒÂ§inden ilk embed/player URL'sini ÃƒÂ§Ã„Â±kar."""
    # iframe src ara
    iframes = re.findall(
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    for src in iframes:
        if any(skip in src for skip in _SKIP_IFRAME_DOMAINS):
            continue
        # Protocol-relative URL (//) Ã¢â€ â€™ https: ekle
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            logger.info("iframe bulundu: %s", src[:80])
            return src

    # Embed pattern'leri ara
    for pat in _EMBED_PATTERNS:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            logger.info("embed pattern bulundu: %s", m.group(1)[:80])
            return m.group(1)

    return None


def _extract_mp4_from_html(html: str) -> Optional[str]:
    """HTML/JS iÃƒÂ§inden direkt MP4 URL'si ÃƒÂ§Ã„Â±kar (CDN token'lÃ„Â± URL'ler dahil)."""
    patterns = [
        r'"(https?://[^\s"\'<>\\]+\.mp4\?[^\s"\'<>\\]{20,})"',
        r"'(https?://[^\s\"'<>\\]+\.mp4\?[^\s\"'<>\\]{20,})'",
        r'(https?://cdn\d*\.[a-z0-9.-]+/[^\s"\'<>\\]+\.mp4\?[^\s"\'<>\\]{10,})',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            url = m.group(1)
            logger.info("Direkt MP4 URL bulundu (HTML/JS): %s", url[:80])
            return url
    return None


async def _nodriver_get_html(url: str, wait_secs: int = 20) -> Optional[str]:
    """nodriver (undetected Chrome) ile CF Managed Challenge aÃ…Å¸Ã„Â±lÃ„Â±r, JS-render HTML alÃ„Â±nÃ„Â±r."""
    import nodriver as uc
    browser = None
    try:
        logger.info("nodriver baÃ…Å¸lÃ„Â±yor: %s", url[:80])
        browser = await uc.start(
            headless=True,
            browser_executable_path=_CHROMIUM_BIN,
            no_sandbox=True,
        )
        tab = await browser.get(url)
        await asyncio.sleep(wait_secs)
        html = await tab.get_content()
        title = await tab.evaluate("document.title")
        logger.info("nodriver title: %s (html len=%d)", title, len(html))
        if "security verification" in (title or "").lower() or len(html) < 1000:
            logger.warning("nodriver: CF challenge geÃƒÂ§ilemedi (%s)", title)
            return None
        return html
    except Exception as exc:
        logger.error("nodriver_get_html hatasÃ„Â±: %s", exc)
        return None
    finally:
        if browser:
            try:
                browser.stop()
            except Exception:
                pass


_SITE_PARSER_DOMAINS = {
    "hdfilmcehennemi": "hdfilmcehennemi",
    "dizigom": "dizigom",
    "sezonlukdizi": "sezonlukdizi",
    "fullhdfilmizlesene": "fullhdfilmizlesene",
    "setfilmizle": "setfilmizle",
}

_ANIME_ONLY_DOMAINS = {"tranimaci.com", "tranimeizle.co", "tranimeizle.xyz", "turkanime.tv", "turkanime.com.tr", "anizm.net", "animexe.com"}


from backend.scraper.tag_extractor import extract_site_tags


def _extract_tags_from_html(html: str, domain: str) -> list[str]:
    """Domain iÃƒÂ§eriÃ„Å¸ine gÃƒÂ¶re sayfa HTML'den tÃƒÂ¼r etiketi ÃƒÂ§Ã„Â±kar."""
    site_key = ""
    for key in _SITE_PARSER_DOMAINS:
        if key in domain:
            site_key = key
            break
    if not site_key:
        return []
    try:
        return extract_site_tags(site_key, html, domain)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Tag extraction failed for %s: %s", domain, exc)
        return []


async def _try_site_parser(domain: str, url: str) -> dict:
    """Site-specific parser dene (Playwright click + network interception)."""
    result = {"stream_url": None, "tags": []}
    for site_key, site_name in _SITE_PARSER_DOMAINS.items():
        if site_key in domain:
            from backend.scraper.parsers import parse_url_with_tags
            logger.info("Site parser (tags) deneniyor: %s Ã¢â€ â€™ %s", site_name, url[:60])
            try:
                data = await parse_url_with_tags(site_name, url)
                if data and data.get("stream_url"):
                    logger.info("Site parser video URL buldu: %s", data["stream_url"][:80])
                    result["stream_url"] = data["stream_url"]
                    result["tags"] = data.get("tags", [])
                    return result
                logger.warning("Site parser embed bulamadi: %s", site_name)
                if data and data.get("tags"):
                    result["tags"] = data["tags"]
            except Exception as e:
                logger.error("Site parser hatasi (%s): %s", site_name, e)
            break
    return result


_DEAD_DOMAIN_TTL = 300  # sn
_dead_domain_cache: dict[str, float] = {}


async def _domain_is_dead(domain: str) -> bool:
    """DB'de is_dead isaretli site mi? (S-166 hizli-fail; 5dk in-process cache)"""
    import time
    now = time.monotonic()
    hit = _dead_domain_cache.get(domain)
    if hit is not None and now - hit < _DEAD_DOMAIN_TTL:
        return True
    if hit is not None:
        return False
    try:
        from backend.database import AsyncSessionLocal
        from sqlalchemy import select
        from backend.models import Site
        async with AsyncSessionLocal() as db:
            r = await db.execute(
                select(Site.id).where(
                    Site.is_dead == True,  # noqa: E712
                    Site.site_url.like(f"%{domain}%"),
                ).limit(1)
            )
            dead = r.scalar_one_or_none() is not None
        _dead_domain_cache[domain] = now if dead else now - _DEAD_DOMAIN_TTL + 60
        return dead
    except Exception:
        return False


async def find_stream_url_with_tags(episode_url: str, media_type: str = "anime") -> tuple[str, list[str]]:
    """
    find_stream_url'un zengin versiyonu: video URL + kaynak site etiketleri dÃƒÂ¶ndÃƒÂ¼r.
    media_type: "anime", "series", "movie", "cartoon" Ã¢â‚¬â€ anime-only domain'leri filtreler.
    """
    domain = _domain(episode_url)

    # 00. Olu siteler hizli-fail (S-166): DB is_dead -> 4-mirror zincirine hic girme
    if await _domain_is_dead(domain):
        logger.warning("OLU SITE atlaniyor (is_dead isaretli): %s", domain)
        return "", []

    _sess_reset()
    source_tags: list[str] = []
    is_anime_domain = any(domain.endswith(d) for d in _ANIME_ONLY_DOMAINS)

    # Anime-only domain kontrolÃƒÂ¼: uyuÃ…Å¸mazlÃ„Â±k varsa atla, sonraki site/yÃƒÂ¶nteme bÃ„Â±rak
    if media_type not in ("anime",) and is_anime_domain:
        msg = (f"MEDYA TÃ„Â°PÃ„Â° UYUÃ…ÂMAZLIÃ„ÂI (atlanÃ„Â±yor): '{media_type}' tipi iÃƒÂ§erik "
               f"anime sitesi ({domain}) kullanamaz. "
               f"Sonraki uyumlu site denenecek.")
        logger.warning(msg)
        return "", []

    # 0. Site-spesifik parser dene (dizigom / fullhdfilmizlesene)
    try:
        parser_result = await _try_site_parser(domain, episode_url)
        if parser_result.get("stream_url"):
            return parser_result["stream_url"], parser_result.get("tags", [])
        source_tags = parser_result.get("tags", [])
    except Exception:
        pass

    # 1. Cloudflare Managed Challenge siteleri: nodriver ile JS-render HTML al
    if any(domain.endswith(d) for d in _NODRIVER_HTML_SITES):
        logger.info("nodriver HTML site: %s", domain)
        html = await _nodriver_get_html(episode_url, wait_secs=20)
        if html:
            embed = _extract_mp4_from_html(html) or _extract_embed_from_html(html)
            if embed:
                tags = _extract_tags_from_html(html, domain) or source_tags
                logger.info("nodriver HTML embed buldu: %s", embed[:80])
                return embed, tags
            logger.warning("nodriver HTML alÃ„Â±ndÃ„Â± ama embed bulunamadÃ„Â± (len=%d)", len(html))
            source_tags = source_tags or _extract_tags_from_html(html, domain)
        else:
            logger.warning("nodriver HTML alÃ„Â±namadÃ„Â±, Playwright fallback deneniyor")

    # 2. CF korumalÃ„Â± site: nodriver cf_clearance + curl-cffi fetch
    if any(domain.endswith(d) for d in _CF_SITES):
        logger.info("CF site tespit edildi (%s) Ã¢â‚¬â€ nodriver bypass deneniyor", domain)
        try:
            html = await _fetch_with_cf_bypass(episode_url)
            if html:
                url = _extract_mp4_from_html(html)
                if not url:
                    url = _extract_embed_from_html(html)
                if url:
                    tags = _extract_tags_from_html(html, domain) or source_tags
                    logger.info("CF bypass URL buldu: %s", url[:80])
                    return url, tags
                logger.warning("CF bypass HTML alÃ„Â±ndÃ„Â± ama URL bulunamadÃ„Â± (len=%d)", len(html))
                source_tags = source_tags or _extract_tags_from_html(html, domain)
        except Exception as exc:
            logger.error("CF bypass hatasÃ„Â±: %s", exc)

    force_pw = any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT)

    # 3. Cookies.txt varsa dene
    if not force_pw:
        cookies_file = _cookies_path(episode_url)
        if cookies_file:
            logger.info("Cookies dosyasÃ„Â± bulundu: %s", cookies_file)
            try:
                html = await _fetch_with_cookies(episode_url, cookies_file)
                if html:
                    embed = _extract_embed_from_html(html)
                    if embed:
                        tags = _extract_tags_from_html(html, domain) or source_tags
                        return embed, tags
                    logger.warning("HTML alÃ„Â±ndÃ„Â± ama embed bulunamadÃ„Â± (len=%d)", len(html))
                    source_tags = source_tags or _extract_tags_from_html(html, domain)
            except Exception as exc:
                logger.error("stream_finder fetch hatasÃ„Â±: %s", exc)
    else:
        logger.info("JS-render gerekli site (%s) Ã¢â‚¬â€ Playwright'a yÃƒÂ¶nlendiriliyor", domain)

    # 4. Playwright: JS-render + aÃ„Å¸ isteÃ„Å¸i izleme (fallback)
    if "turkanime.tv" in domain or "turkanime.com.tr" in domain:
        pw_timeout = 60000
    elif "tranimaci.com" in domain:
        pw_timeout = 45000
    elif "setfilmizle.uk" in domain or "setfilmizle.com" in domain:
        pw_timeout = 30000
    else:
        pw_timeout = 15000
    try:
        embed = await _playwright_find_embed(episode_url, timeout_ms=pw_timeout)
        if embed:
            logger.info("Playwright embed buldu: %s", embed[:80])
            return embed, source_tags
    except Exception as exc:
        logger.warning("Playwright fallback baÃ…Å¸arÃ„Â±sÃ„Â±z: %s", exc)

    # tranimaci.com baÃ…Å¸arÃ„Â±sÃ„Â±z Ã¢â€ â€™ _resolve_tranimaci ÃƒÂ¶zel ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m dene
    if "tranimaci.com" in domain:
        logger.info("tranimaci.com ÃƒÂ¶zel ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m deneniyor (_resolve_tranimaci)")
        resolved = await _resolve_tranimaci(episode_url)
        if resolved:
            logger.info("tranimaci ÃƒÂ§ÃƒÂ¶zÃƒÂ¼ldÃƒÂ¼: %s", resolved[:80])
            return resolved, source_tags
        # mirror siteleri dene
        for mirror in ("turkanime.tv", "tranimeizle.xyz", "tranimeizle.co", "turkanime.com.tr"):
            mirror_url = episode_url.replace("tranimaci.com", mirror)
            if mirror_url != episode_url:
                logger.info("tranimaci.com mirror deneniyor: %s", mirror)
                mirror_domain = _domain(mirror_url)
                try:
                    if any(mirror_domain.endswith(d) for d in _CF_SITES):
                        html = await _fetch_with_cf_bypass(mirror_url)
                        if html:
                            embed = _extract_mp4_from_html(html) or _extract_embed_from_html(html)
                            if embed:
                                logger.info("Mirror embed buldu (%s): %s", mirror, embed[:80])
                                return embed, source_tags
                    pw_timeout = 60000 if "turkanime" in mirror else 30000
                    embed = await _playwright_find_embed(mirror_url, timeout_ms=pw_timeout)
                    if embed:
                        logger.info("Mirror PW embed buldu (%s): %s", mirror, embed[:80])
                        return embed, source_tags
                except Exception as exc:
                    logger.warning("Mirror %s baÃ…Å¸arÃ„Â±sÃ„Â±z: %s", mirror, exc)

    logger.info("Embed bulunamadÃ„Â±, orijinal URL kullanÃ„Â±lÃ„Â±yor: %s", episode_url[:60])
    return episode_url, source_tags


async def find_stream_url(episode_url: str, media_type: str = "anime") -> str:
    """
    Episode sayfasÃ„Â±ndan gerÃƒÂ§ek video/embed URL'si dÃƒÂ¶ndÃƒÂ¼r.
    SÃ„Â±ra: site parser Ã¢â€ â€™ nodriver HTML Ã¢â€ â€™ CF bypass Ã¢â€ â€™ cookies Ã¢â€ â€™ Playwright Ã¢â€ â€™ orijinal URL.
    """
    url, _ = await find_stream_url_with_tags(episode_url, media_type)
    return url


async def _nodriver_get_cookies(domain: str, base_url: str) -> tuple[dict, str]:
    """
    nodriver ile siteye git, tÃƒÂ¼m cookie'leri + user_agent al. 23 saat cache'lenir.
    CF Turnstile olan siteler iÃƒÂ§in cf_clearance dahil; olmayanlarda session cookie'leri alÃ„Â±r.
    """
    cached = _cf_cache.get(domain)
    if cached:
        cookies_dict, ua, ts = cached
        if time.time() - ts < _CF_CACHE_TTL:
            logger.info("nodriver cookie cache'den kullanÃ„Â±ldÃ„Â±: %s", domain)
            return cookies_dict, ua

    import nodriver as uc
    logger.info("nodriver baÃ…Å¸lÃ„Â±yor: %s (ilk seferinde ~10sn sÃƒÂ¼rer)", domain)
    browser = await uc.start(
        headless=True,
        browser_executable_path=_CHROMIUM_BIN,
        no_sandbox=True,
    )
    cookies_dict: dict = {}
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
    try:
        page = await browser.get(base_url)
        await asyncio.sleep(10)
        raw_cookies = await browser.cookies.get_all()
        cookies_dict = {c.name: c.value for c in raw_cookies}
        cf_ok = "cf_clearance" in cookies_dict
        logger.info(
            "nodriver tamamlandÃ„Â±: %s | %d cookie | cf_clearance=%s",
            domain, len(cookies_dict), cf_ok,
        )
        try:
            ua_js = await page.evaluate("navigator.userAgent")
            if ua_js:
                user_agent = ua_js
        except Exception:
            pass
        _cf_cache[domain] = (cookies_dict, user_agent, time.time())
    except Exception as exc:
        logger.error("nodriver hatasÃ„Â±: %s", exc)
    finally:
        browser.stop()
    return cookies_dict, user_agent


async def _fetch_with_cf_bypass(url: str) -> Optional[str]:
    """nodriver cookie'leri + curl-cffi ile CF korumalÃ„Â± sayfayÃ„Â± getir."""
    from curl_cffi.requests import AsyncSession

    domain = _domain(url)
    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
    cookies_dict, user_agent = await _nodriver_get_cookies(domain, base_url)
    if not cookies_dict:
        return None

    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        "Referer": base_url,
    }
    try:
        async with AsyncSession(impersonate="chrome131") as s:
            resp = await s.get(url, headers=headers, cookies=cookies_dict, timeout=20)
            if resp.status_code == 200:
                text = resp.text
                if "challenge" not in resp.url.lower() and "captcha" not in text[:500].lower():
                    return text
                logger.warning("CF yeniden challenge (%s) Ã¢â‚¬â€ cache temizleniyor", domain)
                _cf_cache.pop(domain, None)
            else:
                logger.warning("curl-cffi %s Ã¢â€ â€™ HTTP %d", url[:60], resp.status_code)
    except Exception as exc:
        logger.error("curl-cffi fetch hatasÃ„Â±: %s", exc)
    return None


async def _fetch_with_cookies(url: str, cookies_file: Path) -> Optional[str]:
    """requests_html veya requests + cookies ile sayfa getir."""
    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        "Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
    }

    cookies = _parse_netscape_cookies(cookies_file, _domain(url))

    resp = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: requests.get(url, headers=headers, cookies=cookies, timeout=15, allow_redirects=True)
    )

    if resp.status_code == 200 and "captcha" not in resp.url.lower() and "challenge" not in resp.url.lower():
        return resp.text
    logger.warning("Sayfa alÃ„Â±namadÃ„Â±: status=%s url=%s", resp.status_code, resp.url[:80])
    return None


def _parse_netscape_cookies(cookies_file: Path, domain: str) -> dict:
    """Netscape format cookies.txt Ã¢â€ â€™ {name: value} dict (domain filtreli)."""
    cookies: dict = {}
    try:
        for line in cookies_file.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            cookie_domain, _, path, secure, expires, name, value = parts[:7]
            cookie_domain_clean = cookie_domain.lstrip(".").removeprefix("www.")
            if domain.endswith(cookie_domain_clean) or cookie_domain_clean.endswith(domain):
                cookies[name] = value
    except Exception as exc:
        logger.error("Cookie parse hatasÃ„Â±: %s", exc)
    return cookies


def get_yt_dlp_cookies_arg(episode_url: str) -> list[str]:
    """yt-dlp iÃƒÂ§in --cookies argÃƒÂ¼manÃ„Â± dÃƒÂ¶ndÃƒÂ¼r (dosya varsa)."""
    p = _cookies_path(episode_url)
    if p:
        return ["--cookies", str(p)]
    return []


def get_session_cookies_arg(embed_url: str, episode_url: str = "") -> list[str]:
    """Playwright session cookie'lerini yt-dlp --add-header Cookie olarak dÃƒÂ¶ndÃƒÂ¼r.
    
    embed_url: tespit edilen embed/video URL'si
    episode_url: orijinal episode sayfasÃ„Â± URL'si (cookie'ler bu domainden alÃ„Â±nÃ„Â±r)
    """
    domain = _domain(episode_url or embed_url)
    cookie_str = _sess_cookies().get(domain)
    if cookie_str:
        return ["--add-header", f"Cookie:{cookie_str}"]
    return []


async def _playwright_find_embed(episode_url: str, timeout_ms: int = 15000) -> Optional[str]:
    """
    Playwright headless chromium ile sayfayÃ„Â± JS-render et, embed/video URL ÃƒÂ§Ã„Â±kar.
    JS-render gerektiren siteler (tranimaci.com, dizibox.live, hdfilmcehennemi.nl vb.) iÃƒÂ§in.
    """
    from playwright.async_api import async_playwright

    found_embed: list[str] = []
    domain = _domain(episode_url)
    html = ""
    http_status: Optional[int] = None

    _KNOWN_PLAYERS = (
        "filemoon", "vidmoly", "doodstream", "streamtape", "voe.sx",
        "speedfiles", "sibnet", "ok.ru", "fembed", "upstream",
        "rapidvid", "mixdrop", "gounlimited", "mp4upload",
        "odnoklassniki", "mail.ru", "vk.com/video",
        "dizibox.live/embed", "dizibox.so/embed",
        "hdfilmcehennemi",
        "dizigom",
        "pichive.online/iframe", "aso1.net",
        "anizmplayer.com", "media.aso",
        "fastplay.mom",
    )

    def _is_embed(url: str) -> bool:
        # JS/CSS dosyalarÃ„Â± ve analytics/tracking atla
        parsed_path = url.split("?")[0].split("#")[0].lower()
        if parsed_path.endswith((".js", ".css", ".woff", ".woff2", ".png", ".ico", ".svg", ".json")):
            return False
        if any(k in url for k in (".m3u8", "/hls/", ".mp4", ".mpd")):
            return True
        if "manifest" in url:
            return True
        if "/iframe.php" in url or "/embed/" in url or "/player/" in url or "/ifr.html" in url:
            return True
        return any(p in url for p in _KNOWN_PLAYERS)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
        )

        # Cookies.txt varsa Playwright context'e yÃƒÂ¼kle (turkanime.tv gibi force_playwright siteleri iÃƒÂ§in)
        _pw_cookies_file = _cookies_path(episode_url)
        if _pw_cookies_file:
            _pw_domain = _domain(episode_url)
            _pw_cookies_dict = _parse_netscape_cookies(_pw_cookies_file, _pw_domain)
            if _pw_cookies_dict:
                _pw_scheme = urlparse(episode_url).scheme
                _pw_cookie_list = [
                    {"name": k, "value": v, "domain": f".{_pw_domain}", "path": "/", "secure": _pw_scheme == "https"}
                    for k, v in _pw_cookies_dict.items()
                ]
                try:
                    await ctx.add_cookies(_pw_cookie_list)
                    logger.info("Playwright cookies yÃƒÂ¼klendi: %s (%d adet)", _pw_domain, len(_pw_cookie_list))
                except Exception as _ce:
                    logger.warning("Playwright cookie yÃƒÂ¼kleme hatasÃ„Â±: %s", _ce)

        page = await ctx.new_page()

        # Bot tespiti atla (playwright-stealth) Ã¢â‚¬â€ context'e uygula, navigation'dan ÃƒÂ¶nce
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
            logger.info("playwright-stealth aktif (context)")
        except Exception as _se:
            logger.warning("playwright-stealth bypass yok: %s", _se)

        # GET ve XHR/fetch isteklerini izle; direkt MP4 iÃƒÂ§in header'larÃ„Â± da yakala
        async def on_request(req):
            url = req.url
            if _is_embed(url) and url not in found_embed:
                found_embed.append(url)
                # yt-dlp'ye geÃƒÂ§irmek iÃƒÂ§in embed URL isteÃ„Å¸inin header'larÃ„Â±nÃ„Â± sakla
                # (CF cookie, Referer, Authorization vb. gerekebilir)
                try:
                    h = dict(req.headers)
                    h["_domain"] = _domain(url)
                    if not _sess_headers():
                        _sess_headers().update(h)
                        logger.info("Embed request header'larÃ„Â± yakalandÃ„Â±: %d adet", len(h) - 1)
                except Exception:
                    pass

        page.on("request", on_request)

        try:
            response = await page.goto(episode_url, timeout=timeout_ms, wait_until="domcontentloaded")
            http_status = response.status if response else 0
            if http_status != 200:
                logger.warning(
                    "PW: HTTP %d - %s (%s)",
                    http_status, episode_url[:60],
                    "PAGE NOT FOUND" if http_status == 404 else "BLOCKED/ERROR"
                )
            else:
                logger.info("PW: HTTP 200 OK - %s", episode_url[:60])

            # tranimaci.com: JS PoW challenge (SHA-256 difficulty=4) Ã¢â€ â€™ /__waf_challenge POST
            # Ã¢â€ â€™ 800ms sonra window.location.reload() Ã¢â€ â€™ gerÃƒÂ§ek sayfa yÃƒÂ¼kleniyor
            # Bu yÃƒÂ¼zden networkidle'Ã„Â± uzun bekliyoruz (PoW ~3sn + reload + player ~10sn)
            nidle_timeout = 25000 if "tranimaci.com" in domain else 8000
            try:
                await page.wait_for_load_state("networkidle", timeout=nidle_timeout)
            except Exception:
                pass  # timeout OK, devam

            # Site-spesifik popup kapat (player butonundan ÃƒÂ¶nce)
            _popup_selectors = []
            for _popup_key, _popup_sels in _POPUP_CLOSE_SELECTORS.items():
                if _popup_key in domain:
                    _popup_selectors = _popup_sels
                    break
            for selector in _popup_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        logger.info("Popup kapatÃ„Â±ldÃ„Â±: %s", selector)
                        await asyncio.sleep(0.5)
                        # Bootstrap modal fade-out animasyonu bitmeden backdrop kalabilir.
                        # JS ile #modallar + .modal-backdrop'Ã„Â± zorla kaldÃ„Â±r.
                        await page.evaluate("""
                            const m = document.querySelector('#modallar');
                            if (m) { m.classList.remove('in'); m.style.display = 'none'; }
                            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
                            document.body.classList.remove('modal-open');
                        """)
                        await asyncio.sleep(0.3)
                        break
                except Exception:
                    pass

            # Site-spesifik play/sunucu butonu varsa tÃ„Â±kla
            _play_selectors = []
            for _play_key, _play_sels in _PLAY_BUTTON_SELECTORS.items():
                if _play_key in domain:
                    _play_selectors = _play_sels
                    break
            for selector in _play_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        # force=True: backdrop kalmÃ„Â±Ã…Å¸sa bile tÃ„Â±klamayÃ„Â± zorunlu kÃ„Â±l
                        await btn.click(force=True)
                        logger.info("Play butonu tÃ„Â±klandÃ„Â±: %s", selector)
                        await asyncio.sleep(3)  # tÃ„Â±klama sonrasÃ„Â± iframe yÃƒÂ¼klensin
                        break
                except Exception:
                    pass

            # Player yÃƒÂ¼klensin
            if "turkanime.tv" in domain or "turkanime.com.tr" in domain:
                wait_secs = 32
            elif "tranimaci.com" in domain:
                wait_secs = 45  # JS PoW challenge (~5-15sn) + player load (~15sn) + embed fetch
            elif "hdfilmcehennemi" in domain:
                wait_secs = 20  # rplayer iframe lazy-load + CF geÃƒÂ§iÃ…Å¸i
            elif "dizigom" in domain:
                wait_secs = 15
            elif "tranimeizle" in domain:
                wait_secs = 15
            elif "setfilmizle" in domain:
                wait_secs = 20  # AJAX-loaded iframe + networkidle bekle
            elif any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT):
                wait_secs = 12
            else:
                wait_secs = 8
            await asyncio.sleep(wait_secs)

            # tranimaci.com ÃƒÂ¶zel: auth wall veya boÃ…Å¸ player kontrolÃƒÂ¼
            if "tranimaci.com" in domain:
                try:
                    await asyncio.sleep(3)  # navigasyon/rerender bitene kadar bekle
                    player_state = await page.evaluate("""() => {
                        const pd = document.querySelector('[data-player-embed]');
                        if (!pd) return 'NO_PLAYER';
                        const html = pd.innerHTML;
                        const hasAlert = html.includes('triangle-alert') || html.includes('lucide-alert');
                        const hasVideo = html.includes('iframe') || html.includes('video') || html.includes('m3u8');
                        const childCount = pd.children.length;
                        return {hasAlert, hasVideo, childCount};
                    }""")
                    if isinstance(player_state, dict):
                        if player_state.get("hasAlert"):
                            logger.warning("tranimaci.com: oynatÃ„Â±cÃ„Â± uyarÃ„Â± gÃƒÂ¶steriyor (triangle-alert) Ã¢â‚¬â€ oturum/kayÃ„Â±t gerekebilir")
                            await browser.close()
                            return None
                        if not player_state.get("hasVideo") and player_state.get("childCount", 0) <= 1:
                            logger.warning("tranimaci.com: oynatÃ„Â±cÃ„Â± boÃ…Å¸ (childCount=%s) Ã¢â‚¬â€ oturum veya embed sorunu", player_state.get("childCount"))
                            await browser.close()
                            return None
                except Exception as pw_exc:
                    logger.warning("tranimaci.com player durumu okunamadÃ„Â±: %s Ã¢â‚¬â€ normal akÃ„Â±Ã…Å¸a devam", pw_exc)

            html = await page.content()

            # JS ile tÃƒÂ¼m iframe/video src topla (lazy-set data-src dahil)
            try:
                js_srcs = await page.evaluate("""
                    () => {
                        const r = [];
                        document.querySelectorAll('iframe, frame').forEach(el => {
                            const s = el.src || el.getAttribute('data-src') || el.getAttribute('data-lazy-src');
                            if (s && s.startsWith('http')) r.push(s);
                        });
                        document.querySelectorAll('video, video source').forEach(el => {
                            const s = el.src || el.currentSrc || el.getAttribute('data-src');
                            if (s && s.startsWith('http')) r.push(s);
                        });
                        return [...new Set(r)];
                    }
                """)
                for s in js_srcs or []:
                    if s and s.startswith("http") and s not in found_embed:
                        if not any(skip in s for skip in _SKIP_IFRAME_DOMAINS):
                            found_embed.append(s)
                            logger.info("JS iframe/video bulundu: %s", s[:80])
            except Exception as js_exc:
                logger.warning("JS eval hatasÃ„Â±: %s", js_exc)

            # DOM'daki video/source/iframe elementlerinden URL topla
            for sel in ("video source", "video", "iframe"):
                els = await page.query_selector_all(sel)
                for el in els:
                    for attr in ("src", "data-src"):
                        src = await el.get_attribute(attr) or ""
                        if not src:
                            continue
                        # Protocol-relative URL (//) Ã¢â€ â€™ https: ekle
                        if src.startswith("//"):
                            src = "https:" + src
                        if not src.startswith("http"):
                            continue
                        if any(skip in src for skip in _SKIP_IFRAME_DOMAINS):
                            logger.info("LisanslÃ„Â± iframe atlandÃ„Â±: %s", src[:80])
                            continue
                        if src not in found_embed and (_is_embed(src) or sel == "iframe"):
                            found_embed.append(src)

            # turkanime.tv embed URL'leri hÃ„Â±zlÃ„Â±ca ÃƒÂ§ÃƒÂ¶zÃƒÂ¼lmeli (aynÃ„Â± PW session'da)
            # Aksi halde token/session expire olur ve embed -> 404.
            for embed_url in list(found_embed):
                if "turkanime.tv" in embed_url or "turkanime.com.tr" in embed_url:
                    logger.info("turkanime.tv embed aynÃ„Â± PW session'da ÃƒÂ§ÃƒÂ¶zÃƒÂ¼lÃƒÂ¼yor: %s", embed_url[:60])
                    try:
                        embed_page = await ctx.new_page()
                        embed_video_urls: list[str] = []
                        def _capture_video(req):
                            url = req.url.lower()
                            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest")):
                                if url not in embed_video_urls:
                                    embed_video_urls.append(req.url)
                                    logger.info("turkanime.tv PW video URL: %s", req.url[:80])
                        embed_page.on("request", _capture_video)
                        embed_resp = await embed_page.goto(embed_url, timeout=30000, wait_until="domcontentloaded")
                        if embed_resp and embed_resp.status == 404:
                            logger.warning("turkanime.tv embed 404 (expired): %s", embed_url[:60])
                        else:
                            await asyncio.sleep(12)
                            try:
                                await embed_page.wait_for_load_state("networkidle", timeout=10000)
                            except Exception:
                                pass
                            if embed_video_urls:
                                logger.info("turkanime.tv PW: %d video URL yakalandÃ„Â±", len(embed_video_urls))
                                found_embed = [embed_video_urls[-1]]  # sadece son video URL'yi kullan
                    except Exception as exc:
                        logger.warning("turkanime.tv PW embed ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m hatasÃ„Â±: %s", exc)
                    finally:
                        try:
                            await embed_page.close()
                        except Exception:
                            pass

            # Session cookie'lerini kaydet (yt-dlp --cookies iÃƒÂ§in)
            try:
                await _save_session_cookies(ctx, episode_url)
            except Exception:
                pass
        finally:
            await browser.close()

    if found_embed:
        logger.info("PW: %d embed bulundu Ã¢â‚¬â€ ilki dÃƒÂ¶ndÃƒÂ¼rÃƒÂ¼lÃƒÂ¼yor", len(found_embed))
        # fastplay.mom embed'leri: Playwright ile iÃƒÂ§ video URL'sini bul
        for u in found_embed:
            if "fastplay.mom" in u:
                resolved = await _resolve_embed_with_playwright(u, referer=episode_url)
                if resolved and resolved != u:
                    logger.info("Embed PW ile ÃƒÂ§ÃƒÂ¶zÃƒÂ¼ldÃƒÂ¼: %s -> %s", u[:60], resolved[:80])
                    return resolved
        # m3u8 varsa ÃƒÂ¶ncelik ver (ama embed ÃƒÂ§ÃƒÂ¶zÃƒÂ¼mÃƒÂ¼ baÃ…Å¸arÃ„Â±sÃ„Â±z olduysa)
        # En son yakalanan URL'yi tercih et (ad/preview'dan sonra asÃ„Â±l video)
        for u in reversed(found_embed):
            if ".m3u8" in u or "manifest.mpd" in u:
                return u
        # Direkt mp4 URL varsa tercih et (rotor/wrapper sayfasÃ„Â± yerine)
        for u in reversed(found_embed):
            if u.lower().split("?")[0].endswith(".mp4"):
                return u
        # YouTube/Social media embed'leri (yt-dlp native) Ã¢â‚¬â€ JS-render wrappers'tan ÃƒÂ¶nce
        for u in found_embed:
            if any(p in u for p in ("youtube.com/embed", "youtu.be", "youtube.com/watch", "vk.com/video", "ok.ru", "dailymotion")):
                return u
        # Ãƒâ€“lÃƒÂ¼/rotor domainlerini atla
        filtered = [u for u in found_embed if not any(d in u for d in _DEAD_EMBED_DOMAINS)]
        if filtered:
            return filtered[0]
        logger.warning("TÃƒÂ¼m embed URL'leri ÃƒÂ¶lÃƒÂ¼ domain (%s) Ã¢â‚¬â€ None dÃƒÂ¶ndÃƒÂ¼rÃƒÂ¼lÃƒÂ¼yor", _DEAD_EMBED_DOMAINS)
        return None

    if http_status and http_status != 200:
        logger.warning("PW: embed bulunamadÃ„Â± Ã¢â‚¬â€ sayfa HTTP %d (site kapalÃ„Â±/iÃƒÂ§erik silinmiÃ…Å¸)", http_status)
    else:
        logger.warning("PW: embed bulunamadÃ„Â± Ã¢â‚¬â€ sayfa HTTP %d fakat HTML'de player yok (len=%d)", http_status or 0, len(html))
    return _extract_embed_from_html(html)


_KEEP_PLAY_EMBED_DOMAINS = {
    "turkanime.tv", "turkanime.com.tr",
    "fastplay.mom",
    "anizmplayer.com",
}

async def _resolve_embed_with_playwright(embed_url: str, timeout_ms: int = 45000, *, referer: str | None = None) -> Optional[str]:
    """
    Playwright network interception ile embed URL'sinden gerÃƒÂ§ek video URL'sini bul.
    turkanime.tv / fastplay.mom gibi yt-dlp'nin desteklemediÃ„Å¸i embed'ler iÃƒÂ§in kullanÃ„Â±lÃ„Â±r.
    referer: embed URL'sine giderken kullanÃ„Â±lacak HTTP Referrer (bazÃ„Â± siteler zorunlu kÃ„Â±lar).
    """
    from playwright.async_api import async_playwright

    found_video: list[str] = []

    def _is_video_target(url: str) -> bool:
        lower = url.lower()
        if any(lower.endswith(ext) for ext in (".js", ".css", ".png", ".ico", ".svg", ".woff", ".woff2", ".json", ".xml")):
            return False
        if ".m3u8" in lower or "/hls/" in lower or ".mp4" in lower or ".mpd" in lower:
            return True
        if "/m3u/" in lower or ".ts" in lower:
            return True
        if "manifest" in lower:
            return True
        return False

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        extra_headers = {}
        if referer:
            extra_headers["Referer"] = referer
        ctx = await browser.new_context(
            extra_http_headers=extra_headers or None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
        except Exception:
            pass

        page = await ctx.new_page()

        async def on_request(req):
            url = req.url
            if _is_video_target(url) and url not in found_video:
                found_video.append(url)
                logger.info("Embed PW video URL yakalandÃ„Â±: %s", url[:80])

        page.on("request", on_request)

        try:
            resp = await page.goto(embed_url, timeout=timeout_ms, wait_until="domcontentloaded")
            if resp and resp.status != 200:
                logger.warning("Embed PW: HTTP %d - %s", resp.status, embed_url[:60])
                if resp.status == 404:
                    await browser.close()
                    return None

            await asyncio.sleep(5)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            # turkanime.tv: popup kapat + play butonu bul
            if "turkanime" in embed_url:
                popup_sels = ["button.site-popup-close", ".popup-close", "#popup-close", ".modal-close"]
                for sel in popup_sels:
                    try:
                        if await page.locator(sel).first.is_visible(timeout=1000):
                            await page.locator(sel).first.click()
                            await asyncio.sleep(0.5)
                    except Exception:
                        pass
                play_sels = [".play-button", "#play", "video", "button.play", ".video-js", ".jw-player"]
                for sel in play_sels:
                    try:
                        if await page.locator(sel).first.is_visible(timeout=3000):
                            # If it's a video element, get its src
                            tag = await page.locator(sel).first.evaluate("el => el.tagName")
                            if tag == "VIDEO":
                                src = await page.locator(sel).first.get_attribute("src") or ""
                                if src and src not in found_video:
                                    found_video.append(src)
                                break
                            await page.locator(sel).first.click(force=True)
                            await asyncio.sleep(2)
                            break
                    except Exception:
                        pass

            # fastplay.mom: bekle + play butonuna bas + video src'yi kontrol et
            if "fastplay.mom" in embed_url:
                for sel in ("#playbtn", ".play-button", "button.play", "video", ".vjs-big-play-button", "[aria-label='Play']", "#player-play"):
                    try:
                        el = page.locator(sel).first
                        if await el.is_visible(timeout=2000):
                            await el.click(force=True)
                            logger.info("fastplay.mom play butonuna basÃ„Â±ldÃ„Â±: %s", sel)
                            await asyncio.sleep(3)
                            break
                    except Exception:
                        pass
                await asyncio.sleep(10)

            # Ek bekleme + network isteklerini topla
            await asyncio.sleep(8)
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            # DOM'daki video/source elementlerinden URL topla
            try:
                for sel in ("video source", "video"):
                    els = await page.query_selector_all(sel)
                    for el in els:
                        src = await el.get_attribute("src") or ""
                        if not src:
                            src = await el.get_attribute("data-src") or ""
                        if src:
                            if src.startswith("//"):
                                src = "https:" + src
                            if src.startswith("http") and src not in found_video:
                                if _is_video_target(src) or any(k in src for k in (".m3u8", ".mp4")):
                                    found_video.append(src)
            except Exception:
                pass

        except Exception as e:
            logger.warning("Embed PW navigation hatasÃ„Â±: %s", e)
        finally:
            await browser.close()

    if found_video:
        logger.info("Embed PW: %d video URL yakalandÃ„Â± Ã¢â‚¬â€ sonuncu dÃƒÂ¶ndÃƒÂ¼rÃƒÂ¼lÃƒÂ¼yor", len(found_video))
        # En son yakalanan M3U8/MP4 dÃƒÂ¶ndÃƒÂ¼r (genelde ad/preview'dan sonraki asÃ„Â±l video)
        for u in reversed(found_video):
            if ".m3u8" in u or "/hls/" in u or "manifest.mpd" in u:
                return u
        for u in reversed(found_video):
            if u.lower().split("?")[0].endswith(".mp4"):
                return u
        return found_video[-1]
    return None


async def _save_session_cookies(ctx, media_url: str) -> None:
    """Playwright context cookie'lerini media domain iÃƒÂ§in _SESSION_COOKIES'e kaydet."""
    try:
        media_domain = _domain(media_url)
        cookies = await ctx.cookies()
        parts = [
            f"{c['name']}={c['value']}"
            for c in cookies
            if media_domain in c.get("domain", "").lstrip(".")
        ]
        if parts:
            _sess_cookies()[media_domain] = "; ".join(parts)
            logger.info("Session cookie kaydedildi: %s (%d adet)", media_domain, len(parts))
    except Exception as exc:
        logger.warning("Session cookie kayÃ„Â±t hatasÃ„Â±: %s", exc)


async def download_hls_via_playwright(
    episode_url: str,
    output_path: str,
    min_bytes: int = 10_000_000,
    timeout_sec: int = 90,
) -> str | None:
    """
    HLS video'yu Playwright browser ile indir.
    Segmentleri browser ÃƒÂ¼zerinden yakalar (CF/Cloudflare bypass), 
    birleÃ…Å¸tirir ve output_path'e yazar.
    fastplay.mom/setfilmizle.uk benzeri korumalÃ„Â± siteler iÃƒÂ§in.
    output_path: tam dosya yolu (ÃƒÂ¶rn: /path/to/ep001.mp4)
    """
    from playwright.async_api import async_playwright

    segment_data: dict[int, bytes] = {}
    total_bytes = 0
    segment_count = 0
    stop_event = asyncio.Event()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
            java_script_enabled=True,
        )
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
        except Exception:
            pass

        page = await ctx.new_page()

        async def on_response(response):
            nonlocal segment_count, total_bytes, segment_data
            url = response.url
            if "srv." in url and ".cfd" in url and url.endswith(".png") and response.status == 200:
                try:
                    body = await response.body()
                    if len(body) > 1000:
                        idx = len(segment_data)
                        segment_data[idx] = body
                        segment_count += 1
                        total_bytes += len(body)
                        logger.info("HLS PW segment %d: %s (%d bytes)", idx, url.split("/")[-1], len(body))
                        if total_bytes >= min_bytes:
                            stop_event.set()
                except Exception as e:
                    logger.debug("HLS PW segment error: %s", e)

        page.on("response", on_response)

        logger.info("HLS PW: navigating to %s", episode_url[:80])
        try:
            await page.goto(episode_url, timeout=30000, wait_until="domcontentloaded")
        except Exception as e:
            logger.warning("HLS PW goto error: %s", e)
            await browser.close()
            return None

        await asyncio.sleep(2)

        play_btn = await page.query_selector("#fimcnt_pb")
        if play_btn:
            await play_btn.click(delay=500)
            logger.info("HLS PW: clicked play button")
        else:
            for sel in (".play-button", "button.play", "img[alt*='play']"):
                el = await page.query_selector(sel)
                if el:
                    await el.click(delay=500)
                    logger.info("HLS PW: clicked %s", sel)
                    break

        await asyncio.sleep(3)

        stall_count = 0
        for i in range(timeout_sec // 3):
            if stop_event.is_set():
                break
            old_total = total_bytes
            await asyncio.sleep(3)
            if total_bytes == old_total:
                stall_count += 1
            else:
                stall_count = 0
            if stall_count > 10:
                logger.info("HLS PW: stalled for %ds", stall_count * 3)
                break
            logger.debug("HLS PW: %d segments, %.1fMB / %dMB", segment_count, total_bytes / 1e6, min_bytes / 1e6)

        await browser.close()

    if not segment_data:
        logger.warning("HLS PW: no segments captured")
        return None

    sorted_idx = sorted(segment_data.keys())
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        for idx in sorted_idx:
            f.write(segment_data[idx])

    actual_size = os.path.getsize(output_path)
    logger.info("HLS PW: saved %s (%d bytes, %d segments)", output_path, actual_size, len(segment_data))

    if actual_size < min_bytes:
        logger.warning("HLS PW: file too small (%d bytes < %d)", actual_size, min_bytes)
        return None

    return output_path


# Ã¢â€â‚¬Ã¢â€â‚¬ tranimaci.com ÃƒÂ¶zel ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬

_TRANIMACI_MIRRORS = [
    "tranimeizle.co",
    "tranimeizle.xyz",
    "tranimeizle.io",
    "turkanime.tv",
]

async def _resolve_tranimaci(episode_url: str) -> Optional[str]:
    """
    tranimaci.com iÃƒÂ§in ÃƒÂ¶zel ÃƒÂ§ÃƒÂ¶zÃƒÂ¼m.
    Playwright ile:
      1. PoW challenge'Ã„Â± bekle (45sn)
      2. Auth wall kontrolÃƒÂ¼ (giriÃ…Å¸ gerekiyor mu?)
      3. Video varsa embed URL'yi dÃƒÂ¶ndÃƒÂ¼r
      4. Video yoksa mirro dene
    """
    from playwright.async_api import async_playwright

    async def _try_page(ctx, url: str) -> Optional[str]:
        """Tek bir sayfayÃ„Â± dene, video embed bulursa dÃƒÂ¶ndÃƒÂ¼r."""
        page = await ctx.new_page()
        found: list[str] = []
        
        def _capture(req):
            u = req.url
            if any(k in u for k in (".m3u8", ".mp4", "manifest", ".mpd")):
                if u not in found:
                    found.append(u)
        page.on("request", _capture)
        
        try:
            resp = await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            if resp and resp.status != 200:
                logger.warning("tranimaci: HTTP %d - %s", resp.status, url[:60])
                return None
            
            nidle_timeout = 25000
            try:
                await page.wait_for_load_state("networkidle", timeout=nidle_timeout)
            except Exception:
                pass
            
            await asyncio.sleep(10)
            
            # Auth wall kontrolÃƒÂ¼
            player_state = await page.evaluate("""() => {
                const pd = document.querySelector('[data-player-embed]');
                if (!pd) return null;
                return {
                    hasAlert: pd.innerHTML.includes('triangle-alert') || pd.innerHTML.includes('lucide-alert'),
                    hasVideo: pd.innerHTML.includes('iframe') || pd.innerHTML.includes('video') || pd.innerHTML.includes('m3u8'),
                    childCount: pd.children.length
                };
            }""")
            if player_state and player_state.get("hasAlert"):
                logger.warning("tranimaci: auth wall tespit edildi (%s) Ã¢â‚¬â€ oturum gerekli", url[:60])
                return None
            
            if player_state and not player_state.get("hasVideo") and player_state.get("childCount", 0) <= 1:
                logger.warning("tranimaci: oynatÃ„Â±cÃ„Â± boÃ…Å¸ (%s) Ã¢â‚¬â€ video yÃƒÂ¼klenmedi", url[:60])
                return None
            
            # Video URL'lerini topla (network + DOM)
            await asyncio.sleep(8)
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass
            
            # DOM'dan embed/video URLs
            dom_urls = await page.evaluate("""() => {
                const urls = [];
                document.querySelectorAll('iframe, video, video source').forEach(el => {
                    const s = el.src || el.getAttribute('data-src') || el.getAttribute('data-lazy-src');
                    if (s && s.startsWith('http')) urls.push(s);
                });
                return urls;
            }""")
            
            all_urls = found + (dom_urls or [])
            if all_urls:
                logger.info("tranimaci: %d URL bulundu (%s)", len(all_urls), url[:60])
                return all_urls[0]
            
            return None
        except Exception as e:
            logger.warning("tranimaci: hata: %s", e)
            return None
        finally:
            await page.close()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        # S-166: her cikis yolunda kapan — zombi chrome.exe birikimi fix'i
        try:
            ctx = await browser.new_context(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"),
                locale="tr-TR",
                viewport={"width": 1920, "height": 1080},
            )
            try:
                from playwright_stealth import Stealth
                await Stealth().apply_stealth_async(ctx)
            except Exception:
                pass

            # Ãƒâ€“nce ana URL'yi dene
            result = await _try_page(ctx, episode_url)
            if result:
                return result

            # Mirro dene
            domain = _domain(episode_url)
            for mirror in _TRANIMACI_MIRRORS:
                mirror_url = episode_url.replace(domain, mirror)
                if mirror_url == episode_url:
                    mirror_url = episode_url.replace("tranimaci.com", mirror)
                logger.info("tranimaci mirror deneniyor: %s", mirror_url[:80])
                result = await _try_page(ctx, mirror_url)
                if result:
                    return result

            logger.warning("tranimaci: tÃƒÂ¼m kaynaklar denendi Ã¢â‚¬â€ hiÃƒÂ§biri video sunmuyor")
            return None
        finally:
            try:
                await browser.close()
            except Exception:
                pass
