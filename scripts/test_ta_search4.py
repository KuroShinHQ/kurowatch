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
            if "turkanime" in r.url:
                if any(k in r.url for k in ("ajax", "search", "arama", "api", "suggest", "auto", "kelime")):
                    body = ""
                    try:
                        body = r.post_data or ""
                    except Exception:
                        pass
                    print(f"  {r.method} {r.url[:150]} | body={body[:80]}")

        page.on("request", on_req)
        await page.goto("https://www.turkanime.tv/", timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Harfi harfine yaz — autocomplete tetiklesin
        box = page.locator("input[type='search']").first
        if await box.is_visible(timeout=2000):
            for ch in "attack":
                await box.press(ch)
                await asyncio.sleep(0.3)
            await asyncio.sleep(2)

        await browser.close()

asyncio.run(main())
