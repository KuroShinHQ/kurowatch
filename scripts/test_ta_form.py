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
        await page.goto("https://www.turkanime.tv/", timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        html = await page.content()

        # Form ve input'ları bul
        forms = re.findall(r"<form[^>]*>.*?</form>", html, re.DOTALL | re.IGNORECASE)
        print(f"Form sayısı: {len(forms)}")
        for i, f in enumerate(forms[:3]):
            print(f"\nForm[{i}] (ilk 500 char):")
            print(f[:500])

        # Ajax endpoint ipuçları
        ajax_calls = re.findall(r"['\"](/ajax/[^'\"]+)['\"]", html)
        print("\nAjax endpoint'ler:", list(dict.fromkeys(ajax_calls))[:10])

        # Arama ile ilgili JS kodu
        js_search = re.findall(r".{0,50}(arama|search|kelime|ajax).{0,100}", html, re.IGNORECASE)
        for s in js_search[:10]:
            print("JS:", s.strip()[:150])

        await browser.close()

asyncio.run(main())
