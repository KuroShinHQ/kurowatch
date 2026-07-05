"""tranimaci.com Playwright debug - sayfanin gercekten yuklenip yuklenmedigini goster"""
import asyncio
import sys
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
sys.path.insert(0, '.')

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    url = 'https://www.tranimaci.com/video/konosuba-s3-bolum-1/'
    captured_requests = []
    captured_iframes = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
        )

        try:
            await Stealth().apply_stealth_async(ctx)
        except Exception as e:
            print(f"stealth warning: {e}")

        page = await ctx.new_page()

        def on_req(req):
            u = req.url
            if any(k in u for k in ('m3u8', '.mp4', '/embed/', '/player/', 'filemoon', 'vidmoly', 'doodstream', 'streamtape', '__waf', 'api', 'ajax', 'video')):
                captured_requests.append(u)
                print(f"  [REQ] {u[:100]}")

        page.on("request", on_req)

        print(f"\n1. goto: {url}")
        await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        print(f"   URL after goto: {page.url}")

        # PoW challenge tamamlanmasini bekle (max 15sn)
        print("\n2. networkidle bekle (25sn)...")
        try:
            await page.wait_for_load_state("networkidle", timeout=25000)
            print(f"   networkidle OK, URL: {page.url}")
        except Exception as e:
            print(f"   networkidle timeout (OK): {e}")
            print(f"   URL after timeout: {page.url}")

        # Sayfa durumu
        title = await page.title()
        print(f"\n3. Sayfa title: '{title}'")
        print(f"   URL: {page.url}")

        # iframe'leri topla
        try:
            js_result = await page.evaluate("""
                () => {
                    const r = [];
                    document.querySelectorAll('iframe, frame').forEach(el => {
                        r.push({src: el.src, dataSrc: el.getAttribute('data-src'), id: el.id, class: el.className});
                    });
                    document.querySelectorAll('video, video source').forEach(el => {
                        r.push({src: el.src || el.currentSrc, type: 'video'});
                    });
                    return r;
                }
            """)
            print(f"\n4. iframe/video elements: {js_result}")
        except Exception as e:
            print(f"\n4. JS eval error: {e}")

        # Player-related elements
        try:
            selectors = [
                '#player', '.player', '.video-player', '.embed-player',
                '.source-btn', '.server-btn', '.btn-server',
                '[data-source]', '[data-server]',
                '.player-wrapper', '#video-container'
            ]
            for sel in selectors:
                try:
                    els = await page.query_selector_all(sel)
                    if els:
                        print(f"\n5. Found '{sel}': {len(els)} element(s)")
                        for el in els[:2]:
                            html_snippet = await el.inner_html()
                            print(f"   -> {html_snippet[:200]}")
                except Exception:
                    pass
        except Exception as e:
            print(f"\n5. selector error: {e}")

        # HTML son durumu
        html = await page.content()
        print(f"\n6. Page HTML length: {len(html)}")

        # Ilginc class'lari bul
        import re
        classes = re.findall(r'class="([^"]{5,50})"', html)
        player_classes = [c for c in classes if any(k in c.lower() for k in ['player', 'video', 'server', 'source', 'embed'])]
        print(f"   Player-related classes: {list(set(player_classes))[:15]}")

        # iframe src'leri
        iframes = re.findall(r'<iframe[^>]+src="([^"]+)"', html, re.I)
        print(f"   iframe srcs: {iframes[:5]}")

        # data-src'leri
        datasrcs = re.findall(r'data-src="([^"]+)"', html, re.I)
        print(f"   data-srcs: {datasrcs[:5]}")

        print(f"\n7. Captured requests: {len(captured_requests)}")
        for r in captured_requests[:20]:
            print(f"   {r[:100]}")

        # 10 saniye daha bekle ve tekrar kontrol
        print("\n8. 10 saniye daha bekliyoruz...")
        await asyncio.sleep(10)

        html2 = await page.content()
        iframes2 = re.findall(r'<iframe[^>]+src="([^"]+)"', html2, re.I)
        print(f"   iframe srcs after +10s: {iframes2[:5]}")
        print(f"   Captured requests total: {len(captured_requests)}")

        await browser.close()

asyncio.run(test())
