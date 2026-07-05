"""tranimaci.com Playwright - www. olmadan episode embed bul"""
import asyncio, sys, re
sys.path.insert(0, '.')

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    url = 'https://tranimaci.com/video/kono-subarashii-sekai-ni-shukufuku-wo-3-1-bolum'
    captured = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
        )
        try:
            await Stealth().apply_stealth_async(ctx)
        except Exception:
            pass

        page = await ctx.new_page()

        def on_req(req):
            u = req.url
            if any(k in u for k in ('m3u8', '.mp4', '/embed/', '/player/', 'filemoon', 'vidmoly',
                                      'doodstream', 'streamtape', 'voe.sx', 'aso1.net',
                                      'pichive', 'anizmplayer', '__waf', '/video/')):
                if u not in captured:
                    captured.append(u)
                    print(f"  [REQ] {u[:100]}")

        page.on("request", on_req)

        print(f"1. goto: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        print(f"   URL after goto: {page.url}")

        # PoW bekle - networkidle (25sn)
        print("2. PoW + networkidle bekleniyor (25sn)...")
        try:
            await page.wait_for_load_state("networkidle", timeout=25000)
        except Exception as e:
            print(f"   networkidle: {e}")

        print(f"   URL: {page.url}")
        try:
            title = await page.title()
            print(f"   Title: {title}")
        except Exception:
            print("   (navigation devam ediyor)")
            await asyncio.sleep(3)
            print(f"   URL: {page.url}, Title: {await page.title()}")

        # 15 sn daha bekle - player yuklensin
        print("3. 15sn player bekleniyor...")
        await asyncio.sleep(15)

        print(f"   URL: {page.url}")
        title = await page.title()
        print(f"   Title: {title}")

        # iframe/video bul
        try:
            elements = await page.evaluate("""
                () => {
                    const r = [];
                    document.querySelectorAll('iframe').forEach(el => {
                        r.push({tag: 'iframe', src: el.src || el.getAttribute('data-src') || '', id: el.id, cls: el.className});
                    });
                    document.querySelectorAll('video').forEach(el => {
                        r.push({tag: 'video', src: el.src || el.currentSrc || '', cls: el.className});
                    });
                    return r;
                }
            """)
            print(f"\n4. iframe/video elements: {elements}")
        except Exception as e:
            print(f"4. error: {e}")

        # Player related divler
        try:
            player_els = await page.evaluate("""
                () => Array.from(document.querySelectorAll('[class*="player"],[class*="video"],[id*="player"],[id*="video"]'))
                    .map(el => ({tag: el.tagName, cls: el.className.slice(0,50), id: el.id.slice(0,30)}))
                    .slice(0, 10)
            """)
            print(f"\n5. Player elements: {player_els}")
        except Exception as e:
            print(f"5. error: {e}")

        # HTML analiz
        html = await page.content()
        print(f"\n6. HTML len: {len(html)}")
        iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
        print(f"   iframes: {iframes[:5]}")
        datasrc = re.findall(r'data-src="([^"]+)"', html, re.I)
        print(f"   data-src: {datasrc[:5]}")
        api_calls = re.findall(r'fetch\(["\']([^"\']+)["\']', html)
        print(f"   fetch calls: {api_calls[:5]}")

        print(f"\n7. Captured requests ({len(captured)}):")
        for r in captured:
            print(f"   {r[:100]}")

        await browser.close()

asyncio.run(test())
