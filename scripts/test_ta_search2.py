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

        def on_req(r):
            if "turkanime" in r.url and any(k in r.url for k in ("ara", "search", "arama", "kelime", "api", "ajax")):
                print("REQ:", r.method, r.url[:150])

        page.on("request", on_req)
        await page.goto("https://www.turkanime.tv/", timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Arama kutusunu bul
        selectors = ["input[type='search']", "input[name='kelime']", "#kelime", ".search-input", "input[placeholder]"]
        for sel in selectors:
            try:
                box = page.locator(sel).first
                if await box.is_visible(timeout=1000):
                    print("Arama kutusu bulundu:", sel)
                    await box.fill("attack on titan")
                    await asyncio.sleep(1)
                    await box.press("Enter")
                    await asyncio.sleep(3)
                    print("Yönlendirilen URL:", page.url)
                    html = await page.content()
                    # video linklerini bul
                    links = re.findall(r"turkanime\.tv(/video/[^\"'<>\s]+)", html)
                    links = list(dict.fromkeys(links))[:8]
                    print("Bulunan linkler:", links)
                    break
            except Exception:
                pass

        await browser.close()

asyncio.run(main())
