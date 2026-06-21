"""diziwatch.ac Playwright DOM debug."""
import asyncio

async def main():
    from playwright.async_api import async_playwright

    url = "https://diziwatch.ac/dizi/solo-leveling/sezon-1/bolum-1"
    print(f"Playwright debug: {url}")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
        )
        page = await ctx.new_page()

        # Network request izle
        requests_seen = []
        def on_req(req):
            u = req.url
            if any(x in u for x in ('iframe', 'embed', 'player', 'm3u8', 'mp4', 'pichive', 'stream')):
                requests_seen.append(u)

        page.on("request", on_req)

        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass

        import asyncio
        await asyncio.sleep(5)

        # Tüm iframe elementleri
        iframes = await page.query_selector_all("iframe")
        print(f"\niframe count: {len(iframes)}")
        for el in iframes:
            src = await el.get_attribute("src") or ""
            data_src = await el.get_attribute("data-src") or ""
            print(f"  src={src[:100]}  data-src={data_src[:100]}")

        # JS eval ile iframe
        js_iframes = await page.evaluate("""
            () => {
                const r = [];
                document.querySelectorAll('iframe, frame').forEach(el => {
                    const s = el.src || el.getAttribute('data-src') || el.getAttribute('data-lazy-src') || '';
                    r.push(s);
                });
                return r;
            }
        """)
        print(f"\nJS iframe srcs: {js_iframes[:10]}")

        # Network requests
        print(f"\nİlgili network istekleri ({len(requests_seen)}):")
        for r in requests_seen[:10]:
            print(f"  {r[:100]}")

        # Page source'da iframe ara
        html = await page.content()
        import re
        static_iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        print(f"\nHTML'deki iframe src'ler: {static_iframes[:5]}")

        await browser.close()

asyncio.run(main())
