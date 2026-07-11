"""
Site-specific parsers for movie/series sites.
Uses Playwright for JS interaction + network interception.
Supports persistent context for Cloudflare bypass via saved profiles.
"""
import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from backend.scraper.sources import get_active_url, get_source_config

logger = logging.getLogger(__name__)

_KNOWN_HOSTS = (
    "vidmoly", "streamtape", "filemoon", "doodstream", "voe.sx",
    "fembed", "upstream", "mixdrop", "gounlimited", "mp4upload",
    "sibnet", "ok.ru", "mail.ru", "vk.com/video", "spidypro",
    "rapidvid.net", "rapidvid",
)

_PROFILES_DIR = Path(__file__).parent / "pw_profiles"
_CF_COOKIE_FILE = Path(__file__).parent / "cf_cookies.json"


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


# ── CF Cookie Management ──────────────────────────────────────────────

def _load_cf_cookies() -> dict[str, list[dict]]:
    """Load saved CF cookies from disk. Returns {domain: [cookies]}."""
    if _CF_COOKIE_FILE.exists():
        try:
            return json.loads(_CF_COOKIE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_cf_cookies(cookies: list[dict], domain_key: str):
    """Save CF cookies for a domain. Extracts cf_clearance + __cf_bm."""
    cf_cookies = [c for c in cookies if c.get("name") in ("cf_clearance", "__cf_bm", "__cfruid")]
    if not cf_cookies:
        return
    data = _load_cf_cookies()
    data[domain_key] = cf_cookies
    _CF_COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CF_COOKIE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("CF cookies kaydedildi: %s (%d adet)", domain_key, len(cf_cookies))


def _detect_cf_challenge(page) -> bool:
    """Check if page is stuck on Cloudflare challenge."""
    import asyncio
    try:
        title = asyncio.run(asyncio.wait_for(page.title(), timeout=3))
        if title in ("Just a moment...", "...", "Attention Required! | Cloudflare"):
            return True
        # CF challenge iframe kontrolü
        body_text = asyncio.run(asyncio.wait_for(page.evaluate("document.body?.innerText?.substring(0,200) || ''"), timeout=3))
        if "Checking your browser" in body_text or "DDoS protection" in body_text:
            return True
    except Exception:
        pass
    return False


async def _ensure_browser_context(headless: bool = True, site_name: str = "", extra_args: list[str] | None = None):
    """Create a Playwright context. Uses persistent profile for CF sites."""
    from playwright.async_api import async_playwright

    extra_args = extra_args or []
    base_args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"] + extra_args
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    pw = await async_playwright().__aenter__()
    profile_dir = _PROFILES_DIR / site_name if site_name else None

    if profile_dir and profile_dir.exists():
        # Persistent context with saved profile
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=headless,
            args=base_args,
            user_agent=ua,
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )
        # Inject saved CF cookies
        cf_data = _load_cf_cookies()
        if site_name in cf_data:
            try:
                await ctx.add_cookies(cf_data[site_name])
                logger.info("CF cookies yuklendi: %s", site_name)
            except Exception as e:
                logger.debug("CF cookie yukleme hatasi: %s", e)
    else:
        # Fresh context
        if profile_dir:
            profile_dir.mkdir(parents=True, exist_ok=True)
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir or (_PROFILES_DIR / "_default")),
            headless=headless,
            args=base_args,
            user_agent=ua,
            locale="tr-TR",
            viewport={"width": 1920, "height": 1080},
        )

    # Apply stealth
    try:
        from playwright_stealth import Stealth
        await Stealth().apply_stealth_async(ctx)
    except Exception:
        pass

    return pw, ctx


async def _pw_click_and_capture(
    url: str,
    click_selectors: list[str],
    known_hosts: tuple[str, ...] = _KNOWN_HOSTS,
    wait_before_click: float = 3.0,
    wait_after_click: float = 5.0,
    network_idle_timeout: int = 15000,
    site_name: str = "",
    cf_retry_headless: bool = True,
    popup_selectors: list[str] | None = None,
) -> tuple[Optional[str], Optional[str]]:
    """Playwright ile sayfaya git, butonlara tıkla, network'ten embed yakala.
    
    CF korumali siteler icin persistent profile + cookie cache + headless fallback.
    Donus: (yakalanan_embed_url, son_html_icerigi)
    """
    found: list[str] = []
    captured_html: Optional[str] = None

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

    async def _try_capture(headless: bool) -> tuple[bool, Optional[str]]:
        nonlocal found
        from playwright.async_api import async_playwright

        pw = await async_playwright().__aenter__()
        profile_dir = _PROFILES_DIR / site_name if site_name else None
        base_args = ["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/131.0.0.0 Safari/537.36")

        try:
            if profile_dir and profile_dir.exists():
                ctx = await pw.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir), headless=headless, args=base_args,
                    user_agent=ua, locale="tr-TR", viewport={"width": 1920, "height": 1080},
                )
                cf_data = _load_cf_cookies()
                if site_name in cf_data:
                    try:
                        await ctx.add_cookies(cf_data[site_name])
                    except Exception:
                        pass
            else:
                if profile_dir:
                    profile_dir.mkdir(parents=True, exist_ok=True)
                ctx = await pw.chromium.launch_persistent_context(
                    user_data_dir=str(profile_dir or (_PROFILES_DIR / "_default")),
                    headless=headless, args=base_args,
                    user_agent=ua, locale="tr-TR", viewport={"width": 1920, "height": 1080},
                )

            try:
                from playwright_stealth import Stealth
                await Stealth().apply_stealth_async(ctx)
            except Exception:
                pass

            page = await ctx.new_page()
            _local_found: list[str] = []
            page.on("request", lambda req: _local_found.append(req.url)
                    if _is_target(req.url) and req.url not in _local_found else None)

            try:
                resp = await page.goto(url, timeout=45000, wait_until="commit")
                status = resp.status if resp else 0
                # Try to reach domcontentloaded (may timeout on CF challenge)
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=20000)
                except Exception:
                    pass
            except Exception as e:
                logger.error("PW goto (%s, hl=%s): %s", site_name, headless, e)
                await pw.stop()
                return False, (None, None)

            # CF challenge detection
            try:
                title = await page.title()
                if title in ("Just a moment...", "...", "Attention Required! | Cloudflare"):
                    logger.warning("CF challenge: %s (hl=%s)", site_name, headless)
                    await pw.stop()
                    return True, (None, None)
            except Exception:
                pass

            if status == 404:
                logger.warning("PW 404: %s", url[:60])
                await pw.stop()
                return False, (None, None)

            logger.info("PW %d: %s (hl=%s)", status, url[:60], headless)
            await asyncio.sleep(wait_before_click)

            # Popups
            for sel in (popup_selectors or [".modal-close", ".popup-close", ".site-popup-close", "button.close"]):
                try:
                    if await page.locator(sel).first.is_visible(timeout=1000):
                        await page.locator(sel).first.click()
                        await asyncio.sleep(0.5)
                except Exception:
                    pass

            # Click
            for sel in click_selectors:
                try:
                    if await page.locator(sel).first.is_visible(timeout=2000):
                        await page.locator(sel).first.click(force=True)
                        await asyncio.sleep(0.5)
                except Exception:
                    pass

            await asyncio.sleep(wait_after_click)
            try:
                await page.wait_for_load_state("networkidle", timeout=network_idle_timeout)
            except Exception:
                pass

            # Save CF cookies on success
            if site_name and _local_found:
                try:
                    await _save_cf_cookies(await ctx.cookies(), site_name)
                except Exception:
                    pass

            # Fallback: iframe src extraction from HTML (for sites with static iframes)
            if not _local_found:
                try:
                    captured_html = await page.content()
                    iframe_srcs = re.findall(r'<iframe[^>]+src="([^"]+)"', captured_html)
                    for src in iframe_srcs:
                        if _is_target(src):
                            _local_found.append(src)
                except Exception:
                    pass

            if captured_html is None:
                try:
                    captured_html = await page.content()
                except Exception:
                    pass

            await pw.stop()
            found = _local_found
            return False, (found[0] if found else None, captured_html)

        except Exception as e:
            logger.error("PW kritik (%s): %s", site_name, e)
            try:
                await pw.stop()
            except Exception:
                pass
            return False, (None, None)

    # Strategy 1: headless=True
    is_cf, result = await _try_capture(headless=True)
    embed_url, page_html = result if result else (None, None)
    if embed_url:
        return embed_url, page_html

    # Strategy 2: CF detected → headless=False
    if is_cf and cf_retry_headless and site_name:
        logger.info("CF -> headless=False: %s", site_name)
        _, result2 = await _try_capture(headless=False)
        embed_url2, page_html2 = result2 if result2 else (None, None)
        if embed_url2:
            return embed_url2, page_html2
        logger.warning("CF bypass basarisiz: %s", site_name)

    return None, None


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

    embed, _ = await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".play-that-video", ".play-button", "#play", ".jw-icon-playback",
        ]),
        wait_before_click=4.0,
        wait_after_click=8.0,
        network_idle_timeout=20000,
        site_name="hdfilmcehennemi",
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

    embed, _ = await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".player-area iframe", ".video-js", "#player iframe", ".film-player iframe",
            ".tab-link:first-child", ".server-btn:first-child", ".source-btn:first-child",
        ]),
        wait_before_click=3.0,
        wait_after_click=6.0,
        network_idle_timeout=15000,
        site_name="dizigom",
    )

    if embed:
        return await resolve_embed_with_ytdlp(embed)
    return None


async def parse_url(site_name: str, url: str) -> Optional[str]:
    """Auto-detect parser by site name and extract video URL."""
    slug = urlparse(url).path.lstrip("/")
    
    if site_name == "hdfilmcehennemi":
        return await parse_hdfilmcehennemi(slug)
    elif site_name == "dizigom":
        return await parse_dizigom(slug)
    elif site_name in ("sezonlukdizi", "fullhdfilmizlesene", "setfilmizle"):
        return await parse_generic(site_name, url)
    else:
        logger.warning("Bilinmeyen site parser: %s", site_name)
        return None


async def parse_url_with_tags(site_name: str, url: str) -> dict:
    """Auto-detect parser and extract both video URL + local site tags."""
    from backend.scraper.tag_extractor import extract_site_tags

    slug = urlparse(url).path.lstrip("/")
    page_html: Optional[str] = None
    embed: Optional[str] = None

    if site_name == "hdfilmcehennemi":
        embed, page_html = await _parse_hdfilmcehennemi_raw(slug)
    elif site_name == "dizigom":
        embed, page_html = await _parse_dizigom_raw(slug)
    elif site_name in ("sezonlukdizi", "fullhdfilmizlesene", "setfilmizle"):
        embed, page_html = await _parse_generic_raw(site_name, url)
    else:
        logger.warning("Bilinmeyen site parser (tags): %s", site_name)

    tags: list[str] = []
    if page_html:
        tags = extract_site_tags(site_name, page_html, url)

    result = {"stream_url": None, "tags": tags}
    if embed:
        result["stream_url"] = await resolve_embed_with_ytdlp(embed)
    return result


async def _parse_hdfilmcehennemi_raw(slug: str) -> tuple[Optional[str], Optional[str]]:
    """hdfilmcehennemi için (embed, html) tuple döndür."""
    config = get_source_config("hdfilmcehennemi")
    if not config:
        return None, None
    domain = await _resolve_domain("hdfilmcehennemi")
    if not domain:
        return None, None
    url = f"https://{domain}/{slug}"
    return await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".play-that-video", ".play-button", "#play", ".jw-icon-playback",
        ]),
        wait_before_click=4.0,
        wait_after_click=8.0,
        network_idle_timeout=20000,
        site_name="hdfilmcehennemi",
    )


async def _parse_dizigom_raw(slug: str) -> tuple[Optional[str], Optional[str]]:
    """dizigom için (embed, html) tuple döndür."""
    config = get_source_config("dizigom")
    if not config:
        return None, None
    domain = await _resolve_domain("dizigom")
    if not domain:
        return None, None
    url = f"https://{domain}/{slug}"
    return await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".player-area iframe", ".video-js", "#player iframe", ".film-player iframe",
            ".tab-link:first-child", ".server-btn:first-child", ".source-btn:first-child",
        ]),
        wait_before_click=3.0,
        wait_after_click=6.0,
        network_idle_timeout=15000,
        site_name="dizigom",
    )


async def _parse_generic_raw(site_name: str, url: str) -> tuple[Optional[str], Optional[str]]:
    """Generic site için (embed, html) tuple döndür."""
    config = get_source_config(site_name)
    if not config:
        return None, None
    domain = await _resolve_domain(site_name)
    if not domain:
        return None, None
    return await _pw_click_and_capture(
        url=url,
        click_selectors=config.get("play_selectors", [
            ".player-area iframe", "#player iframe", ".video-js",
            "iframe[src*='embed']", ".play-button",
        ]),
        wait_before_click=3.0,
        wait_after_click=6.0,
        network_idle_timeout=15000,
        site_name=site_name,
    )


async def parse_generic(site_name: str, url: str) -> Optional[str]:
    """Generic parser using _pw_click_and_capture with site config."""
    embed, _ = await _parse_generic_raw(site_name, url)
    if embed:
        return await resolve_embed_with_ytdlp(embed)
    return None


async def _resolve_domain(site_name: str) -> Optional[str]:
    """Get active domain for a site."""
    from backend.scraper.sources import get_active_domain
    domain = await get_active_domain(site_name)
    if not domain:
        logger.error("Aktif domain bulunamadi: %s", site_name)
        return None
    return domain
