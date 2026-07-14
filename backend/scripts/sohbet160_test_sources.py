"""SOHBET-160: Test Turkish manga/manhwa + movie sources"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        has_content = len(r.text) > 5000
        has_manga = 'manga' in r.text.lower() or 'chapter' in r.text.lower() or 'bolum' in r.text.lower()
        has_iframe = '<iframe' in r.text or 'embed' in r.text.lower()
        return {"label": label, "status": r.status_code, "size": len(r.text), "ok": r.status_code == 200 and has_content, "manga": has_manga, "iframe": has_iframe}
    except Exception as e:
        return {"label": label, "status": None, "size": 0, "ok": False, "error": str(e)[:60]}

async def main():
    async with httpx.AsyncClient(timeout=15) as cl:
        manga_sites = [
            ("https://monomanga.com.tr/", "monomanga homepage"),
            ("https://monomanga.com.tr/manga/return-to-player/", "monomanga manga page"),
            ("https://www.mangawow.org/", "mangawow homepage"),
            ("https://www.mangawow.org/manga/the-hunter/", "mangawow manga page"),
            ("https://www.ruyamanga2.com/", "ruyamanga2 homepage"),
            ("https://www.ruyamanga2.com/manga/omniscient-reader/", "ruyamanga2 manga"),
            ("https://www.ruyamanga.net/", "ruyamanga homepage (CF)"),
            ("https://manga-tr.com/", "manga-tr.com"),
            ("https://www.mangaoku.com.tr/", "mangaoku"),
            ("https://golgebahcesi.com/", "golgebahcesi homepage"),
            ("https://golgebahcesi.com/manga/solo-leveling/", "golgebahcesi manga"),
            ("https://www.majorscans.com/", "majorscans"),
            ("https://www.majorscans.com/manga/reincarnation-of-the-fist-king/", "majorscans manga"),
            ("https://asurascans.com.tr/", "asurascans (CF)"),
            ("https://www.tranimeizle.org.tr/", "tranimeizle (check manga cat)"),
            ("https://www.tranimeizle.org.tr/?s=naruto+manga", "tranimeizle manga search"),
        ]

        movie_sites = [
            ("https://www.hdfilmcehennemi.sh/", "hdfc.sh homepage"),
            ("https://www.hdfilmcehennemi.net/", "hdfc.net homepage"),
            ("https://www.hdfilmcehennemi.sh/american-psycho/", "hdfc.sh movie page"),
            ("https://www.hdfilmcehennemi.net/american-psycho/", "hdfc.net movie page"),
            ("https://www.fullhdfilmizlesene.pw/", "fullhdfilmizlesene"),
            ("https://www.fullhdfilmizlesene.pw/film/3-idiots-izle/", "fullhd 3idiots"),
            ("https://www.fullhdfilmizlesene.pw/film/3-aptal-izle/", "fullhd 3aptal"),
            ("https://720pizle.com/", "720pizle"),
            ("https://720pizle.com/film/3-idiots-izle/", "720pizle 3idiots"),
            ("https://www.hdfilmcehennemi.nl/film/3-idiots-izle/", "hdfc.nl 3idiots alt"),
            ("https://www.hdfilmcehennemi.nl/film/3-idiots-izle-2/", "hdfc.nl 3idiots-2"),
            ("https://dizimag.com.tr/film/", "dizimag film"),
            ("https://www.hdfilmcehennemi.io/", "hdfc.io homepage"),
            ("https://www.hdfilmcehennemi.io/film/", "hdfc.io/film/"),
        ]

        print("=== MANGA/MANHWA SITES ===")
        for url, label in manga_sites:
            r = await check(cl, url, label)
            icon = "✅" if r["ok"] else "❌"
            print(f"  {icon} {label:45s} HTTP {r['status']} ({r['size']}B) manga:{r.get('manga','?')}")

        print("\n=== MOVIE SITES ===")
        for url, label in movie_sites:
            r = await check(cl, url, label)
            icon = "✅" if r["ok"] else "❌"
            print(f"  {icon} {label:45s} HTTP {r['status']} ({r['size']}B) iframe:{r.get('iframe','?')}")

if __name__ == "__main__":
    asyncio.run(main())
