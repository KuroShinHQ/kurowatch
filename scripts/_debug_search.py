"""Arama fonksiyonlarını direkt test et."""
import asyncio, aiohttp, re, urllib.parse
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
}
TIMEOUT = aiohttp.ClientTimeout(total=12)

async def search_turkanime(session, title):
    search_url = f"https://www.turkanime.tv/arama?kelime={urllib.parse.quote(title)}"
    print(f"  turkanime arama: {search_url[:80]}")
    try:
        async with session.get(search_url, headers=HEADERS, timeout=TIMEOUT) as r:
            html = await r.text()
            print(f"  status={r.status} len={len(html)}")
        links = re.findall(r'href=["\']((https?://www\.turkanime\.tv/anime/[^"\']+))["\']', html)
        print(f"  anime linkleri: {links[:3]}")
        if not links:
            # Genel link ara
            all_links = re.findall(r'href=["\']([^"\']*turkanime[^"\']*)["\']', html)
            print(f"  genel turkanime linkleri: {all_links[:5]}")
        if links:
            anime_url = links[0][0] if isinstance(links[0], tuple) else links[0]
            async with session.get(anime_url, headers=HEADERS, timeout=TIMEOUT) as r2:
                html2 = await r2.text()
            ep_links = re.findall(r'href=["\']([^"\']*turkanime\.tv/video/[^"\']+)["\']', html2)
            print(f"  bölüm linkleri: {ep_links[:2]}")
            if ep_links:
                return ep_links[0]
    except Exception as e:
        print(f"  HATA: {e}")
    return None

async def search_anizm(session, title):
    search_url = f"https://anizm.net/search?q={urllib.parse.quote(title)}"
    print(f"  anizm arama: {search_url[:80]}")
    try:
        async with session.get(search_url, headers={**HEADERS, "Referer": "https://anizm.net/"}, timeout=TIMEOUT) as r:
            html = await r.text()
            print(f"  status={r.status} len={len(html)}")
        links = re.findall(r'href=["\']([^"\']*anizm\.net[^"\']*)["\']', html)
        print(f"  anizm linkleri: {links[:5]}")
    except Exception as e:
        print(f"  HATA: {e}")
    return None

async def search_manga(session, title, base_url):
    search_url = base_url.rstrip("/") + "/?s=" + urllib.parse.quote(title) + "&post_type=wp-manga"
    print(f"  manga arama: {search_url[:80]}")
    try:
        async with session.get(search_url, headers={**HEADERS, "Referer": base_url}, timeout=TIMEOUT) as r:
            html = await r.text()
            print(f"  status={r.status} len={len(html)}")
        domain = re.search(r'https?://(?:www\.)?([^/]+)', base_url).group(1)
        links = re.findall(rf'href=["\']([^"\']*{re.escape(domain)}/(?:manga|manhwa)/[^"\']+)["\']', html, re.IGNORECASE)
        print(f"  manga linkleri: {links[:3]}")
    except Exception as e:
        print(f"  HATA: {e}")
    return None

async def main():
    TEST_ANIME = "Solo Leveling"
    TEST_MANGA = "Solo Leveling"

    async with aiohttp.ClientSession() as session:
        print(f"=== ANİME: '{TEST_ANIME}' ===")
        print("[turkanime.tv]")
        r = await search_turkanime(session, TEST_ANIME)
        print(f"  SONUÇ: {r}")

        print("\n[anizm.net]")
        r = await search_anizm(session, TEST_ANIME)
        print(f"  SONUÇ: {r}")

        print(f"\n=== MANGA: '{TEST_MANGA}' ===")
        for base_url in ["https://mangawow.com/", "https://ragnarscans.net/"]:
            print(f"\n[{base_url}]")
            await search_manga(session, TEST_MANGA, base_url)

asyncio.run(main())
