"""SOHBET-158: Check search endpoints on tranimeizle and hdfilmcehennemi"""
import asyncio, httpx

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text)
    except Exception as e:
        return label, None, str(e)[:50]

async def main():
    async with httpx.AsyncClient(timeout=15) as cl:
        results = []

        # === TRANIMEIZLE SEARCH ===
        print("=== TRANIMEIZLE SEARCH ===")
        tests = [
            ("/?s=naruto", "search naruto"),
            ("/?search=naruto", "search param naruto"),
            ("/arama/naruto/", "arama/naruto"),
            ("/search/naruto/", "search/naruto"),
            ("/search?q=naruto", "search?q=naruto"),
            ("/api/search?q=naruto", "api/search"),
            ("/anime/?s=naruto", "anime/?s=naruto"),
            ("/animelist", "animelist"),
            ("/animelist/", "animelist with slash"),
            ("/list/", "list page"),
        ]
        for path, label in tests:
            label, status, size = await check(cl, f"https://tranimeizle.org.tr{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("tranimeizle", path, label, status, size))

        # Check a few anime slugs from our DB to see if they exist
        print("\n=== TRANIMEIZLE ANIME SLUG TEST ===")
        slug_tests = [
            "naruto", "one-piece", "attack-on-titan", "death-note", "bleach",
            "fullmetal-alchemist", "sword-art-online", "tokyo-ghoul", "code-geass",
            "steins-gate", "hunter-x-hunter", "dragon-ball", "demon-slayer",
            "my-hero-academia", "one-punch-man", "cowboy-bebop", "evangelion",
            "spy-x-family", "jujutsu-kaisen", "chainsaw-man",
            "akame-ga-kill", "another", "arifureta", "assassination-classroom",
            "overlord", "re-zero", "konosuba", "solo-leveling",
        ]
        for slug in slug_tests:
            label, status, size = await check(cl, f"https://tranimeizle.org.tr/{slug}/", f"slug: {slug}")
            print(f"  /{slug}/: HTTP {status} ({size}B)")
            results.append(("tranimeizle_slug", f"/{slug}/", slug, status, size))
            await asyncio.sleep(0.2)

        # === HDFILMCEHENNEMI.IO SEARCH ===
        print("\n=== HDFILMCEHENNEMI.IO SEARCH ===")
        h_tests = [
            ("/?s=3+idiots", "search 3 idiots"),
            ("/?s=fight+club", "search fight club"),
            ("/search/3+idiots/", "search/"),
            ("/arama/3+idiots/", "arama/"),
            ("/search?keyword=3+idiots", "search kw"),
            ("/film-ara?q=3+idiots", "film-ara"),
            ("/filmler/", "film list"),
            ("/movie/3-idiots/", "movie/"),
            ("/film/3-idiots/", "film/"),
        ]
        for path, label in h_tests:
            label, status, size = await check(cl, f"https://www.hdfilmcehennemi.io{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("hdfc.io", path, label, status, size))

        # Try generic movie slugs that might work
        print("\n=== HDFILMCEHENNEMI.IO KNOWN MOVIE SLUGS ===")
        known = ["3-idiots", "3-aptal", "3-idiots-2009", "the-godfather", "fight-club",
                  "pulp-fiction", "inception", "the-dark-knight", "interstellar",
                  "titanic", "avatar", "the-matrix", "forrest-gump", "the-shawshank-redemption",
                  "esaretin-bedeli", "yeşil-yol", "yesil-yol", "başlangıç", "baslangic"]
        for slug in known:
            label, status, size = await check(cl, f"https://www.hdfilmcehennemi.io/{slug}/", f"slug: {slug}")
            print(f"  /{slug}/: HTTP {status} ({size}B)")
            results.append(("hdfc.io_slug", f"/{slug}/", slug, status, size))
            await asyncio.sleep(0.2)

        # === DIZIMAG EPISODE PATTERN ===
        print("\n=== DIZIMAG EPISODE PATTERNS ===")
        d_tests = [
            ("/dizi/breaking-bad/1-sezon-1-bolum-izle/", "1-sezon-1-bolum-izle"),
            ("/breaking-bad-1-sezon-1-bolum-izle/", "no dizi prefix"),
            ("/dizi/breaking-bad/bolum/1/", "bolum/1"),
            ("/dizi/breaking-bad/1/", "/1/"),
            ("/bolum/breaking-bad-1-sezon-1-bolum/", "bolum prefix"),
            ("/dizi/breaking-bad/sezon/1/bolum/1/", "sezon/bolum"),
            ("/dizi/breaking-bad/1-sezon/1-bolum/", "1-sezon/1-bolum"),
        ]
        for path, label in d_tests:
            label, status, size = await check(cl, f"https://www.dizimag.com.tr{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("dizimag", path, label, status, size))

        print("\n\n=== WORKING PATTERNS ===")
        for site, path, label, status, size in results:
            if status == 200 and (isinstance(size, int) and size > 5000):
                print(f"  ✅ {site:20s} {path:50s} ({size//1000}KB)")

if __name__ == "__main__":
    asyncio.run(main())
