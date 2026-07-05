"""Find working manga sites by testing known chapter pages"""
import httpx
import asyncio


async def test_site(name, urls):
    """Test multiple URLs for a site and report"""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for url in urls:
            try:
                r = await client.get(url)
                has_cf = 'cf-browser' in r.text or 'challenge-platform' in r.text
                has_madara = 'wp-manga' in r.text or 'chapter-img' in r.text
                print(f"  {url[:80]}")
                print(f"    HTTP {r.status_code} | {len(r.text)} bytes | CF={'🔴' if has_cf else '✅'} | Madara={'✅' if has_madara else ' '}")
            except Exception as e:
                print(f"  {url[:80]}")
                print(f"    ERROR: {e}")


async def main():
    print("=== MANGA SITE TESTLERİ ===")
    print()
    
    sites = [
        ("mangawow.org (NO CF ✅)", [
            "https://mangawow.org",
            "https://mangawow.org/manga/test/bolum-1/",
        ]),
        ("ragnarscans.com (CF?)", [
            "https://ragnarscans.com",
            "https://ragnarscans.com/manga/test/bolum-1/",
        ]),
        ("mangasehri.net (CF?)", [
            "https://mangasehri.net",
            "https://mangasehri.net/manga/test/bolum-1/",
        ]),
        ("manhwahentai.me (CF?)", [
            "https://manhwahentai.me",
            "https://manhwahentai.me/manhwa/test/chapter-1/",
        ]),
        ("hayalistic.com.tr", [
            "https://hayalistic.com.tr",
            "https://hayalistic.com.tr/manga/test/bolum-1/",
        ]),
        ("merlintoon.com", [
            "https://merlintoon.com",
            "https://merlintoon.com/manga/test/bolum-1/",
        ]),
        ("mangadenizi.com", [
            "https://mangadenizi.com",
            "https://mangadenizi.com/manga/test/bolum-1/",
        ]),
    ]
    
    for name, urls in sites:
        print(f"\n--- {name} ---")
        await test_site(name, urls)

asyncio.run(main())
