"""tranimaci.com - PoW sonrasi sayfa yüklenir, yeni URL/ep formatini bul"""
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

        # HOME sayfayi yükle
        print("1. HOME sayfasi yukleniyor...")
        await page.goto('https://tranimaci.com/', timeout=45000, wait_until="domcontentloaded")

        # PoW tamamlanip sayfa reload'u bitene kadar bekle
        print("2. PoW + reload bekleniyor (networkidle max 30sn)...")
        try:
            await page.wait_for_load_state("networkidle", timeout=30000)
        except Exception as e:
            print(f"   networkidle timeout: {e}")

        # Ekstra 3sn
        await asyncio.sleep(3)

        try:
            final_url = page.url
            title = await page.title()
            print(f"3. Final URL: {final_url}")
            print(f"   Title: {title}")
        except Exception as e:
            print(f"   title/url error (navigation devam ediyor?): {e}")
            await asyncio.sleep(5)
            final_url = page.url
            title = await page.title()
            print(f"   Retry URL: {final_url}, Title: {title}")

        # Episode linkleri
        try:
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href && a.href.includes('/video/'))
                    .map(a => ({href: a.href, text: a.textContent.trim().slice(0,40)}))
                    .slice(0, 15)
            """)
            print(f"\n4. Video links ({len(links)}):")
            for l in links:
                print(f"   {l}")
        except Exception as e:
            print(f"4. error: {e}")

        # Anime sayfasina git
        try:
            print("\n5. Konosuba anime sayfasi...")
            await page.goto('https://tranimaci.com/anime/konosuba-s3/', timeout=30000, wait_until="networkidle")
            await asyncio.sleep(3)
            ep_links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href && a.href.includes('/video/'))
                    .map(a => ({href: a.href, text: a.textContent.trim().slice(0,40)}))
                    .slice(0, 10)
            """)
            print(f"   Episode links ({len(ep_links)}):")
            for l in ep_links:
                print(f"   {l}")

            # HTML analiz
            html = await page.content()
            ep_hrefs = re.findall(r'href="(/video/[^"]+)"', html)
            print(f"   /video/ hrefs in HTML: {ep_hrefs[:10]}")
        except Exception as e:
            print(f"5. error: {e}")

        # API test
        try:
            result = await page.evaluate("""
                async () => {
                    const endpoints = [
                        '/api/animes?q=konosuba&limit=3',
                        '/api/episodes?anime=konosuba-s3',
                        '/api/content?q=konosuba',
                    ];
                    for (const ep of endpoints) {
                        try {
                            const r = await fetch(ep);
                            if (r.ok) {
                                const data = await r.json();
                                return {endpoint: ep, data: JSON.stringify(data).slice(0,300)};
                            }
                        } catch(e) {}
                    }
                    return null;
                }
            """)
            print(f"\n6. API result: {result}")
        except Exception as e:
            print(f"6. API error: {e}")

        await browser.close()

asyncio.run(test())
