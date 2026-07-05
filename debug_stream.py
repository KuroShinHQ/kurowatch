#!/usr/bin/env python3
"""Stream finder teşhis aracı — tranimeizle.co CF/embed debug"""
import asyncio
import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(message)s")

async def main():
    import sqlite3
    db = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        "SELECT e.number, e.url, c.title FROM episode e "
        "JOIN content c ON c.id=e.content_id "
        "WHERE c.title LIKE '%Dungeon%' ORDER BY e.number LIMIT 5"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("DB'de Dungeon Meshi bulunamadı")
        return

    print("=== Dungeon Meshi episodları ===")
    for row in rows:
        print(f"  Ep{row[0]}: {row[1]}")

    url = rows[0][1]
    if len(sys.argv) > 1:
        url = sys.argv[1]

    print(f"\n=== Playwright test: {url} ===")
    from playwright.async_api import async_playwright

    requests_found = []
    iframes_dom = []

    EMBED_KEYWORDS = (
        ".m3u8", ".mp4", "filemoon", "vidmoly", "sibnet",
        "ok.ru", "mail.ru", "doodstream", "streamtape",
        "speedfiles", "voe.sx", "mixdrop", "upstream",
    )

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="tr-TR",
        )
        page = await ctx.new_page()

        # Stealth mode
        try:
            from playwright_stealth import Stealth
            await Stealth().apply_stealth_async(page)
            print("playwright-stealth aktif")
        except Exception as e:
            print(f"playwright-stealth HATA: {e}")

        def on_req(req):
            u = req.url
            if any(k in u for k in EMBED_KEYWORDS):
                requests_found.append(u)

        page.on("request", on_req)

        print("Sayfaya gidiliyor...")
        try:
            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"goto hatası: {e}")

        title = await page.title()
        print(f"Sayfa başlığı: {title!r}")

        cf_blocked = any(k in title.lower() for k in (
            "just a moment", "attention required", "cloudflare", "checking your"
        ))
        if cf_blocked:
            print("⚠️  CLOUDFLARE CHALLENGE TESPİT EDİLDİ!")

        print("12 saniye bekleniyor...")
        await asyncio.sleep(12)

        title2 = await page.title()
        print(f"Bekleme sonrası başlık: {title2!r}")

        # iframe'leri say
        iframes = await page.query_selector_all("iframe")
        print(f"\niframe sayısı: {len(iframes)}")
        for i, el in enumerate(iframes):
            src = (
                await el.get_attribute("src") or
                await el.get_attribute("data-src") or
                await el.get_attribute("data-lazy-src") or
                "(boş)"
            )
            print(f"  iframe[{i}]: {src[:120]}")
            iframes_dom.append(src)

        # video elementleri
        videos = await page.query_selector_all("video")
        print(f"\nvideo sayısı: {len(videos)}")
        for i, el in enumerate(videos):
            src = await el.get_attribute("src") or await el.get_attribute("data-src") or "(boş)"
            print(f"  video[{i}]: {src[:120]}")

        # JS ile de topla
        try:
            js_srcs = await page.evaluate("""
                () => {
                    const r = [];
                    document.querySelectorAll('iframe, frame').forEach(el => {
                        const s = el.src || el.getAttribute('data-src') || el.getAttribute('data-lazy-src');
                        if (s) r.push('iframe::' + s);
                    });
                    document.querySelectorAll('video, video source').forEach(el => {
                        const s = el.src || el.currentSrc || el.getAttribute('data-src');
                        if (s) r.push('video::' + s);
                    });
                    return [...new Set(r)];
                }
            """)
            print(f"\nJS ile bulunanlar ({len(js_srcs)}):")
            for s in js_srcs:
                print(f"  {s[:120]}")
        except Exception as e:
            print(f"JS eval hatası: {e}")

        print(f"\nNetwork embed istekleri ({len(requests_found)}):")
        for r in requests_found:
            print(f"  {r[:120]}")

        # HTML snippet
        html = await page.content()
        print(f"\nHTML uzunluğu: {len(html)} karakter")
        # İlk 500 karakter (başlık / CF durumu)
        print("HTML baş (500 karakter):")
        print(html[:500])

        await browser.close()

asyncio.run(main())
