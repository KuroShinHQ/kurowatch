"""SOHBET-157: Test MangaDex download pipeline for Martial Peak"""
import asyncio, httpx, os

DOWNLOAD_DIR = '/mnt/c/Kuroshin/kurowatch/temp/sohbet157_test'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def test():
    MANGADEX_API = "https://api.mangadex.org"
    UUID = "b1461071-bfbb-43e7-a5b6-a7ba5904649f"

    print("=== TEST 1: MangaDex API Search ===")
    async with httpx.AsyncClient(timeout=15) as cl:
        r = await cl.get(f"{MANGADEX_API}/manga/{UUID}")
        if r.status_code == 200:
            title = r.json()['data']['attributes']['title'].get('en', 'unknown')
            print(f"  Manga: {title}")
        else:
            print(f"  ERROR: {r.status_code}")
            return

    print("\n=== TEST 2: Latest Chapter ===")
    async with httpx.AsyncClient(timeout=15) as cl:
        r = await cl.get(f"{MANGADEX_API}/manga/{UUID}/feed",
            params={"translatedLanguage[]": "en", "limit": 5, "order[chapter]": "desc"})
        if r.status_code == 200:
            chapters = r.json()['data']
            for ch in chapters[:3]:
                a = ch['attributes']
                print(f"  Ch. {a['chapter']}: {a.get('title', '')}")
            latest_id = chapters[0]['id']
            latest_ch = chapters[0]['attributes']['chapter']
        else:
            print(f"  ERROR: {r.status_code}")
            return

    print(f"\n=== TEST 3: Download Chapter {latest_ch} ===")
    async with httpx.AsyncClient(timeout=15) as cl:
        r = await cl.get(f"{MANGADEX_API}/at-home/server/{latest_id}")
        if r.status_code == 200:
            data = r.json()
            base_url = data['baseUrl']
            ch_hash = data['chapter']['hash']
            pages = data['chapter']['data']
            print(f"  Pages: {len(pages)}")

            page_url = f"{base_url}/data/{ch_hash}/{pages[0]}"
            r2 = await cl.get(page_url)
            if r2.status_code == 200:
                fpath = os.path.join(DOWNLOAD_DIR, f"martial_peak_ch{latest_ch}_page1.jpg")
                with open(fpath, 'wb') as f:
                    f.write(r2.content)
                print(f"  Downloaded: {len(r2.content)} bytes -> {fpath}")
                print(f"  VERIFIED: MangaDex pipeline works!")
            else:
                print(f"  Page download failed: HTTP {r2.status_code}")

if __name__ == "__main__":
    asyncio.run(test())
