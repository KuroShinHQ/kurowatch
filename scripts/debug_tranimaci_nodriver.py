"""nodriver hızlı CF bypass testi - sadece sayfa title kontrolü"""
import asyncio
import nodriver as uc

TEST_URL = "https://tranimaci.com/video/kono-subarashii-sekai-ni-shukufuku-wo-3-1-bolum"
CHROMIUM_BIN = "/usr/bin/chromium-browser"

async def test():
    browser = None
    try:
        print("[1] nodriver başlıyor...")
        browser = await uc.start(
            headless=True,
            browser_executable_path=CHROMIUM_BIN,
            no_sandbox=True,
        )
        print("[2] Goto...")
        tab = await browser.get(TEST_URL)
        print("[3] 15sn bekle...")
        await asyncio.sleep(15)
        title = await tab.evaluate("document.title")
        print("[TITLE]", title)

        # Sayfa HTML'ini al
        html = await tab.get_content()
        print("[HTML len]", len(html))
        # İlk 500 karakteri bas
        print("[HTML preview]", html[:300])

        # iframe ara
        import re
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
        mp4s = re.findall(r'"(https?://[^"]+\.mp4[^"]*)"', html)
        m3u8s = re.findall(r'"(https?://[^"]+\.m3u8[^"]*)"', html)
        print("[IFRAMES]", iframes[:5])
        print("[MP4s]", mp4s[:5])
        print("[M3U8s]", m3u8s[:5])

    except Exception as e:
        print("[HATA]", e)
        import traceback; traceback.print_exc()
    finally:
        if browser:
            try: browser.stop()
            except: pass

asyncio.run(test())
