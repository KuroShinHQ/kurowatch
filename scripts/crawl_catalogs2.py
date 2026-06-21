"""Doğru domainlerden katalog çek."""
import asyncio, aiohttp, re, json
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,*/*",
}

async def fetch(session, url):
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as r:
            if r.status == 200:
                return await r.text(errors="ignore")
    except:
        pass
    return ""

async def crawl_ragnarscans(session):
    results = {}
    # Önce ana sayfa (264 manga link)
    html = await fetch(session, "https://ragnarscans.net/")
    slugs = re.findall(r'ragnarscans\.net/manga/([a-z0-9\-]+)/?["\'\s<]', html)
    for s in set(slugs):
        if s:
            results[s] = f"https://ragnarscans.net/manga/{s}/"
    print(f"  Ana sayfa: {len(results)} slug")

    # Sayfalı liste
    for page in range(1, 20):
        url = f"https://ragnarscans.net/manga-listesi/?page={page}"
        html = await fetch(session, url)
        if not html:
            url2 = f"https://ragnarscans.net/?page={page}"
            html = await fetch(session, url2)
        if not html:
            break
        slugs = re.findall(r'ragnarscans\.net/manga/([a-z0-9\-]+)/?["\'\s<]', html)
        new = [s for s in set(slugs) if s and s not in results]
        if not new:
            break
        for s in new:
            results[s] = f"https://ragnarscans.net/manga/{s}/"
        print(f"  Sayfa {page}: +{len(new)} slug")
        await asyncio.sleep(0.3)

    # /genre/ sayfaları
    genres_html = await fetch(session, "https://ragnarscans.net/genre/manhwa/")
    slugs = re.findall(r'ragnarscans\.net/manga/([a-z0-9\-]+)/?["\'\s<]', genres_html)
    for s in set(slugs):
        if s and s not in results:
            results[s] = f"https://ragnarscans.net/manga/{s}/"

    return results

async def crawl_hayalistic(session):
    results = {}
    html = await fetch(session, "https://hayalistic.blog/")
    slugs = re.findall(r'hayalistic\.blog/manga/([a-z0-9\-]+)/?(?:bolum|chapter|["\'\s<])', html)
    slugs += re.findall(r'hayalistic\.blog/manga/([a-z0-9\-]+)/?"', html)
    for s in set(slugs):
        if s:
            results[s] = f"https://hayalistic.blog/manga/{s}/"
    print(f"  Ana sayfa: {len(results)} slug")

    for page in range(2, 30):
        url = f"https://hayalistic.blog/page/{page}/"
        html = await fetch(session, url)
        if not html:
            break
        slugs = re.findall(r'hayalistic\.blog/manga/([a-z0-9\-]+)/?["\'\s<]', html)
        new = [s for s in set(slugs) if s and s not in results]
        if not new:
            break
        for s in new:
            results[s] = f"https://hayalistic.blog/manga/{s}/"
        print(f"  Sayfa {page}: +{len(new)} slug")
        await asyncio.sleep(0.3)

    return results

async def probe_tranimaci(session):
    """tranimaci HTML yapısını anla."""
    html = await fetch(session, "https://www.tranimaci.com/")
    print(f"  tranimaci ana: {len(html)} chars")
    # Tüm linklere bak
    hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
    anime_like = [h for h in hrefs if re.search(r'tranimaci', h, re.I)][:10]
    print(f"  tranimaci linkler: {anime_like[:5]}")
    all_paths = [h for h in hrefs if h.startswith('/')][:20]
    print(f"  / ile başlayan: {all_paths}")
    return {}

async def main():
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        print("=== tranimaci probe ===")
        await probe_tranimaci(session)

        print("\n=== ragnarscans.net ===")
        rg = await crawl_ragnarscans(session)
        print(f"TOPLAM: {len(rg)}")

        print("\n=== hayalistic.blog ===")
        hy = await crawl_hayalistic(session)
        print(f"TOPLAM: {len(hy)}")

    out = {"ragnarscans": rg, "hayalistic": hy}
    Path("/mnt/c/Kuroshin/kurowatch/scripts/site_catalogs.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )
    print("\nKaydedildi: site_catalogs.json")

asyncio.run(main())
