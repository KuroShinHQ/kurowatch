import asyncio, re

async def search_turkanime_playwright(query: str) -> list:
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    results = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto("https://www.turkanime.tv/", timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(1)

        box = page.locator("input[type='search']").first
        await box.fill(query)
        await asyncio.sleep(0.5)
        await box.press("Enter")

        # /arama sayfası yüklensin ve AJAX sonuçlar gelsin
        try:
            await page.wait_for_url("**/arama**", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(4)  # AJAX sonuçları için bekle

        html = await page.content()
        links = re.findall(r"turkanime\.tv(/video/[^\"'<>\s]+)", html)
        results = list(dict.fromkeys(links))

        # Ayrıca /gelismis (gelişmiş arama) sonuçları kontrol et
        gelismis = re.findall(r'href=["\']https://www\.turkanime\.tv(/video/[^"\']+)["\']', html)
        for g in gelismis:
            if g not in results:
                results.append(g)

        # Tüm a href içindeki /video/ linkleri
        all_links = re.findall(r'href=["\'](?:https://www\.turkanime\.tv)?(/video/[^"\'?#\s]+)["\']', html)
        for l in all_links:
            if l not in results:
                results.append(l)

        await browser.close()

    return list(dict.fromkeys(results))


async def main():
    queries = ["attack on titan", "bofuri", "code geass", "danmachi", "assassination classroom"]
    for q in queries:
        links = await search_turkanime_playwright(q)
        print(f"'{q}': {links[:5]}")

asyncio.run(main())
