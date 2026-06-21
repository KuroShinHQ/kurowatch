import asyncio, aiohttp, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.turkanime.tv/",
}

SEARCHES = ["attack on titan", "bofuri", "code geass", "assassination classroom", "danmachi", "classroom of the elite"]

async def main():
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        for q in SEARCHES:
            url = "https://www.turkanime.tv/ara?kelime=" + q.replace(" ", "+")
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=10)) as r:
                    txt = await r.text(errors="ignore")
                    links = re.findall(r'href=["\']https://www\.turkanime\.tv(/video/[^"\'?#]+)["\']', txt)
                    links = list(dict.fromkeys(links))[:5]
                    print(f"[{r.status}] {q}: {links}")
            except Exception as e:
                print(f"ERR {q}: {str(e)[:80]}")

asyncio.run(main())
