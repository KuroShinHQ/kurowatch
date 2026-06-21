"""turkanime.tv popup kapat → video player bul → stream yakala."""
import asyncio, re

async def test():
    from playwright.async_api import async_playwright

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
        )
        page = await ctx.new_page()

        def on_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", ".ts?", "/hls/", "manifest")):
                if not any(x in url for x in ("google", "youtube", "gstatic")):
                    print(f"STREAM: {url[:120]}")
                    found_streams.append(url)

        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Popup'ları kapat
        popup_closers = [
            "button.close", ".modal .close", ".modal button[data-dismiss]",
            ".popup-close", ".modal-close", "[aria-label='Close']",
            ".closeBtn", "#closeModal", "button.btn-close",
            ".fancybox-close", ".mfp-close",
        ]
        for sel in popup_closers:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=500):
                    await el.click()
                    print(f"Popup kapatıldı: {sel}")
                    await asyncio.sleep(1)
                    break
            except Exception:
                pass

        # Escape ile de dene
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        await page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_after_popup.png")

        # Tüm iframe'leri listele
        all_iframes = await page.query_selector_all("iframe")
        print(f"\niframe sayısı: {len(all_iframes)}")
        for f in all_iframes:
            src = await f.get_attribute("src") or await f.get_attribute("data-src") or ""
            print(f"  iframe: {src[:100]}")

        # HTML'de video/player araması
        html = await page.content()

        # jwplayer, videojs, hls.js referansları
        player_hits = re.findall(r'(jwplayer|videojs|hls\.js|JWPlayer|flowplayer|plyr)', html, re.I)
        print(f"\nPlayer teknolojileri: {set(player_hits)}")

        # file: veya sources: içeren JS
        file_matches = re.findall(r'(?:file|src|source)\s*:\s*["\']([^"\']+\.(?:m3u8|mp4))["\']', html, re.I)
        print(f"\nDoğrudan video URL'leri: {file_matches[:5]}")

        # 15sn bekle ve stream yakala
        print("\n15sn stream bekleniyor...")
        await asyncio.sleep(15)

        print(f"\nYakalanan stream: {len(found_streams)}")
        for s in found_streams[:5]:
            print(f"  {s[:120]}")

        await browser.close()

asyncio.run(test())
