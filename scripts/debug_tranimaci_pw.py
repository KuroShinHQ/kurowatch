"""tranimaci.com Playwright debug — Blood Blockade URL testi"""
import asyncio
import re
from playwright.async_api import async_playwright

TEST_URL = "https://tranimaci.com/video/kekkai-sensen-beyond-1-bolum"

async def test():
    found = []
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
            locale="tr-TR",
        )
        page = await ctx.new_page()

        def on_req(req):
            url = req.url
            if any(k in url for k in (".mp4", ".m3u8", "/embed/", "/player/", "/iframe", "videostraeam", "cdn")):
                print("[REQ]", url[:120])
                found.append(url)

        page.on("request", on_req)

        print("[1] Goto:", TEST_URL)
        await page.goto(TEST_URL, timeout=45000, wait_until="domcontentloaded")
        print("[2] domcontentloaded OK")

        try:
            await page.wait_for_load_state("networkidle", timeout=25000)
            print("[3] networkidle OK")
        except Exception:
            print("[3] networkidle TIMEOUT - devam")

        print("[URL]", page.url)
        print("[TITLE]", await page.title())

        # Mevcut buttonları logla
        btns = await page.query_selector_all("button, a.btn, [class*='server'], [class*='source'], [class*='player']")
        print("[BTNS count]", len(btns))
        for b in btns[:10]:
            cls = await b.get_attribute("class") or ""
            txt = (await b.inner_text()).strip()[:40]
            print("  -", cls[:50], "|", txt)

        # Tıklamayı dene
        for sel in [".source-btn", ".server-btn", ".btn-server", ".player-source", "[data-source]",
                    "button.btn", ".btn-primary", "[class*='server']:first-child", "a[href*='player']"]:
            try:
                el = page.locator(sel).first
                vis = await el.is_visible(timeout=1000)
                if vis:
                    print("[BTN FOUND]", sel)
                    await el.click(force=True)
                    print("[BTN CLICKED]", sel)
                    await asyncio.sleep(3)
                    break
            except Exception:
                pass

        print("[4] 45sn bekleniyor...")
        await asyncio.sleep(45)

        # HTML iframe/video
        html = await page.content()
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
        print("[IFRAMES]", iframes[:5])
        videos = re.findall(r'<(?:video|source)[^>]+src=["\']([^"\']+)["\']', html, re.I)
        print("[VIDEOS]", videos[:5])

        # JS ile iframe/video src
        try:
            js_srcs = await page.evaluate("""
                () => {
                    const r = [];
                    document.querySelectorAll('iframe, frame').forEach(el => {
                        const s = el.src || el.getAttribute('data-src');
                        if (s) r.push('iframe: ' + s);
                    });
                    document.querySelectorAll('video, source').forEach(el => {
                        const s = el.src || el.currentSrc;
                        if (s) r.push('video: ' + s);
                    });
                    return r;
                }
            """)
            print("[JS SRCS]", js_srcs[:10])
        except Exception as e:
            print("[JS eval hata]", e)

        print("[FOUND REQs total]", len(found))
        for u in found[:10]:
            print(" ", u[:120])

        await browser.close()

asyncio.run(test())
