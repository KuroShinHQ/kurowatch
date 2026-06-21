"""turkanime.tv: popup kapat → sunucu tıkla → stream yakala."""
import asyncio, re

async def test():
    from playwright.async_api import async_playwright

    ep_url = "https://www.turkanime.tv/video/sousou-no-frieren-1-bolum"
    found_streams = []
    found_embeds = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            locale="tr-TR",
            viewport={"width": 1280, "height": 800},
        )
        page = await ctx.new_page()

        def on_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest")):
                if not any(x in url for x in ("google", "gstatic")):
                    print(f"  STREAM: {url[:120]}")
                    found_streams.append(url)
            if "embed" in url or "iframe" in url or "player" in url:
                if not any(x in url for x in ("google", "gstatic", ".js", ".css")):
                    print(f"  EMBED REQ: {url[:100]}")
                    found_embeds.append(url)

        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # 1. Popup kapat
        try:
            btn = page.locator("button.site-popup-close").first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                print("✅ Popup kapatıldı (site-popup-close)")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"  Popup kapat hatası: {e}")

        await page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_click1.png")

        # 2. Sunucu butonlarını bul
        server_btns = await page.query_selector_all("button.btn.btn-sm.btn-default")
        print(f"\nSunucu butonu sayısı: {len(server_btns)}")
        for b in server_btns[:5]:
            txt = await b.inner_text()
            onclick = await b.get_attribute("onclick") or ""
            print(f"  '{txt.strip()}' → {onclick[:60]}")

        # 3. İlk sunucuya tıkla (Varsayılan veya ilk)
        varsayilan = None
        for b in server_btns:
            txt = await b.inner_text()
            if "Varsayılan" in txt or "varsayilan" in txt.lower():
                varsayilan = b
                break

        target_btn = varsayilan or (server_btns[0] if server_btns else None)
        if target_btn:
            txt = await target_btn.inner_text()
            print(f"\nTıklanıyor: '{txt.strip()}'")
            await target_btn.click()
            print("Tıklandı, 12sn bekleniyor...")
            await asyncio.sleep(12)
        else:
            print("Sunucu butonu bulunamadı!")

        await page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_click2.png")

        # iframe kontrol
        iframes = await page.query_selector_all("iframe")
        print(f"\niframe sayısı: {len(iframes)}")
        for f in iframes:
            src = await f.get_attribute("src") or ""
            print(f"  iframe: {src[:100]}")

        print(f"\nStream: {len(found_streams)}")
        for s in found_streams[:5]:
            print(f"  {s[:120]}")
        print(f"\nEmbed: {len(found_embeds)}")
        for e in found_embeds[:5]:
            print(f"  {e[:100]}")

        await browser.close()

asyncio.run(test())
