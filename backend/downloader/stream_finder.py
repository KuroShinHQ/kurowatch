"""
stream_finder.py — Türk anime/dizi sitelerinden gerçek video URL'si çıkar.

Strateji:
  1. CF korumalı site → nodriver ile cf_clearance al (23 saat cache) → curl-cffi ile sayfa çek
  2. cookies.txt varsa → requests + CF bypass → iframe/embed URL çıkar
  3. JS-render gereken siteler → Playwright fallback
  4. Hiçbiri çalışmazsa → orijinal episode URL'yi döndür (yt-dlp denesin)

Desteklenen siteler:
  - dizibox.so/live   (nodriver CF bypass → curl-cffi)
   - hdfilmcehennemi.* (site parser → PW click + network interception)
   - dizigom.*         (site parser → PW click + network interception)
   - sezonlukdizi.*    (site parser → generic PW)
   - fullhdfilmizlesene.* (site parser → generic PW)
   - tranimeizle.co    (nodriver CF bypass → curl-cffi)
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

# Cookies dosyaları dizini
_COOKIES_DIR = Path(__file__).parent.parent.parent / "cookies"

# Playwright'ın MP4 URL'sine yaptığı isteğin header'ları (CF cookie dahil)
# anime.py yt-dlp çağrısında kullanır; her find_stream_url çağrısında sıfırlanır
_SESSION_HEADERS: dict[str, str] = {}

# CF bypass: nodriver ile alınan cookie cache'i
# domain → (cookies_dict, user_agent, timestamp)
_cf_cache: dict[str, tuple[dict, str, float]] = {}
_CF_CACHE_TTL = 23 * 3600  # 23 saat (CF cookie ömrü ~24 saat)

# Bu domainler nodriver cf_clearance + curl-cffi CF bypass gerektirir
# nodriver ilk seferde CF challenge'ı çözer, cookie 23 saat cache'lenir
# curl-cffi cookie ile direkt sayfayı çeker (hızlı, browsersız)
_CF_SITES = {
    "dizibox.live",
    "dizibox.so",
    "hdfilmcehennemi.nl", "hdfilmcehennemi.art", "hdfilmcehennemi.tv",
    "hdfilmcehennemi.com", "hdfilmcehennemi.name", "hdfilmcehennemi.gg",
    "hdfilmcehennemi.ws", "hdfilmcehennemi.now",
    "dizigom.info", "dizigom.com", "dizigom.vip", "dizigom.net",
    "dizigom.love", "dizigom.tv", "dizigom1.com",
    "tranimeizle.co",
    "tranimeizle.io",
    "tranimaci.com",
}

# nodriver Chromium binary yolu
_CHROMIUM_BIN = "/usr/bin/chromium-browser"


def get_session_header_args(actual_url: str) -> list[str]:
    """Playwright'ın MP4 isteğindeki header'ları yt-dlp --add-header listesi olarak döndür."""
    if not _SESSION_HEADERS:
        return []
    domain = _domain(actual_url)
    # Sadece bu URL domain'i için yakalanmışsa kullan
    if _SESSION_HEADERS.get("_domain") == domain:
        skip = {"_domain", "host", "content-length", "te", "accept-encoding", "range"}
        args: list[str] = []
        for k, v in _SESSION_HEADERS.items():
            if k.startswith("_") or k in skip:
                continue
            args += ["--add-header", f"{k}:{v}"]
        return args
    return []

# Embed player URL'lerini tanıyan kalıplar (yt-dlp destekleri)
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

# Site → cookies dosyası adı mapping
_SITE_COOKIES = {
    "tranimeizle.co":     "tranimeizle_cookies.txt",
    "tranimeizle.io":     "tranimeizle_cookies.txt",
    "turkanime.co":       "turkanime_cookies.txt",
    "turkanime.tv":       "turkanime_cookies.txt",
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

# Bu domainler iframe olarak bulunsa bile atlanır (lisanslı oynatıcılar, reklam ağları)
_SKIP_IFRAME_DOMAINS = (
    "crunchyroll.com", "vrv.co", "funimation.com",
    "google", "dtscout", "adservice", "doubleclick", "googlesyndication",
)

# Bu domainler JS-render gerektirir — requests fetch atla, direkt Playwright'a git
_FORCE_PLAYWRIGHT = {
    "dizibox.live",
    "dizibox.so",
    "hdfilmcehennemi.nl", "hdfilmcehennemi.art", "hdfilmcehennemi.tv",
    "hdfilmcehennemi.com", "hdfilmcehennemi.name", "hdfilmcehennemi.gg",
    "hdfilmcehennemi.ws", "hdfilmcehennemi.now",
    "dizigom.info", "dizigom.com", "dizigom.vip", "dizigom.net",
    "dizigom.love", "dizigom.tv", "dizigom1.com",
    "turkanime.tv",
}

# Bu domainler Cloudflare Managed Challenge kullanır → nodriver (gerçek Chrome) gerekiyor
# Playwright kolayca algılanıyor; nodriver CF'yi aşıp JS-render edilmiş HTML alıyor
_NODRIVER_HTML_SITES = {
}

# Site-spesifik popup kapatma selector'ları (play butonundan ÖNCE kapatılır)
_POPUP_CLOSE_SELECTORS = {
    "turkanime.tv": ["button.site-popup-close", ".popup-close", "#popup-close", ".modal-close"],
    "hdfilmcehennemi": [".modal-close", ".popup-close", "button.close", ".close-btn"],
    "dizigom": [".modal-close", ".popup-close", "button.close"],
}

# Site-spesifik play butonu CSS selector'ları (Playwright için)
_PLAY_BUTTON_SELECTORS = {
    "dizibox.live":       [".play-btn", "#play-btn", "[data-action='play']", "button.btn-play"],
    "dizibox.so":         [".play-btn", "#play-btn", "[data-action='play']", "button.btn-play"],
    "hdfilmcehennemi": [".play-that-video", "[aria-label='Play video']", ".play-button", "#play", ".jw-icon-playback"],
    "dizigom": [".player-area iframe", ".video-js", "#player iframe", ".film-player iframe"],
    # IndexIcerik AJAX → iframe inject eder; ilk sunucu butonunu tıkla
    "turkanime.tv":       ["button.btn.btn-sm.btn-default", ".btn-server:first-child", "[data-video]:first-child"],
    "tranimeizle.co":     [
        ".players a:first-child",
        ".eps-server:first-child a",
        ".serverList li:first-child a",
        "ul.servers li:first-child a",
        "#playerSezon .btn:first-child",
        ".player-options a:first-child",
        "[data-video]:first-child",
    ],
    # tranimaci.com: JS PoW challenge çözüldükten sonra player yüklenir
    "tranimaci.com": [
        ".source-btn:first-child",
        ".server-btn:first-child",
        ".btn-server:first-child",
        "ul.server-list li:first-child a",
        "[data-source]:first-child",
        ".player-source:first-child",
    ],
}


def _domain(url: str) -> str:
    """URL'den ana domain çıkar."""
    host = urlparse(url).netloc.lstrip("www.")
    return host


def _cookies_path(url: str) -> Optional[Path]:
    """Bu URL için cookies.txt dosyası var mı?"""
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
    """HTML içinden ilk embed/player URL'sini çıkar."""
    # iframe src ara
    iframes = re.findall(
        r'<iframe[^>]+src=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    for src in iframes:
        if any(skip in src for skip in _SKIP_IFRAME_DOMAINS):
            continue
        # Protocol-relative URL (//) → https: ekle
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
    """HTML/JS içinden direkt MP4 URL'si çıkar (CDN token'lı URL'ler dahil)."""
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
    """nodriver (undetected Chrome) ile CF Managed Challenge aşılır, JS-render HTML alınır."""
    import nodriver as uc
    browser = None
    try:
        logger.info("nodriver başlıyor: %s", url[:80])
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
            logger.warning("nodriver: CF challenge geçilemedi (%s)", title)
            return None
        return html
    except Exception as exc:
        logger.error("nodriver_get_html hatası: %s", exc)
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
}


async def _try_site_parser(domain: str, url: str) -> Optional[str]:
    """Site-specific parser dene (Playwright click + network interception)."""
    for site_key, site_name in _SITE_PARSER_DOMAINS.items():
        if site_key in domain:
            from backend.scraper.parsers import parse_url
            logger.info("Site parser deneniyor: %s → %s", site_name, url[:60])
            try:
                result = await parse_url(site_name, url)
                if result:
                    logger.info("Site parser video URL buldu: %s", result[:80])
                    return result
                logger.warning("Site parser embed bulamadi: %s", site_name)
            except Exception as e:
                logger.error("Site parser hatasi (%s): %s", site_name, e)
            break
    return None


async def find_stream_url(episode_url: str) -> str:
    """
    Episode sayfasından gerçek video/embed URL'si döndür.
    Sıra: site parser → nodriver HTML → CF bypass → cookies → Playwright → orijinal URL.
    """
    _SESSION_HEADERS.clear()
    domain = _domain(episode_url)

    # 0. Site-spesifik parser dene (hdfilmcehennemi, dizigom)
    try:
        parser_result = await _try_site_parser(domain, episode_url)
        if parser_result:
            return parser_result
    except Exception:
        pass

    # 1. Cloudflare Managed Challenge siteleri: nodriver ile JS-render HTML al
    if any(domain.endswith(d) for d in _NODRIVER_HTML_SITES):
        logger.info("nodriver HTML site: %s", domain)
        html = await _nodriver_get_html(episode_url, wait_secs=20)
        if html:
            embed = _extract_mp4_from_html(html) or _extract_embed_from_html(html)
            if embed:
                logger.info("nodriver HTML embed buldu: %s", embed[:80])
                return embed
            logger.warning("nodriver HTML alındı ama embed bulunamadı (len=%d)", len(html))
        else:
            logger.warning("nodriver HTML alınamadı, Playwright fallback deneniyor")

    # 1. CF korumalı site: nodriver cf_clearance + curl-cffi fetch
    if any(domain.endswith(d) for d in _CF_SITES):
        logger.info("CF site tespit edildi (%s) — nodriver bypass deneniyor", domain)
        try:
            html = await _fetch_with_cf_bypass(episode_url)
            if html:
                # tranimaci: direkt MP4 linki ara (player sayfası)
                url = _extract_mp4_from_html(html)
                if not url:
                    url = _extract_embed_from_html(html)
                if url:
                    logger.info("CF bypass URL buldu: %s", url[:80])
                    return url
                logger.warning("CF bypass HTML alındı ama URL bulunamadı (len=%d)", len(html))
        except Exception as exc:
            logger.error("CF bypass hatası: %s", exc)

    force_pw = any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT)

    # 2. Cookies.txt varsa dene
    if not force_pw:
        cookies_file = _cookies_path(episode_url)
        if cookies_file:
            logger.info("Cookies dosyası bulundu: %s", cookies_file)
            try:
                html = await _fetch_with_cookies(episode_url, cookies_file)
                if html:
                    embed = _extract_embed_from_html(html)
                    if embed:
                        return embed
                    logger.warning("HTML alındı ama embed bulunamadı (len=%d)", len(html))
            except Exception as exc:
                logger.error("stream_finder fetch hatası: %s", exc)
    else:
        logger.info("JS-render gerekli site (%s) — Playwright'a yönlendiriliyor", domain)

    # 3. Playwright: JS-render + ağ isteği izleme (fallback)
    if "turkanime.tv" in domain:
        pw_timeout = 60000
    elif "tranimaci.com" in domain:
        pw_timeout = 45000  # JS PoW challenge (~5sn) + player yüklenmesi (~20sn)
    else:
        pw_timeout = 15000
    try:
        embed = await _playwright_find_embed(episode_url, timeout_ms=pw_timeout)
        if embed:
            logger.info("Playwright embed buldu: %s", embed[:80])
            return embed
    except Exception as exc:
        logger.warning("Playwright fallback başarısız: %s", exc)

    logger.info("Embed bulunamadı, orijinal URL kullanılıyor: %s", episode_url[:60])
    return episode_url


async def _nodriver_get_cookies(domain: str, base_url: str) -> tuple[dict, str]:
    """
    nodriver ile siteye git, tüm cookie'leri + user_agent al. 23 saat cache'lenir.
    CF Turnstile olan siteler için cf_clearance dahil; olmayanlarda session cookie'leri alır.
    """
    cached = _cf_cache.get(domain)
    if cached:
        cookies_dict, ua, ts = cached
        if time.time() - ts < _CF_CACHE_TTL:
            logger.info("nodriver cookie cache'den kullanıldı: %s", domain)
            return cookies_dict, ua

    import nodriver as uc
    logger.info("nodriver başlıyor: %s (ilk seferinde ~10sn sürer)", domain)
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
            "nodriver tamamlandı: %s | %d cookie | cf_clearance=%s",
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
        logger.error("nodriver hatası: %s", exc)
    finally:
        browser.stop()
    return cookies_dict, user_agent


async def _fetch_with_cf_bypass(url: str) -> Optional[str]:
    """nodriver cookie'leri + curl-cffi ile CF korumalı sayfayı getir."""
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
                logger.warning("CF yeniden challenge (%s) — cache temizleniyor", domain)
                _cf_cache.pop(domain, None)
            else:
                logger.warning("curl-cffi %s → HTTP %d", url[:60], resp.status_code)
    except Exception as exc:
        logger.error("curl-cffi fetch hatası: %s", exc)
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
    logger.warning("Sayfa alınamadı: status=%s url=%s", resp.status_code, resp.url[:80])
    return None


def _parse_netscape_cookies(cookies_file: Path, domain: str) -> dict:
    """Netscape format cookies.txt → {name: value} dict (domain filtreli)."""
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
            cookie_domain_clean = cookie_domain.lstrip(".").lstrip("www.")
            if domain.endswith(cookie_domain_clean) or cookie_domain_clean.endswith(domain):
                cookies[name] = value
    except Exception as exc:
        logger.error("Cookie parse hatası: %s", exc)
    return cookies


def get_yt_dlp_cookies_arg(episode_url: str) -> list[str]:
    """yt-dlp için --cookies argümanı döndür (dosya varsa)."""
    p = _cookies_path(episode_url)
    if p:
        return ["--cookies", str(p)]
    return []


async def _playwright_find_embed(episode_url: str, timeout_ms: int = 15000) -> Optional[str]:
    """
    Playwright headless chromium ile sayfayı JS-render et, embed/video URL çıkar.
    JS-render gerektiren siteler (tranimaci.com, dizibox.live, hdfilmcehennemi.nl vb.) için.
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
    )

    def _is_embed(url: str) -> bool:
        # JS/CSS dosyaları ve analytics/tracking atla
        parsed_path = url.split("?")[0].split("#")[0].lower()
        if parsed_path.endswith((".js", ".css", ".woff", ".woff2", ".png", ".ico", ".svg")):
            return False
        if any(k in url for k in (".m3u8", "/hls/", "manifest.mpd", ".mp4")):
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

        # Cookies.txt varsa Playwright context'e yükle (turkanime.tv gibi force_playwright siteleri için)
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
                    logger.info("Playwright cookies yüklendi: %s (%d adet)", _pw_domain, len(_pw_cookie_list))
                except Exception as _ce:
                    logger.warning("Playwright cookie yükleme hatası: %s", _ce)

        page = await ctx.new_page()

        # Bot tespiti atla (playwright-stealth) — context'e uygula, navigation'dan önce
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
            logger.info("playwright-stealth aktif (context)")
        except Exception as _se:
            logger.warning("playwright-stealth bypass yok: %s", _se)

        # GET ve XHR/fetch isteklerini izle; direkt MP4 için header'ları da yakala
        async def on_request(req):
            url = req.url
            if _is_embed(url) and url not in found_embed:
                found_embed.append(url)
                # CF korumalı direkt MP4: yt-dlp'ye geçirmek için header'ları sakla
                if url.lower().split("?")[0].endswith(".mp4") and not _SESSION_HEADERS:
                    try:
                        h = dict(req.headers)
                        h["_domain"] = _domain(url)
                        _SESSION_HEADERS.update(h)
                        logger.info("MP4 request header'ları yakalandı: %d adet", len(h) - 1)
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

            # tranimaci.com: JS PoW challenge (SHA-256 difficulty=4) → /__waf_challenge POST
            # → 800ms sonra window.location.reload() → gerçek sayfa yükleniyor
            # Bu yüzden networkidle'ı uzun bekliyoruz (PoW ~3sn + reload + player ~10sn)
            nidle_timeout = 25000 if "tranimaci.com" in domain else 8000
            try:
                await page.wait_for_load_state("networkidle", timeout=nidle_timeout)
            except Exception:
                pass  # timeout OK, devam

            # Site-spesifik popup kapat (player butonundan önce)
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
                        logger.info("Popup kapatıldı: %s", selector)
                        await asyncio.sleep(0.5)
                        # Bootstrap modal fade-out animasyonu bitmeden backdrop kalabilir.
                        # JS ile #modallar + .modal-backdrop'ı zorla kaldır.
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

            # Site-spesifik play/sunucu butonu varsa tıkla
            _play_selectors = []
            for _play_key, _play_sels in _PLAY_BUTTON_SELECTORS.items():
                if _play_key in domain:
                    _play_selectors = _play_sels
                    break
            for selector in _play_selectors:
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        # force=True: backdrop kalmışsa bile tıklamayı zorunlu kıl
                        await btn.click(force=True)
                        logger.info("Play butonu tıklandı: %s", selector)
                        await asyncio.sleep(3)  # tıklama sonrası iframe yüklensin
                        break
                except Exception:
                    pass

            # Player yüklensin
            if "turkanime.tv" in domain:
                wait_secs = 32
            elif "tranimaci.com" in domain:
                wait_secs = 30  # JS PoW challenge (~5sn) + player load (~15sn) + embed fetch
            elif "hdfilmcehennemi" in domain:
                wait_secs = 20  # rplayer iframe lazy-load + CF geçişi
            elif "dizigom" in domain:
                wait_secs = 15
            elif "tranimeizle" in domain:
                wait_secs = 15
            elif any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT):
                wait_secs = 12
            else:
                wait_secs = 8
            await asyncio.sleep(wait_secs)

            html = await page.content()

            # JS ile tüm iframe/video src topla (lazy-set data-src dahil)
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
                logger.warning("JS eval hatası: %s", js_exc)

            # DOM'daki video/source/iframe elementlerinden URL topla
            for sel in ("video source", "video", "iframe"):
                els = await page.query_selector_all(sel)
                for el in els:
                    for attr in ("src", "data-src"):
                        src = await el.get_attribute(attr) or ""
                        if not src:
                            continue
                        # Protocol-relative URL (//) → https: ekle
                        if src.startswith("//"):
                            src = "https:" + src
                        if not src.startswith("http"):
                            continue
                        if any(skip in src for skip in _SKIP_IFRAME_DOMAINS):
                            logger.info("Lisanslı iframe atlandı: %s", src[:80])
                            continue
                        if src not in found_embed and (_is_embed(src) or sel == "iframe"):
                            found_embed.append(src)

        finally:
            await browser.close()

    if found_embed:
        logger.info("PW: %d embed bulundu — ilki döndürülüyor", len(found_embed))
        # m3u8 varsa öncelik ver
        for u in found_embed:
            if ".m3u8" in u or "manifest.mpd" in u:
                return u
        # Direkt mp4 URL varsa tercih et (rotor/wrapper sayfası yerine)
        for u in found_embed:
            if u.lower().split("?")[0].endswith(".mp4"):
                return u
        return found_embed[0]

    reason = f"HTTP {http_status}" if http_status else "no response"
    if http_status and http_status != 200:
        logger.warning("PW: embed bulunamadı — sayfa HTTP %d (site kapalı/içerik silinmiş)", http_status)
    else:
        logger.warning("PW: embed bulunamadı — sayfa HTTP %d fakat HTML'de player yok (len=%d)", http_status or 0, len(html))
    return _extract_embed_from_html(html)


async def _save_session_cookies(ctx, media_url: str) -> None:
    """Playwright context cookie'lerini media domain için _SESSION_COOKIES'e kaydet."""
    try:
        media_domain = _domain(media_url)
        cookies = await ctx.cookies()
        parts = [
            f"{c['name']}={c['value']}"
            for c in cookies
            if media_domain in c.get("domain", "").lstrip(".")
        ]
        if parts:
            _SESSION_COOKIES[media_domain] = "; ".join(parts)
            logger.info("Session cookie kaydedildi: %s (%d adet)", media_domain, len(parts))
    except Exception as exc:
        logger.warning("Session cookie kayıt hatası: %s", exc)
