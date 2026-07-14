"""Explore hdfilmcehennemi catalog"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text), r.text[:2000]
    except Exception as e:
        return label, None, 0, str(e)[:100]

async def main():
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as cl:
        urls = [
            ("https://www.hdfilmcehennemi.sh/sitemap.xml", "sitemap.xml"),
            ("https://www.hdfilmcehennemi.sh/sitemap_index.xml", "sitemap_index"),
            ("https://www.hdfilmcehennemi.sh/", "homepage"),
            ("https://www.hdfilmcehennemi.sh/category/film-izle-2/", "film category"),
            ("https://www.hdfilmcehennemi.sh/category/1080p-hd-film-izle-2/", "hd film category"),
            ("https://www.hdfilmcehennemi.sh/film-robotu-1/", "film robotu/search"),
            # Known working movies
            ("https://www.hdfilmcehennemi.sh/american-psycho/", "american-psycho (known)"),
            ("https://www.hdfilmcehennemi.sh/shark-tale/", "shark-tale (known)"),
            ("https://www.hdfilmcehennemi.sh/wall-e/", "wall-e (known)"),
            ("https://www.hdfilmcehennemi.sh/planet-of-the-apes/", "planet-of-the-apes (known)"),
            ("https://www.hdfilmcehennemi.sh/the-collector/", "the-collector (known)"),
            ("https://www.hdfilmcehennemi.sh/howls-moving-castle/", "howls-moving-castle"),
            # Try more movies on hdfc.sh
            ("https://www.hdfilmcehennemi.sh/3-idiots/", "3-idiots"),
            ("https://www.hdfilmcehennemi.sh/300/", "300"),
            ("https://www.hdfilmcehennemi.sh/avatar/", "avatar"),
            ("https://www.hdfilmcehennemi.sh/titanic/", "titanic"),
            ("https://www.hdfilmcehennemi.sh/inception/", "inception"),
            ("https://www.hdfilmcehennemi.sh/esaretin-bedeli/", "esaretin-bedeli"),
        ]
        
        for url, label in urls:
            lbl, status, size, text = await check(cl, url, label)
            has_iframe = '<iframe' in text
            has_player = 'player' in text.lower() or 'video' in text.lower()
            icon = "✅" if (status == 200 and size > 10000) else "❌"
            print(f"  {icon} {label:45s} HTTP {status} ({size}B) iframe={has_iframe} player={has_player}")
            await asyncio.sleep(0.5)
            
            # If sitemap found, parse for movie URLs
            if 'sitemap' in label and status == 200:
                urls_found = re.findall(r'<loc>([^<]+)</loc>', text)
                print(f"    URLs in {label}: {len(urls_found)}")
                for u in urls_found[:30]:
                    print(f"      {u}")

if __name__ == "__main__":
    asyncio.run(main())
