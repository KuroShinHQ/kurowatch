"""tranimaci.com yeni URL formatini Playwright ile bul"""
import asyncio
import sys
import re
import json

sys.path.insert(0, '.')

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    # Anime sayfasindan ep URL'lerini bul
    anime_url = 'https://tranimaci.com/anime/konosuba-s3/'
    captured = []

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
        except Exception:
            pass

        page = await ctx.new_page()

        def on_req(req):
            u = req.url
            if 'video' in u.lower() or 'episode' in u.lower() or 'bolum' in u.lower():
                if u not in captured:
                    captured.append(u)
                    print(f"  [REQ] {u[:100]}")

        page.on("request", on_req)

        print(f"1. goto: {anime_url}")
        await page.goto(anime_url, timeout=45000, wait_until="domcontentloaded")
        print(f"   URL: {page.url}")

        # PoW bekle
        try:
            await page.wait_for_load_state("networkidle", timeout=25000)
        except Exception:
            pass

        print(f"   URL after networkidle: {page.url}")
        title = await page.title()
        print(f"   Title: {title}")

        # 5 sn bekle
        await asyncio.sleep(5)

        # Sayfadaki episode link'lerini bul
        try:
            links = await page.evaluate("""
                () => {
                    const anchors = Array.from(document.querySelectorAll('a[href*="video"]'));
                    return anchors.map(a => ({href: a.href, text: a.textContent.trim().slice(0,50)}));
                }
            """)
            print(f"\n2. Video links found: {len(links)}")
            for l in links[:10]:
                print(f"   {l}")
        except Exception as e:
            print(f"2. Error: {e}")

        # HTML iceriginden URL'leri ara
        html = await page.content()
        video_paths = re.findall(r'["\'](/video/[^"\'<>\s]+)["\']', html)
        print(f"\n3. /video/ paths in HTML: {video_paths[:10]}")

        # API cagrilarini ara
        api_calls = [u for u in captured if 'api' in u.lower()]
        print(f"\n4. API calls: {api_calls[:10]}")

        await browser.close()

asyncio.run(test())
