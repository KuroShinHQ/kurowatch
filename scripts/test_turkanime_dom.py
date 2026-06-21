import asyncio
import re

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
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest", "stream")):
                if not any(x in url for x in ("google", "youtube", "gstatic")):
                    print(f"STREAM REQ: {url[:120]}")
                    found_streams.append(url)

        page.on("request", on_req)

        await page.goto(ep_url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # iframe'leri listele
        iframes = await page.query_selector_all("iframe")
        print(f"\n=== {len(iframes)} iframe bulundu ===")
        for f in iframes:
            src = await f.get_attribute("src") or await f.get_attribute("data-src") or ""
            fid = await f.get_attribute("id") or ""
            cls = await f.get_attribute("class") or ""
            print(f"  iframe: src={src[:80]} id={fid} class={cls[:40]}")

        # Sunucu/player butonları
        html = await page.content()
        server_links = re.findall(r'href=["\']([^"\']*(?:video|embed|player|izle)[^"\']*)["\']', html[:8000], re.I)
        print(f"\n=== Sunucu linkleri ({len(server_links)}) ===")
        for l in server_links[:10]:
            print(f"  {l[:80]}")

        # data-video veya data-src attribute'ları
        data_videos = re.findall(r'data-(?:video|src|embed)["\s]*=["\s]*["\']([^"\']+)["\']', html[:8000], re.I)
        print(f"\n=== data-video/src ({len(data_videos)}) ===")
        for v in data_videos[:5]:
            print(f"  {v[:80]}")

        # 10sn daha bekle ve stream yakala
        print("\n10sn bekleniyor...")
        await asyncio.sleep(10)

        print(f"\n=== Yakalanan stream URL ({len(found_streams)}) ===")
        for s in found_streams[:10]:
            print(f"  {s[:120]}")

        await browser.close()

asyncio.run(test())
