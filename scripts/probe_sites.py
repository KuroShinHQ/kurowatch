"""Her sitenin ilk sayfasından link örüntüsünü öğren."""
import asyncio, aiohttp, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,*/*",
}

URLS = [
    ("tranimaci", "https://www.tranimaci.com/anime-listesi"),
    ("tranimaci2", "https://www.tranimaci.com/"),
    ("ragnarscans", "https://ragnarscans.com/manga-list/"),
    ("ragnarscans2", "https://ragnarscans.com/"),
    ("hayalistic", "https://hayalistic.com.tr/manga-listesi/"),
    ("hayalistic2", "https://hayalistic.com.tr/"),
]

async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as s:
        for name, url in URLS:
            try:
                async with s.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=12)) as r:
                    html = await r.text(errors="ignore")
                    # Tüm href'leri çek
                    hrefs = re.findall(r'href=["\']([^"\']{5,80})["\']', html)
                    # İçerik linklerine benzeyen (anime|manga|series|chapter)
                    content = [h for h in hrefs if re.search(r'/(anime|manga|series|dizi|chapter|bol[üu]m)/', h, re.I)][:8]
                    print(f"\n[{name}] {r.status} len={len(html)}")
                    print(f"  İçerik linkleri örn: {content[:5]}")
                    # Genel link örüntüsü
                    patterns = {}
                    for h in hrefs:
                        m = re.match(r'https?://[^/]+(/[^/]+/)', h)
                        if m:
                            p = m.group(1)
                            patterns[p] = patterns.get(p, 0) + 1
                    top = sorted(patterns.items(), key=lambda x: -x[1])[:5]
                    print(f"  En çok href prefix: {top}")
            except Exception as e:
                print(f"[{name}] HATA: {e}")

asyncio.run(main())
