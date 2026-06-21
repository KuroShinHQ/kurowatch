import asyncio, aiohttp, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.turkanime.tv/",
    "Origin": "https://www.turkanime.tv",
    "Content-Type": "application/x-www-form-urlencoded",
}

SEARCHES = ["attack on titan", "code geass", "bofuri", "danmachi"]

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Önce anasayfaya git (cookie al)
        async with session.get("https://www.turkanime.tv/", headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
            print(f"Ana sayfa: {r.status}, cookies: {len(session.cookie_jar)}")

        for q in SEARCHES:
            data = {"arama": q}
            try:
                async with session.post(
                    "https://www.turkanime.tv/arama",
                    headers=HEADERS,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    txt = await r.text(errors="ignore")
                    links = re.findall(r"turkanime\.tv(/video/[^\"'<>\s]+)", txt)
                    links = list(dict.fromkeys(links))[:5]
                    print(f"[{r.status}] '{q}': {links}")
            except Exception as e:
                print(f"ERR '{q}': {str(e)[:80]}")

asyncio.run(main())
