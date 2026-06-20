"""
stream_finder.py — Türk anime/dizi sitelerinden gerçek video URL'si çıkar.

Strateji:
  1. cookies.txt varsa → requests + CF bypass → iframe/embed URL çıkar
  2. iframe URL yt-dlp'nin desteklediği bir player ise (Filemoon, Vidmoly vb.) → direkt kullan
  3. Hiçbiri çalışmazsa → orijinal episode URL'yi döndür (yt-dlp denesin)

Desteklenen siteler:
  - tranimeizle.co (cookies.txt gerekli)
  - diziwatch.com
  - turkanime.co
  - dizibox.live     (Playwright — JS-render + CF korumalı)
  - hdfilmcehennemi.nl (Playwright — JS-render)
"""
import os
import re
import asyncio
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Cookies dosyaları dizini
_COOKIES_DIR = Path(__file__).parent.parent.parent / "cookies"

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
    "diziwatch.com":      "diziwatch_cookies.txt",
    "anizm.net":          "anizm_cookies.txt",
    "dizibox.live":       "dizibox_cookies.txt",
    "hdfilmcehennemi.nl": "hdfilmcehennemi_cookies.txt",
}

# Bu domainler JS-render gerektirir — requests fetch atla, direkt Playwright'a git
_FORCE_PLAYWRIGHT = {
    "dizibox.live",
    "hdfilmcehennemi.nl",
}

# Site-spesifik play butonu CSS selector'ları (Playwright için)
_PLAY_BUTTON_SELECTORS = {
    "dizibox.live":       [".play-btn", "#play-btn", "[data-action='play']", "button.btn-play"],
    "hdfilmcehennemi.nl": [".play-button", "#play", ".jw-icon-playback", "[aria-label='play']"],
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
        if any(skip in src for skip in ("google", "dtscout", "adservice", "doubleclick")):
            continue
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


async def find_stream_url(episode_url: str) -> str:
    """
    Episode sayfasından gerçek video/embed URL'si döndür.
    Sıra: cookies fetch → Playwright JS-render → orijinal URL.

    JS-render gerektiren siteler (dizibox.live, hdfilmcehennemi.nl) için
    requests fetch atlanır, direkt Playwright kullanılır.
    """
    domain = _domain(episode_url)
    force_pw = any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT)

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

    # Playwright: JS-render + ağ isteği izleme
    try:
        embed = await _playwright_find_embed(episode_url)
        if embed:
            logger.info("Playwright embed buldu: %s", embed[:80])
            return embed
    except Exception as exc:
        logger.warning("Playwright fallback başarısız: %s", exc)

    logger.info("Embed bulunamadı, orijinal URL kullanılıyor: %s", episode_url[:60])
    return episode_url


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

    _KNOWN_PLAYERS = (
        "filemoon", "vidmoly", "doodstream", "streamtape", "voe.sx",
        "speedfiles", "sibnet", "ok.ru", "fembed", "upstream",
        "rapidvid", "mixdrop", "gounlimited", "mp4upload",
        "odnoklassniki", "mail.ru", "vk.com/video",
        "dizibox.live/embed", "hdfilmcehennemi.nl/embed",
    )

    def _is_embed(url: str) -> bool:
        if any(k in url for k in (".m3u8", "/hls/", "manifest.mpd", ".mp4")):
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
        page = await ctx.new_page()

        # GET ve XHR/fetch isteklerini izle
        async def on_request(req):
            url = req.url
            if _is_embed(url) and url not in found_embed:
                found_embed.append(url)

        page.on("request", on_request)

        try:
            await page.goto(episode_url, timeout=timeout_ms, wait_until="domcontentloaded")

            # Site-spesifik play butonu varsa tıkla
            for selector in _PLAY_BUTTON_SELECTORS.get(domain, []):
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=2000):
                        await btn.click()
                        logger.info("Play butonu tıklandı: %s", selector)
                        break
                except Exception:
                    pass

            # Player yüklensin — CF siteler için daha uzun bekle
            wait_secs = 12 if any(domain.endswith(d) for d in _FORCE_PLAYWRIGHT) else 8
            await asyncio.sleep(wait_secs)

            html = await page.content()

            # DOM'daki video/source/iframe elementlerinden URL topla
            for sel in ("video source", "video", "iframe"):
                els = await page.query_selector_all(sel)
                for el in els:
                    for attr in ("src", "data-src"):
                        src = await el.get_attribute(attr) or ""
                        if src and src.startswith("http") and src not in found_embed:
                            if _is_embed(src) or sel == "iframe":
                                found_embed.append(src)

        finally:
            await browser.close()

    if found_embed:
        # m3u8 varsa öncelik ver
        for u in found_embed:
            if ".m3u8" in u or "manifest.mpd" in u:
                return u
        return found_embed[0]

    return _extract_embed_from_html(html)
