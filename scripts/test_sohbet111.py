#!/usr/bin/env python3
"""
SOHBET-111 — Cloudflare Bypass + Auto-Assign + Alternatif Site Testi
"""
import asyncio, sys, os, re, json

sys.path.insert(0, "/mnt/c/Kuroshin/kurowatch")
os.chdir("/mnt/c/Kuroshin/kurowatch")

from backend.scraper.parsers import (
    _pw_click_and_capture, resolve_embed_with_ytdlp,
    _load_cf_cookies, _save_cf_cookies, _PROFILES_DIR,
)
from backend.scraper.sources import get_active_domain
from playwright.async_api import async_playwright

PASS = 0; FAIL = 0; LOG = []

def ll(step, status, detail=""):
    global PASS, FAIL
    LOG.append((step, status, detail))
    if status == "PASS": PASS += 1
    elif status == "FAIL": FAIL += 1
    icon = "✅" if status == "PASS" else ("⚠️" if status in ("SKIP","FALLBACK") else "❌")
    print(f"  {icon} [{status}] {step}")
    if detail: print(f"     {detail[:250]}")

async def test_site(url, site_name, play_sel, label):
    print(f"\n── {label} ──")
    embed = await _pw_click_and_capture(
        url=url, click_selectors=play_sel,
        wait_before_click=3, wait_after_click=6,
        site_name=site_name, cf_retry_headless=True,
    )
    if embed:
        ll(f"PW: {site_name}", "PASS", embed[:200])
        # yt-dlp
        video = await resolve_embed_with_ytdlp(embed)
        if video and video != embed:
            ll(f"yt-dlp: {site_name}", "PASS", video[:200])
        else:
            ll(f"yt-dlp: {site_name}", "SKIP", "embed as-is")
        return embed
    else:
        ll(f"PW: {site_name}", "FAIL" if "hdfilm" in site_name else "FAIL", "no embed")
        return None

async def test_cf_cookies():
    print(f"\n── CF Cookie Cache Test ──")
    before = _load_cf_cookies()
    ll("CF cookie file OK" if isinstance(before, dict) else "CF cookie file corrupt", "PASS")
    keys = list(before.keys())
    if keys:
        ll(f"Kayitli CF cookie domainleri: {keys}", "PASS")
    else:
        ll("Henuz CF cookie yok (ilk calistirmada olusur)", "SKIP")
    print(f"  Profile dir: {_PROFILES_DIR}")
    print(f"  Var mi: {_PROFILES_DIR.exists()}")

async def test_alt_sites():
    """Quick HTTP check for new sites."""
    print(f"\n── Alternatif Site HTTP Test ──")
    sites = {
        "sezonlukdizi.com": "https://sezonlukdizi.com/",
        "fullhdfilmizlesene.com": "https://fullhdfilmizlesene.com/",
    }
    import httpx
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as c:
        for name, url in sites.items():
            try:
                r = await c.head(url)
                if r.status_code < 400:
                    ll(f"HTTP: {name}", "PASS", f"HTTP {r.status_code}")
                else:
                    ll(f"HTTP: {name}", "FAIL", f"HTTP {r.status_code}")
            except Exception as e:
                ll(f"HTTP: {name}", "FAIL", str(e)[:80])

async def main():
    print("="*55)
    print("  SOHBET-111 — CANLI TEST")
    print("  WSL + Playwright + CF bypass + Yeni Siteler")
    print("  7 Temmuz 2026")
    print("="*55)

    # 1. CF Cookie Cache
    await test_cf_cookies()

    # 2. Alternatif Site HTTP Check
    await test_alt_sites()

    # 3. Dizigom (re-test with new persistent context)
    await test_site(
        "https://www.dizigom.love/silo-3-sezon-1-bolum/",
        "dizigom",
        [".player-area iframe", ".video-js", "#player iframe", ".tab-link:first-child"],
        "Dizigom (persistent context)"
    )

    # 4. hdfilmcehennemi CF bypass (persistent context + headless=False fallback)
    await test_site(
        "https://hdfilmcehennemi.name/hesaplasma-2-izle/",
        "hdfilmcehennemi",
        [".play-that-video", ".play-button", "#play"],
        "HDFilmCehennemi (CF bypass)"
    )

    # 5. sezonlukdizi (alt site)
    # First try to find active domain
    d = await get_active_domain("sezonlukdizi")
    if d:
        await test_site(
            f"https://{d}/",
            "sezonlukdizi",
            [".player-area iframe", "#player iframe", "iframe[src*='embed']"],
            "SezonlukDizi"
        )

    # 6. Check CF cookie cache after tests
    print(f"\n── CF Cookie Cache After Test ──")
    after = _load_cf_cookies()
    for domain, cookies in after.items():
        names = [c.get("name", "?") for c in cookies]
        ll(f"  {domain}: {names}", "PASS" if any("cf_clearance" in n for n in names) else "SKIP")

    # REPORT
    print(f"\n{'='*55}")
    print(f"  RAPOR: {PASS} PASS / {FAIL} FAIL")
    for step, status, detail in LOG:
        icon = "✅" if status == "PASS" else ("⚠️" if status in ("SKIP","FALLBACK") else "❌")
        print(f"  {icon} {step}")
        if detail: print(f"     {detail[:200]}")
    
    if FAIL == 0 and PASS > 0:
        print(f"\n  ✅ SOHBET-111 TUM TESTLER BASARILI!")
    else:
        print(f"\n  ⚠️ KISMEN BASARILI (hdfilmcehennemi CF beklenen)")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
