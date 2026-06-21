"""Doğru arama URL formatlarını bul."""
import asyncio, aiohttp, re, urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}
TIMEOUT = aiohttp.ClientTimeout(total=12)
TITLE = "Solo Leveling"

async def try_url(session, label, url, find_pattern=None):
    try:
        async with session.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True) as r:
            html = await r.text()
        print(f"[{r.status}] {label}: {url[:80]}")
        if find_pattern and r.status == 200:
            found = re.findall(find_pattern, html)
            print(f"  matches: {found[:3]}")
    except Exception as e:
        print(f"[ERR] {label}: {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        # turkanime.tv arama alternatifleri
        q = urllib.parse.quote(TITLE)
        print("=== turkanime.tv ===")
        await try_url(session, "arama?kelime=", f"https://www.turkanime.tv/arama?kelime={q}")
        await try_url(session, "/?s=", f"https://www.turkanime.tv/?s={q}")
        await try_url(session, "/search/", f"https://www.turkanime.tv/search/{q}")
        await try_url(session, "arama/ (slug)", f"https://www.turkanime.tv/arama/{q.replace('%20','-').lower()}")
        await try_url(session, "wp search", f"https://www.turkanime.tv/?s={q}&post_type=anime",
                      r'href=["\']([^"\']*turkanime\.tv/anime/[^"\']+)["\']')

        print("\n=== mangawow.com slug deneme ===")
        slug = re.sub(r'[^a-z0-9]+', '-', TITLE.lower()).strip('-')
        await try_url(session, "slug direct", f"https://mangawow.com/manga/{slug}/",
                      r'href=["\']([^"\']*mangawow[^"\']*(?:manga|manhwa)[^"\']+)["\']')
        await try_url(session, "search", f"https://mangawow.com/?s={q}&post_type=wp-manga",
                      r'href=["\']([^"\']*(?:manga|manhwa)/[^"\']+)["\']')

        # mangawow.com'da farklı arama: /ajax/search/
        print("\n=== mangawow.com AJAX arama ===")
        try:
            async with session.post(
                "https://mangawow.com/wp-admin/admin-ajax.php",
                data={"action": "wp-manga-search-manga", "title": TITLE},
                headers={**HEADERS, "Referer": "https://mangawow.com/", "X-Requested-With": "XMLHttpRequest"},
                timeout=TIMEOUT
            ) as r:
                text = await r.text()
                print(f"  AJAX [{r.status}]: {text[:200]}")
        except Exception as e:
            print(f"  AJAX HATA: {e}")

asyncio.run(main())
