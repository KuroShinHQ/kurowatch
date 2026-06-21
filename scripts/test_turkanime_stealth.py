"""playwright-stealth ile turkanime.tv stream test."""
import asyncio

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    ep_url = "https://www.turkanime.tv/video/sousou-no-frieren-1-bolum"
    found_streams = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            locale="tr-TR",
            viewport={"width": 1280, "height": 720},
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)

        def on_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest", ".ts?")):
                if not any(x in url for x in ("google", "youtube", "gstatic")):
                    print(f"STREAM: {url[:120]}")
                    found_streams.append(url)

        ctx.on("request", on_req)

        print("Stealth ile yükleniyor...")
        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Popup kapat
        for sel in ["button.close", ".modal .close", ".mfp-close", "button[data-dismiss='modal']"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=500):
                    await el.click()
                    print(f"Popup kapatıldı: {sel}")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        # Screenshot
        await page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_stealth.png")
        print("Screenshot alındı")

        # 15sn stream bekle
        print("15sn bekleniyor...")
        await asyncio.sleep(15)

        # iframe kontrol
        iframes = await page.query_selector_all("iframe")
        print(f"\niframe sayısı: {len(iframes)}")
        for f in iframes:
            src = await f.get_attribute("src") or ""
            if src and "aso1" not in src:
                print(f"  FARKLI iframe: {src[:100]}")

        print(f"\nStream sayısı: {len(found_streams)}")
        for s in found_streams[:5]:
            print(f"  {s[:120]}")

        await browser.close()

asyncio.run(test())
