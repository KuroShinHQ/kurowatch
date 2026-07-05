"""tranimaci.com HOME sayfasinden yeni URL formatini al"""
import asyncio, sys, re
sys.path.insert(0, '.')

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

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

        # HOME sayfayi yükle ve PoW'i bekle
        print("1. HOME sayfasi yukleniyor...")
        await page.goto('https://tranimaci.com/', timeout=45000, wait_until="domcontentloaded")

        # PoW tamamlanana kadar bekle (max 20sn)
        for i in range(20):
            await asyncio.sleep(1)
            title = await page.title()
            url = page.url
            if 'Security' not in title and 'Verification' not in title:
                print(f"   PoW cozuldu! ({i+1}sn) Title: {title}")
                break
            if i % 5 == 0:
                print(f"   {i+1}sn: title='{title}', url={url}")

        print(f"\n2. Final URL: {page.url}, Title: {await page.title()}")

        # Episode linkleri
        links = await page.evaluate("""
            () => {
                const anchors = Array.from(document.querySelectorAll('a'));
                return anchors
                    .filter(a => a.href && a.href.includes('/video/'))
                    .map(a => ({href: a.href, text: a.textContent.trim().slice(0, 40)}))
                    .slice(0, 20);
            }
        """)
        print(f"\n3. Video links ({len(links)}):")
        for l in links:
            print(f"   {l}")

        # HTML icinde /anime/ linkleri
        html = await page.content()
        anime_links = re.findall(r'href="(https?://tranimaci\.com/anime/[^"]+)"', html)
        print(f"\n4. Anime links: {anime_links[:10]}")

        # API endpoints
        try:
            konosuba_api = await page.evaluate("""
                async () => {
                    try {
                        const r = await fetch('/api/animes?q=konosuba&limit=5');
                        if (!r.ok) return {status: r.status};
                        return await r.json();
                    } catch(e) { return {error: e.message}; }
                }
            """)
            print(f"\n5. /api/animes?q=konosuba: {str(konosuba_api)[:300]}")
        except Exception as e:
            print(f"\n5. API test error: {e}")

        await browser.close()

asyncio.run(test())
