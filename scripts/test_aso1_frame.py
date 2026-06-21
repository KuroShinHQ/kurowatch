"""aso1.net iframe içine girip m3u8 stream yakalamayı test eder."""
import asyncio

async def test():
    from playwright.async_api import async_playwright

    ep_url = "https://www.turkanime.tv/video/sousou-no-frieren-1-bolum"
    found_streams = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required",
                  "--disable-web-security"]  # cross-origin frame erişimi için
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            locale="tr-TR",
        )
        page = await ctx.new_page()

        def on_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest", ".ts?")):
                if not any(x in url for x in ("google", "youtube", "gstatic")):
                    print(f"STREAM: {url[:120]}")
                    found_streams.append(url)

        # Ana sayfa + tüm frame istekleri dinle
        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=20000, wait_until="networkidle")
        print("Sayfa yüklendi")

        # Frame'leri listele
        all_frames = page.frames
        print(f"\nToplam frame: {len(all_frames)}")
        for fr in all_frames:
            print(f"  Frame: {fr.url[:80]}")

        # aso1 frame'ine gir
        aso1_frame = None
        for fr in all_frames:
            if "aso1.net" in fr.url:
                aso1_frame = fr
                print(f"\naso1 frame bulundu: {fr.url}")
                break

        if aso1_frame:
            # Frame içindeki video/play elementleri
            try:
                video_els = await aso1_frame.query_selector_all("video, .play-btn, [class*=play], button")
                print(f"Frame içi elementler: {len(video_els)}")
                for el in video_els[:5]:
                    tag = await el.get_attribute("class") or await el.evaluate("el => el.tagName")
                    print(f"  El: {tag}")

                # Video src dene
                vid = await aso1_frame.query_selector("video")
                if vid:
                    src = await vid.get_attribute("src") or ""
                    curr = await vid.evaluate("el => el.currentSrc || ''")
                    print(f"video.src={src[:80]} currentSrc={curr[:80]}")
            except Exception as e:
                print(f"Frame erişim hatası: {e}")

        print("\n15sn stream bekleniyor...")
        await asyncio.sleep(15)

        print(f"\nYakalanan stream: {len(found_streams)}")
        for s in found_streams[:5]:
            print(f"  {s[:120]}")

        await browser.close()

asyncio.run(test())
