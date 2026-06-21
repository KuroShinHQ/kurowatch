"""Tranimaci, ragnarscans, hayalistic kataloglarını çek."""
import asyncio, aiohttp, re, json
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,*/*;q=0.8",
}

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                return await r.text(errors="ignore")
    except:
        pass
    return ""

async def crawl_tranimaci(session):
    """tranimaci.com/anime-listesi — tüm animeleri çek."""
    results = {}
    for page in range(1, 30):
        url = f"https://www.tranimaci.com/anime-listesi?page={page}" if page > 1 else "https://www.tranimaci.com/anime-listesi"
        html = await fetch(session, url)
        if not html:
            break
        # /anime/SLUG/ formatındaki linkler
        links = re.findall(r'href=["\']https?://(?:www\.)?tranimaci\.com/anime/([a-z0-9\-]+)/?["\']', html, re.I)
        # href="/anime/slug/" formatı
        links += re.findall(r'href=["\']/?anime/([a-z0-9\-]+)/?["\']', html, re.I)
        links = list(set(links))
        if not links:
            break
        for slug in links:
            results[slug] = f"https://www.tranimaci.com/anime/{slug}/"
        print(f"  tranimaci page {page}: {len(links)} slug")
        await asyncio.sleep(0.5)
    return results

async def crawl_ragnarscans(session):
    """ragnarscans.com/manga-list — tüm manga/manhwayı çek."""
    results = {}
    for page in range(1, 50):
        url = f"https://ragnarscans.com/manga-list/?page={page}"
        html = await fetch(session, url)
        if not html:
            break
        links = re.findall(r'href=["\']https?://(?:www\.)?ragnarscans\.com/manga/([a-z0-9\-]+)/?["\']', html, re.I)
        links += re.findall(r'href=["\']/?manga/([a-z0-9\-]+)/?["\']', html, re.I)
        links = [l for l in set(links) if l and l != "manga"]
        if not links:
            break
        for slug in links:
            results[slug] = f"https://ragnarscans.com/manga/{slug}/"
        print(f"  ragnarscans page {page}: {len(links)} slug")
        await asyncio.sleep(0.3)
    return results

async def crawl_hayalistic(session):
    """hayalistic.com.tr — manga listesi."""
    results = {}
    for page in range(1, 50):
        url = f"https://hayalistic.com.tr/manga-listesi/?page={page}" if page > 1 else "https://hayalistic.com.tr/manga-listesi/"
        html = await fetch(session, url)
        if not html:
            break
        links = re.findall(r'href=["\']https?://(?:www\.)?hayalistic\.com\.tr/manga/([a-z0-9\-]+)/?["\']', html, re.I)
        links += re.findall(r'href=["\']/?manga/([a-z0-9\-]+)/?["\']', html, re.I)
        links = [l for l in set(links) if l]
        if not links:
            break
        for slug in links:
            results[slug] = f"https://hayalistic.com.tr/manga/{slug}/"
        print(f"  hayalistic page {page}: {len(links)} slug")
        await asyncio.sleep(0.3)
    return results

async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        print("=== tranimaci crawl ===")
        ta = await crawl_tranimaci(session)
        print(f"Toplam: {len(ta)}")

        print("\n=== ragnarscans crawl ===")
        rg = await crawl_ragnarscans(session)
        print(f"Toplam: {len(rg)}")

        print("\n=== hayalistic crawl ===")
        hy = await crawl_hayalistic(session)
        print(f"Toplam: {len(hy)}")

    out = {"tranimaci": ta, "ragnarscans": rg, "hayalistic": hy}
    Path("/mnt/c/Kuroshin/kurowatch/scripts/site_catalogs.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print("\nKaydedildi: site_catalogs.json")

asyncio.run(main())
