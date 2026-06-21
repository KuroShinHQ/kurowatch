import asyncio, re

async def main():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)

        async def on_req(r):
            if "turkanime.tv/arama" in r.url and r.method == "POST":
                try:
                    body = r.post_data
                    print("POST DATA:", body[:200] if body else "(bos)")
                except Exception:
                    pass

        page.on("request", on_req)
        await page.goto("https://www.turkanime.tv/", timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        box = page.locator("input[type='search']").first
        await box.fill("attack on titan")
        await asyncio.sleep(0.5)
        await box.press("Enter")
        await asyncio.sleep(3)

        html = await page.content()
        links = re.findall(r"turkanime\.tv(/video/[^\"'<>\s]+)", html)
        links = list(dict.fromkeys(links))[:10]
        print("Arama sonucu URL:", page.url)
        print("Linkler:", links)

        await browser.close()

asyncio.run(main())
