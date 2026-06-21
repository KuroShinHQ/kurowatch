"""turkanime.tv'nin tüm anime slug'larını çıkar."""
import aiohttp, asyncio, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,*/*;q=0.8",
}

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Sitemap içeriğine bak
        async with session.get("https://www.turkanime.tv/sitemap.xml", headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
            xml = await r.text(errors="ignore")
            print("Sitemap.xml içeriği:")
            print(xml[:1000])
            print()

        # anime-izle sayfalama var mı?
        for page in (1, 2, 3):
            url = f"https://www.turkanime.tv/anime-izle?sayfa={page}"
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    txt = await r.text(errors="ignore")
                    slugs = list(dict.fromkeys(re.findall(r"/anime/([a-z0-9-]+)", txt)))
                    # Alternatif: /video/slug formatı
                    v_slugs = list(dict.fromkeys(re.findall(r"/video/([a-z0-9-]+)-\d+-bolum", txt)))
                    print(f"Sayfa {page} [{r.status}]: anime_slugs={len(slugs)} video_slugs={len(v_slugs)}")
                    if v_slugs:
                        print(f"  Örnekler: {v_slugs[:5]}")
            except Exception as e:
                print(f"Sayfa {page} ERR: {str(e)[:60]}")

        # Harf bazlı liste var mı?
        for harf in ("a", "b", "s", "t"):
            url = f"https://www.turkanime.tv/anime-izle?harf={harf}"
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    txt = await r.text(errors="ignore")
                    v_slugs = list(dict.fromkeys(re.findall(r"/video/([a-z0-9-]+)-\d+-bolum", txt)))
                    print(f"Harf '{harf}' [{r.status}]: {len(v_slugs)} slug")
                    if v_slugs:
                        print(f"  Örnekler: {v_slugs[:5]}")
            except Exception as e:
                print(f"Harf '{harf}' ERR: {str(e)[:60]}")

asyncio.run(main())
