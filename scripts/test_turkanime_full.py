"""turkanime.tv tam HTML analizi — video/embed nerede?"""
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

        ALL_INTERESTING = []
        def on_req(req):
            url = req.url
            # Her isteği logla (filtresiz)
            if any(k in url for k in (".m3u8", ".mp4", ".ts", "/hls/", "manifest",
                                       "stream", "video", "cdn", "embed", "player")):
                if not any(x in url for x in ("google", "youtube", "gstatic", "font", ".css", ".woff")):
                    ALL_INTERESTING.append(url)

        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(8)

        html = await page.content()

        # Tüm iframe src'leri
        all_iframes = re.findall(r'<iframe[^>]+(?:src|data-src)=["\']([^"\']+)["\']', html, re.I)
        print(f"=== İframe'ler ({len(all_iframes)}) ===")
        for i in all_iframes:
            print(f"  {i[:120]}")

        # Embed/video/player ile başlayan scriptler
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.I | re.S)
        video_scripts = [s for s in scripts if any(k in s.lower() for k in
                         ("m3u8", "mp4", "hls", "player", "jwplayer", "videojs", "source", "file:"))]
        print(f"\n=== Video içerikli script ({len(video_scripts)}) ===")
        for s in video_scripts[:3]:
            print(s[:400])
            print("---")

        # data-* attribute'lar
        data_attrs = re.findall(r'data-(?:video|src|file|stream|embed|url)[^>]*=["\']([^"\']+)["\']', html, re.I)
        print(f"\n=== data-* attr ({len(data_attrs)}) ===")
        for d in data_attrs[:10]:
            print(f"  {d[:120]}")

        # Network istekleri
        print(f"\n=== İlginç network istekleri ({len(ALL_INTERESTING)}) ===")
        for r in ALL_INTERESTING[:20]:
            print(f"  {r[:120]}")

        # Screenshot
        await page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_screenshot.png")
        print("\nScreenshot: scripts/turkanime_screenshot.png")

        await browser.close()

asyncio.run(test())
