import aiohttp, asyncio, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
}

URLS = [
    "https://www.turkanime.tv/sitemap.xml",
    "https://www.turkanime.tv/sitemap_index.xml",
    "https://www.turkanime.tv/anime-listesi",
    "https://www.turkanime.tv/anime-izle",
    "https://www.turkanime.tv/ajax/gelismis",
    "https://www.turkanime.tv/liste",
]

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for url in URLS:
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    txt = await r.text(errors="ignore")
                    slug_pat = re.compile(r"turkanime\.tv/(?:video|anime)/([a-z0-9-]+)")
                    slugs = slug_pat.findall(txt)
                    print(f"[{r.status}] {url}")
                    print(f"  len={len(txt)} slugs={len(slugs)}")
                    if slugs:
                        print(f"  ornekler: {slugs[:5]}")
            except Exception as e:
                print(f"ERR {url}: {str(e)[:60]}")

asyncio.run(main())
