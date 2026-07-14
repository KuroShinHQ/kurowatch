"""SOHBET-158: Discover URL patterns for alternative sites"""
import asyncio, httpx, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text), r.text[:200] if r.status_code == 200 else r.text[:100]
    except Exception as e:
        return label, None, 0, str(e)[:100]

async def main():
    async with httpx.AsyncClient(timeout=15) as cl:
        results = []

        # === TRANIMEIZLE.ORG.TR PATTERNS ===
        print("=== TRANIMEIZLE.ORG.TR ===")
        tests = [
            ("/", "homepage"),
            ("/anime/", "anime listing"),
            ("/anime-list/", "anime list page"),
            ("/anime/naruto/", "anime detail (naruto)"),
            ("/naruto-1-bolum-izle", "naruto ep1 with -bolum-izle"),
            ("/naruto-izle/", "naruto izle page"),
            ("/naruto/", "just naruto"),
            ("/solo-leveling-izle/", "solo leveling izle"),
            ("/solo-leveling/", "solo leveling"),
            ("/attack-on-titan-1-bolum-izle", "aot ep1 izle"),
            ("/shingeki-no-kyojin-1-bolum-izle", "aot jp name ep1"),
        ]
        for path, label in tests:
            label, status, size, snippet = await check(cl, f"https://tranimeizle.org.tr{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("tranimeizle", path, label, status, size))

        # === DIZIMAG.COM.TR PATTERNS ===
        print("\n=== DIZIMAG.COM.TR ===")
        d_tests = [
            ("/dizi/breaking-bad/", "dizi/breaking-bad"),
            ("/dizi/breaking-bad/1-sezon/1-bolum/", "ep specific"),
            ("/dizi/breaking-bad-izle/", "dizi/breaking-bad-izle"),
            ("/diziler/breaking-bad/", "diziler/breaking-bad"),
            ("/diziler/breaking-bad-izle/", "diziler/breaking-bad-izle"),
            ("/breaking-bad-izle/", "breaking-bad-izle"),
            ("/breaking-bad/1-sezon-1-bolum-izle/", "breaking-bad ep izle"),
            ("/breaking-bad/1-sezon/1-bolum/", "season/ep format"),
            ("/dexter-1-sezon-1-bolum/", "dexter ep short"),
            ("/dizi/dexter/", "dizi/dexter"),
        ]
        for path, label in d_tests:
            label, status, size, snippet = await check(cl, f"https://www.dizimag.com.tr{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("dizimag", path, label, status, size))

        # === HDFILMCEHENNEMI.IO PATTERNS ===
        print("\n=== HDFILMCEHENNEMI.IO ===")
        h_tests = [
            ("/", "homepage"),
            ("/film/3-aptal/", "film/3-aptal"),
            ("/film/3-idiots-2009-izle/", "film/3-idiots-2009-izle"),
            ("/film/3-idiots-izle/", "film/3-idiots-izle"),
            ("/3-idiots/", "3-idiots"),
            ("/film/3-idiots/", "film/3-idiots"),
            ("/film/3-aptal-2009-izle/", "film/3-aptal-2009-izle"),
            ("/film/3-aptal-izle/", "film/3-aptal-izle"),
            ("/3-aptal-izle/", "3-aptal-izle"),
            ("/dovus-kulubu-1999-izle/", "dovus-kulubu-1999-izle"),
            ("/fight-club-izle/", "fight-club-izle"),
            ("/film/dovus-kulubu/", "film/dovus-kulubu"),
        ]
        for path, label in h_tests:
            label, status, size, snippet = await check(cl, f"https://www.hdfilmcehennemi.io{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("hdfc.io", path, label, status, size))

        # === HDFILMCEHENNEMI.SH PATTERNS ===
        print("\n=== HDFILMCEHENNEMI.SH ===")
        sh_tests = [
            ("/", "homepage"),
            ("/american-psycho/", "american-psycho"),
            ("/film/3-aptal/", "film/3-aptal"),
            ("/3-aptal/", "3-aptal"),
        ]
        for path, label in sh_tests:
            label, status, size, snippet = await check(cl, f"https://www.hdfilmcehennemi.sh{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("hdfc.sh", path, label, status, size))

        # === HDFILMCEHENNEMI.NET PATTERNS ===
        print("\n=== HDFILMCEHENNEMI.NET ===")
        for path, label in [
            ("/", "homepage"),
            ("/american-psycho/", "american-psycho"),
            ("/film/3-aptal/", "film/3-aptal"),
        ]:
            label, status, size, snippet = await check(cl, f"https://www.hdfilmcehennemi.net{path}", label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("hdfc.net", path, label, status, size))

        # === TR ANIME SITES TO CHECK ===
        print("\n=== OTHER ANIME SITES ===")
        sites = [
            ("https://openani.me/", "OpenAnime"),
            ("https://www.aniturk.co/", "AniTurk"),
            ("https://www.tranimeizle.org.tr/naruto-bolum-1/", "naruto-bolum-1"),
            ("https://www.tranimeizle.org.tr/naruto-1/", "naruto-1"),
            ("https://www.tranimeizle.org.tr/anime/naruto-1-bolum-izle/", "anime/naruto-1-bolum-izle"),
        ]
        for url, label in sites:
            label2, status, size, snippet = await check(cl, url, label)
            print(f"  {label:45s} HTTP {status} ({size}B)")
            results.append(("other", url, label, status, size))

        # Print summary
        print("\n\n=== WORKING PATTERNS ===")
        for site, path, label, status, size in results:
            if status == 200 and size > 5000:
                print(f"  ✅ {site:15s} {path:50s} ({size//1000}KB)")

if __name__ == "__main__":
    asyncio.run(main())
