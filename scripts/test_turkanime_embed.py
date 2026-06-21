"""turkanime.tv embed iframe'ini yükle ve gerçek stream URL'ini yakala."""
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
            viewport={"width": 1280, "height": 800},
        )
        page = await ctx.new_page()

        embed_iframes = []

        def on_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest", ".ts?")):
                if "err.mp4" not in url and not any(x in url for x in ("google", "gstatic")):
                    print(f"  STREAM: {url[:120]}")
                    found_streams.append(url)
            if "turkanime.tv/embed" in url and "#/url/" in url:
                embed_iframes.append(url)

        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Popup kapat
        try:
            btn = page.locator("button.site-popup-close").first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                print("✅ Popup kapatıldı")
                await asyncio.sleep(2)
        except Exception:
            pass

        # Sunucu tıkla
        server_btns = await page.query_selector_all("button.btn.btn-sm.btn-default")
        if server_btns:
            await server_btns[0].click()
            print(f"✅ İlk sunucuya tıklandı")
            await asyncio.sleep(5)

        # Embed iframe src'ini al
        embed_src = None
        iframes = await page.query_selector_all("iframe")
        for f in iframes:
            src = await f.get_attribute("src") or ""
            if "turkanime.tv/embed" in src or "embed/#" in src:
                embed_src = src
                if embed_src.startswith("//"):
                    embed_src = "https:" + embed_src
                print(f"✅ Embed iframe: {embed_src[:100]}")
                break

        if not embed_src:
            print("❌ Embed iframe bulunamadı")
            await browser.close()
            return

        # Embed sayfasını ayrı bir page'de aç
        embed_page = await ctx.new_page()

        def on_embed_req(req):
            url = req.url
            if any(k in url for k in (".m3u8", ".mp4", "/hls/", "manifest")):
                if "err.mp4" not in url:
                    print(f"  EMBED STREAM: {url[:120]}")
                    found_streams.append(url)

        embed_page.on("request", on_embed_req)

        print(f"\nEmbed sayfa yükleniyor...")
        await embed_page.goto(embed_src, timeout=20000, wait_until="domcontentloaded",
                              referer="https://www.turkanime.tv/")
        print("Embed DOM yüklendi, 15sn bekleniyor...")
        await asyncio.sleep(15)

        # Embed HTML analizi
        embed_html = await embed_page.content()
        m3u8_in_html = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', embed_html)
        print(f"HTML'de m3u8: {m3u8_in_html[:3]}")

        # Video element
        vid = await embed_page.query_selector("video")
        if vid:
            src = await vid.get_attribute("src") or ""
            curr = await vid.evaluate("el => el.currentSrc || ''")
            print(f"video.src={src[:80]}")
            print(f"video.currentSrc={curr[:80]}")

        await embed_page.screenshot(path="/mnt/c/Kuroshin/kurowatch/scripts/turkanime_embed.png")
        print("Screenshot: turkanime_embed.png")

        print(f"\nToplam stream: {len(found_streams)}")
        for s in found_streams[:5]:
            print(f"  {s[:120]}")

        await browser.close()

asyncio.run(test())
