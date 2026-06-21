"""turkanime.tv tüm XHR/fetch isteklerini izle + popup kapat."""
import asyncio

async def test():
    from playwright.async_api import async_playwright
    from playwright_stealth import Stealth

    ep_url = "https://www.turkanime.tv/video/sousou-no-frieren-1-bolum"
    xhr_reqs = []
    all_reqs = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,  # Headful: bot tespiti atla
            args=["--no-sandbox", "--start-maximized"]
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            locale="tr-TR",
            viewport={"width": 1280, "height": 800},
        )
        page = await ctx.new_page()
        await Stealth().apply_stealth_async(page)

        def on_req(req):
            url = req.url
            rtype = req.resource_type
            if rtype in ("xhr", "fetch"):
                print(f"XHR: [{rtype}] {url[:100]}")
                xhr_reqs.append(url)
            if any(k in url for k in (".m3u8", ".mp4", "stream", "video", "embed")):
                if not any(x in url for x in ("google", "gstatic", "font", ".css", ".js")):
                    print(f"MEDIA: {url[:100]}")

        ctx.on("request", on_req)

        await page.goto(ep_url, timeout=25000, wait_until="domcontentloaded")
        print("DOM yüklendi")
        await asyncio.sleep(5)

        # Popup close butonunun gerçek HTML'ini bul
        modal_html = await page.evaluate("""() => {
            const modals = document.querySelectorAll('.modal, [class*=modal], [class*=popup], .mfp-wrap, .fancybox');
            const r = [];
            modals.forEach(m => r.push(m.outerHTML.substring(0, 200)));
            return r;
        }""")
        print(f"\nModal HTML ({len(modal_html)}):")
        for m in modal_html[:3]:
            print(f"  {m[:150]}")

        # Visible button'ları bul
        visible_btns = await page.evaluate("""() => {
            const btns = document.querySelectorAll('button, a.close, .close, [data-dismiss]');
            const r = [];
            btns.forEach(b => {
                const rect = b.getBoundingClientRect();
                if (rect.width > 0) r.push({
                    tag: b.tagName,
                    cls: b.className.substring(0,60),
                    text: b.innerText.substring(0,20),
                    html: b.outerHTML.substring(0,100)
                });
            });
            return r;
        }""")
        print(f"\nGörünür butonlar ({len(visible_btns)}):")
        for b in visible_btns[:10]:
            print(f"  {b}")

        await browser.close()

asyncio.run(test())
