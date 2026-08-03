"""Deep test of 720pizle and asurascans"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
        iframes = len(re.findall(r'<iframe', r.text))
        embeds = len(re.findall(r'embed', r.text.lower()))
        return {"label": label, "status": r.status_code, "size": len(r.text), "ok": r.status_code == 200 and len(r.text) > 5000, "iframes": iframes, "embeds": embeds, "text": r.text[:500]}
    except Exception as e:
        return {"label": label, "ok": False, "error": str(e)[:60]}

async def main():
    async with httpx.AsyncClient(timeout=15) as cl:
        print("=== 720PIZLE DETAILED ===")
        tests = [
            ("https://720pizle.com/", "homepage"),
            ("https://720pizle.com/film/3-idiots-izle/", "film/3-idiots-izle"),
            ("https://720pizle.com/film/3-idiots-2009-izle/", "film/3-idiots-2009-izle"),
            ("https://720pizle.com/film/3-aptal-izle/", "film/3-aptal-izle"),
            ("https://720pizle.com/film/3-aptal-2009-izle/", "film/3-aptal-2009-izle"),
            ("https://720pizle.com/film/fight-club-izle/", "film/fight-club-izle"),
            ("https://720pizle.com/film/the-godfather-izle/", "film/the-godfather-izle"),
            ("https://720pizle.com/film/esaretin-bedeli-izle/", "film/esaretin-bedeli-izle"),
            ("https://720pizle.com/3-idiots-izle/", "no /film/ prefix"),
            ("https://720pizle.com/film/3-idiots/", "film/3-idiots no -izle"),
        ]
        for url, label in tests:
            r = await check(cl, url, label)
            t = "✅" if r.get("ok") else "❌"
            print(f"  {t} {label:50s} HTTP {r.get('status')} ({r.get('size')}B) iframes:{r.get('iframes',0)}")

        print("\n=== ASURASCANS DETAILED ===")
        tests = [
            ("https://asurascans.com.tr/", "homepage"),
            ("https://asurascans.com.tr/manga/", "manga list"),
            ("https://asurascans.com.tr/manga/omniscient-reader/", "manga page"),
            ("https://asurascans.com.tr/manga/omniscient-reader/bolum-1/", "chapter page"),
        ]
        for url, label in tests:
            r = await check(cl, url, label)
            t = "✅" if r.get("ok") else "❌"
            print(f"  {t} {label:50s} HTTP {r.get('status')} ({r.get('size')}B)")

        print("\n=== MONOMANGA SLUG TEST ===")
        slugs = ["return-to-player", "bug-player", "solo-leveling", "martial-peak",
                 "omniscient-reader", "tower-of-god", "nano-machine", "solo-leveling-webtoon"]
        for slug in slugs:
            r = await check(cl, f"https://monomanga.com.tr/manga/{slug}/", f"slug: {slug}")
            t = "✅" if r.get("ok") else "❌"
            print(f"  {t} /manga/{slug}/: HTTP {r.get('status')} ({r.get('size')}B)")

        print("\n=== 720PIZLE MOVIE RANDOM ===")
        test_movies = ["the-dark-knight", "inception", "interstellar", "pulp-fiction",
                       "titanic", "avatar", "the-matrix", "forrest-gump", "the-shawshank-redemption",
                       "esaretin-bedeli", "yesil-yol", "fight-club", "dovus-kulubu"]
        for slug in test_movies:
            # Try multiple patterns
            for pattern in [f"/film/{slug}-izle/", f"/{slug}-izle/"]:
                r = await check(cl, f"https://720pizle.com{pattern}", f"{pattern}")
                if r.get("ok"):
                    print(f"  ✅ https://720pizle.com{pattern} -> HTTP {r['status']} ({r['size']}B)")
                    break
            else:
                print(f"  ❌ {slug}: no pattern worked")

if __name__ == "__main__":
    asyncio.run(main())
