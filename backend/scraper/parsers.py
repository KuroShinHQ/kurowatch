"""
Site-specific parsers for movie/series sites.
Uses Playwright for JS interaction + network interception.
"""
import asyncio
import logging
import re
from typing import Optional
from urllib.parse import urlparse

from backend.scraper.sources import get_active_url, get_source_config

logger = logging.getLogger(__name__)

_KNOWN_HOSTS = (
    "vidmoly", "streamtape", "filemoon", "doodstream", "voe.sx",
    "fembed", "upstream", "mixdrop", "gounlimited", "mp4upload",
    "sibnet", "ok.ru", "mail.ru", "vk.com/video", "spidypro",
)


async def resolve_embed_with_ytdlp(embed_url: str) -> Optional[str]:
    """yt-dlp --get-url ile embed host'tan direkt video URL'si çıkar."""
    import subprocess
    logger.info("yt-dlp ile embed çözülüyor: %s", embed_url[:80])
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--get-url",
            "--no-warnings",
            embed_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            logger.warning("yt-dlp timeout (30sn)")
            return embed_url
        out = stdout.decode("utf-8", errors="replace").strip()
        if out and out.startswith("http"):
            logger.info("yt-dlp çözüm: %s", out[:80])
            return out.split("\n")[0]
        err = stderr.decode("utf-8", errors="replace")[:200]
        logger.warning("yt-dlp başarısız: %s", err)
    except FileNotFoundError:
        logger.warning("yt-dlp kurulu değil, embed URL olduğu gibi döndürülüyor")
    except Exception as e:
        logger.error("yt-dlp hatası: %s", e)
    return embed_url


async def _pw_click_and_capture(
    url: str,
    click_selectors: list[str],
    known_hosts: tuple[str, ...] = _KNOWN_HOSTS,
    wait_before_click: float = 3.0,
    wait_after_click: float = 5.0,
    network_idle_timeout: int = 15000,
) -> Optional[str]:
    """Playwright ile sayfaya git, butonlara tıkla, network'ten embed yakala."""
    from playwright.async_api import async_playwright

    found: list[str] = []

    def _is_target(url: str) -> bool:
        if url.endswith((".js", ".css", ".png", ".ico", ".svg", ".woff", ".woff2")):
            return False
        if any(h in url for h in known_hosts):
            return True
        if re.search(r"\.m3u8?|/hls/|\.mp4\?", url, re.IGNORECASE):
            return True
        if "/m3u/" in url:
            return True
        if "/embed/" in url or "/iframe.php" in url or "/player/" in url:
            return True
        return False

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
        )
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
        except Exception:
            pass

        page = await ctx.new_page()
        page.on("request", lambda req: found.append(req.url) if _is_target(req.url) and req.url not in found else None)

        try:
            resp = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            status = resp.status if resp else 0
            if status == 404:
                logger.warning("PW 404: %s", url[:60])
                return None
            logger.info("PW %d: %s", status, url[:60])
        except Exception as e:
            logger.error("PW goto hatasi: %s", e)
            return None

        await asyncio.sleep(wait_before_click)

        # Popup kapat
        for popup_sel in [".modal-close", ".popup-close", ".site-popup-close", "button.close"]:
            try:
                btn = page.locator(popup_sel).first
                if await btn.is_visible(timeout=1000):
                    await btn.click()
                    await asyncio.sleep(0.5)
                    logger.info("Popup kapandi: %s", popup_sel)
            except Exception:
                pass

        # Click selectors
        for sel in click_selectors:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=2000):
                    await el.click(force=True)
                    logger.info("Tiklandi: %s", sel)
                    await asyncio.sleep(0.5)
            except Exception:
                pass

        await asyncio.sleep(wait_after_click)

        try:
            await page.wait_for_load_state("networkidle", timeout=network_idle_timeout)
        except Exception:
            pass

        await browser.close()

    if found:
        logger.info("Yakalanan URL'ler: %s", [u[:60] for u in found])
        return found[0]
    return None


async def parse_hdfilmcehennemi(slug: str, media_type: str = "movie") -> Optional[str]:
    """hdfilmcehennemi film/dizi sayfasindan embed URL yakala."""
    config = get_source_config("hdfilmcehennemi")
    if not config:
        logger.warning("hdfilmcehennemi kaynak config bulunamadi")
        return None

    domain = await _resolve_domain("hdfilmcehennemi")
    if not domain:
        return None

    url = f"https://{domain}/{slug}"
    logger.info("hdfilmcehennemi parser: %s", url)

    embed = await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".play-that-video", ".play-button", "#play", ".jw-icon-playback",
        ]),
        wait_before_click=4.0,
        wait_after_click=8.0,
        network_idle_timeout=20000,
    )

    if embed:
        return await resolve_embed_with_ytdlp(embed)
    return None


async def parse_dizigom(slug: str, media_type: str = "episode") -> Optional[str]:
    """dizigom dizi bolumu sayfasindan embed URL yakala."""
    config = get_source_config("dizigom")
    if not config:
        logger.warning("dizigom kaynak config bulunamadi")
        return None

    domain = await _resolve_domain("dizigom")
    if not domain:
        return None

    url = f"https://{domain}/{slug}"
    logger.info("dizigom parser: %s", url)

    embed = await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".player-area iframe", ".video-js", "#player iframe", ".film-player iframe",
            ".tab-link:first-child", ".server-btn:first-child", ".source-btn:first-child",
        ]),
        wait_before_click=3.0,
        wait_after_click=6.0,
        network_idle_timeout=15000,
    )

    if embed:
        return await resolve_embed_with_ytdlp(embed)
    return None


async def parse_url(site_name: str, url: str) -> Optional[str]:
    """Auto-detect parser by site name and extract video URL."""
    if site_name == "hdfilmcehennemi":
        path = urlparse(url).path.lstrip("/")
        return await parse_hdfilmcehennemi(path)
    elif site_name == "dizigom":
        path = urlparse(url).path.lstrip("/")
        return await parse_dizigom(path)
    else:
        logger.warning("Bilinmeyen site parser: %s", site_name)
        return None


async def _resolve_domain(site_name: str) -> Optional[str]:
    """Get active domain for a site."""
    from backend.scraper.sources import get_active_domain
    domain = await get_active_domain(site_name)
    if not domain:
        logger.error("Aktif domain bulunamadi: %s", site_name)
        return None
    return domain
