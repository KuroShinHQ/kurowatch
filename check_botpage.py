"""Bot Kontrol sayfasının HTML'ini incele - ne gerekiyor?"""
import asyncio

async def main():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    url = "https://www.tranimeizle.co/dungeon-meshi-1-bolum-izle"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        html = await page.content()

        # Bot kontrol sayfasında ne var?
        # form, script, button ara
        import re
        forms = re.findall(r'<form[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE)
        print(f"Form sayısı: {len(forms)}")
        for i, f in enumerate(forms):
            print(f"Form[{i}]: {f[:300]}")

        # Script içeriğine bak (kısa olanlar)
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
        print(f"\nScript sayısı: {len(scripts)}")
        for i, s in enumerate(scripts[:5]):
            if len(s.strip()) < 2000 and s.strip():
                print(f"Script[{i}] ({len(s)} karakter): {s[:300]}")

        # meta tag'ler
        metas = re.findall(r'<meta[^>]+>', html, re.IGNORECASE)
        for m in metas:
            if 'cookie' in m.lower() or 'token' in m.lower() or 'bot' in m.lower():
                print(f"meta: {m}")

        # Buton/link metinleri
        buttons = re.findall(r'<button[^>]*>(.*?)</button>', html, re.DOTALL | re.IGNORECASE)
        print(f"\nButton sayısı: {len(buttons)}")
        for b in buttons:
            print(f"  Button: {b[:100]}")

        # div.bot-check veya benzer sınıflar
        divs = re.findall(r'<div[^>]*class="[^"]*bot[^"]*"[^>]*>.*?</div>', html, re.DOTALL | re.IGNORECASE)
        print(f"\nBot-class div sayısı: {len(divs)}")
        for d in divs[:3]:
            print(f"  {d[:200]}")

        await browser.close()

asyncio.run(main())
