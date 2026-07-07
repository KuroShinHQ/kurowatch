#!/usr/bin/env python3
"""
SOHBET-110 Asama 3 — CANLI TEST (v5)
Deep test: hdfilmcehennemi CF bypass strategies + dizigom + yt-dlp spidypro
"""
import asyncio, sys, os, re

sys.path.insert(0, "/mnt/c/Kuroshin/kurowatch")
os.chdir("/mnt/c/Kuroshin/kurowatch")

from backend.scraper.parsers import resolve_embed_with_ytdlp
from playwright.async_api import async_playwright

PASS = 0
FAIL = 0
LOG = []

_KNOWN_HOSTS = ("vidmoly", "streamtape", "filemoon", "upstream", "mixdrop", "spidypro")

def ll(step, status, detail=""):
    global PASS, FAIL
    LOG.append((step, status, detail))
    if status == "PASS": PASS += 1
    elif status == "FAIL": FAIL += 1
    icon = "✅" if status == "PASS" else ("⚠️" if status in ("SKIP","FALLBACK") else "❌")
    print(f"  {icon} [{status}] {step}")
    if detail: print(f"     {detail[:250]}")

async def pw_capture(url, play_sel, popup_sel=None, goto_wait="commit", extra_wait=10):
    """PW: navigate, wait, click, capture."""
    found = []
    def on_req(req):
        u = req.url
        if u.endswith((".js",".css",".png",".ico",".svg",".woff",".woff2")): return
        if any(h in u for h in _KNOWN_HOSTS) or re.search(r"\.m3u8|/hls/|\.mp4\?", u, re.I) or "/embed/" in u:
            if u not in found: found.append(u)

    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True, args=["--no-sandbox","--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}, locale="tr-TR",
        )
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
        except: pass
        
        page = await ctx.new_page()
        page.on("request", on_req)
        
        status = 0
        try:
            resp = await page.goto(url, timeout=30000, wait_until=goto_wait)
            status = resp.status if resp else 0
        except Exception as e:
            print(f"  goto FAIL: {type(e).__name__}")
            await b.close()
            return None, None
        
        # Wait extra time for CF + JS rendering
        await asyncio.sleep(extra_wait)
        
        # Try to also wait for network idle (non-blocking)
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except: pass
        
        # Check page content
        try:
            title = await page.title()
            html_parts = (await page.content())[:500]
        except: title = "N/A"; html_parts = ""
        
        print(f"  HTTP {status}, title: {title[:80]}")
        
        # Popups
        if popup_sel:
            for sel in popup_sel:
                try:
                    if await page.locator(sel).first.is_visible(timeout=1000):
                        await page.locator(sel).first.click()
                        await asyncio.sleep(0.5)
                except: pass
        
        # Click play
        for sel in play_sel:
            try:
                if await page.locator(sel).first.is_visible(timeout=3000):
                    await page.locator(sel).first.click(force=True)
                    print(f"  Click: {sel}")
                    await asyncio.sleep(1)
            except: pass
        
        await asyncio.sleep(3)
        try: await page.wait_for_load_state("networkidle", timeout=10000)
        except: pass
        await asyncio.sleep(2)
        await b.close()
    
    return found[0] if found else None, title

async def test_hdfilm_domains():
    print(f"\n{'='*55}")
    print(f"  TEST 1: hdfilmcehennemi — CF bypass stratejileri")
    print(f"{'='*55}")
    
    # Strategy A: .name domain with extra wait
    print("\n── A) hdfilmcehennemi.name /hesaplasma-2-izle/ ──")
    embed, title = await pw_capture(
        "https://hdfilmcehennemi.name/hesaplasma-2-izle/",
        [".play-that-video", ".play-button", "#play"],
        extra_wait=15,
    )
    if embed:
        ll("PW: hdfilmcehennemi.name", "PASS", embed[:200])
        return embed
    
    # Strategy B: different slug
    print("\n── B) hdfilmcehennemi.name /superman-izle-hd1/ ──")
    embed, title = await pw_capture(
        "https://hdfilmcehennemi.name/superman-izle-hd1/",
        [".play-that-video", ".play-button", "#play"],
        extra_wait=15,
    )
    if embed:
        ll("PW: hdfilmcehennemi.name (superman)", "PASS", embed[:200])
        return embed
    
    # Strategy C: Search for film links on homepage
    print("\n── C) hdfilmcehennemi.name ana sayfadan link tara ──")
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await b.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}, locale="tr-TR",
        )
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(ctx)
        except: pass
        page = await ctx.new_page()
        await page.goto("https://hdfilmcehennemi.name/", timeout=30000, wait_until="commit")
        await asyncio.sleep(20)  # wait for CF to clear
        html = await page.content()
        links = re.findall(r'href="(https://hdfilmcehennemi\.name/[^"]+?-(?:izle|izle-hd\d+)/)"', html)
        links = list(dict.fromkeys(links))
        print(f"  Film linkleri: {len(links)}")
        for l in links[:5]: print(f"    {l}")
        await b.close()
        
        if links:
            embed, _ = await pw_capture(links[0], [".play-that-video", ".play-button", "#play"], extra_wait=8)
            if embed:
                ll("PW: hdfilmcehennemi (from homepage)", "PASS", embed[:200])
                return embed
    
    ll("hdfilmcehennemi (all strategies)", "FAIL", "CF bypass basarisiz")
    return None

async def test_dizigom():
    print(f"\n{'='*55}")
    print(f"  TEST 2: dizigom.love")
    print(f"{'='*55}")
    
    embed, title = await pw_capture(
        "https://www.dizigom.love/silo-3-sezon-1-bolum/",
        [".player-area iframe", ".video-js", "#player iframe", ".tab-link:first-child"],
        extra_wait=5,
    )
    
    if embed:
        ll("PW: dizigom", "PASS", embed[:200])
        # yt-dlp on spidypro embed
        video = await resolve_embed_with_ytdlp(embed)
        if video and video != embed:
            ll("yt-dlp: dizigom embed", "PASS", video[:250])
        else:
            ll("yt-dlp: dizigom embed", "SKIP", "embed as-is")
        return True
    else:
        ll("PW: dizigom", "FAIL", "no embed")
        return False

async def test_ytdlp_direct():
    """Direct yt-dlp test on spidypro embed."""
    print(f"\n{'='*55}")
    print(f"  TEST 3: yt-dlp direkt (spidypro embed)")
    print(f"{'='*55}")
    
    embed = "https://spidypro.com/embed/SlZtHbZ1S73V2hO"
    video = await resolve_embed_with_ytdlp(embed)
    if video and video != embed:
        ll("yt-dlp: spidypro", "PASS", video[:250])
        return True
    else:
        ll("yt-dlp: spidypro", "FAIL" if video == embed else "SKIP", str(video)[:200])
        return False

async def main():
    print("="*55)
    print("  SOHBET-110 ASAMA 3 — CANLI TEST")
    print("  WSL + Playwright 1.58 + yt-dlp 2026.6.9")
    print("  7 Temmuz 2026")
    print("="*55)

    hdfilm_result = await test_hdfilm_domains()
    if hdfilm_result:
        video = await resolve_embed_with_ytdlp(hdfilm_result)
        if video and video != hdfilm_result:
            ll("yt-dlp: hdfilmcehennemi", "PASS", video[:250])
        else:
            ll("yt-dlp: hdfilmcehennemi", "SKIP", "embed as-is")
    
    await test_dizigom()
    await test_ytdlp_direct()

    print(f"\n{'='*55}")
    print(f"  RAPOR: {PASS} PASS / {FAIL} FAIL")
    for step, status, detail in LOG:
        icon = "✅" if status == "PASS" else ("⚠️" if status in ("SKIP","FALLBACK") else "❌")
        print(f"  {icon} {step}")
        if detail: print(f"     {detail[:200]}")
    print(f"\n  Pipeline status: ", end="")
    if FAIL == 0:
        print("✅ FULL PASS")
    elif PASS > 0:
        print("⚠️ KISMEN BASARILI (hdfilmcehennemi CF korumali)")
        print("  → Cozum: cookies.txt kullanimi veya farkli domain stratejisi")
    else:
        print("❌ TUMU BASARISIZ")
    return 0 if FAIL == 0 else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
