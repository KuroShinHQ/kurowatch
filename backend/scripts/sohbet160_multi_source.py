"""Simplified multi-source test with better error handling"""
import asyncio, httpx, re

TEST_FILMS = [
    ("Esaretin Bedeli", "esaretin-bedeli"),
    ("Fight Club", "fight-club"),
    ("Inception", "inception"),
    ("Avatar", "avatar"),
    ("Interstellar", "interstellar"),
    ("The Matrix", "the-matrix"),
]

SOURCES = {
    "hdfc3": lambda s: f"https://www.hdfilmcehennemi3.com/{s}/",
    "dizimag": lambda s: f"https://dizimag.com.tr/film/{s}-izle/",
    "diziyou": lambda s: f"https://www.diziyou.com/{s}/",
    "turkish123": lambda s: f"https://www.turkish123.com/{s}/",
    "hdfc.mov": lambda s: f"https://www.hdfilmcehennemi.mov/{s}/",
}

async def test_one(client, name, url_fn):
    results = []
    for title, slug in TEST_FILMS:
        try:
            url = url_fn(slug)
            r = await client.get(url, timeout=10, follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9',
                         'Referer': 'https://google.com'})
            is_ok = r.status_code == 200 and len(r.text) > 5000
            res = "OK" if is_ok else f"FAIL({r.status_code},{len(r.text)})"
            results.append(f"  {title:30s} -> {res}")
        except Exception as e:
            results.append(f"  {title:30s} -> ERROR({str(e)[:30]})")
    return name, results

async def main():
    print("Testing movie sources...\n")
    async with httpx.AsyncClient(timeout=10, limits=httpx.Limits(max_keepalive_connections=3, max_connections=3)) as cl:
        for name, url_fn in SOURCES.items():
            print(f"\n{'='*50}")
            print(f"SOURCE: {name}")
            print(f"{'='*50}")
            n, results = await test_one(cl, name, url_fn)
            for r in results:
                print(r)
            await asyncio.sleep(0.3)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"FATAL: {e}")
