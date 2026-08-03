"""Find content IDs for test cases."""
import httpx, json

API = "http://localhost:8099"
c = httpx.Client(timeout=15)

queries = [
    ("Naruto", "anime"),
    ("Dexter", "series"),
    ("3 Idiots", "movie"),
    ("Martial Peak", "manga"),
    ("Solo Leveling", "manhwa"),
    ("Cult of the Lamb", "game"),
]

for q, typ in queries:
    r = c.get(f"{API}/api/content", params={"search": q, "type": typ, "limit": 10})
    items = r.json()
    if items:
        for it in items[:3]:
            print(f"  {typ}: #{it['id']} '{it['title']}'")
            # Check episodes
            r2 = c.get(f"{API}/api/content/{it['id']}")
            data = r2.json()
            eps = data.get("episodes", [])
            sites = data.get("sites", [])
            has_url = any(e.get("url") for e in eps[:5])
            print(f"    eps={len(eps)}, sites={len(sites)}, has_urls={has_url}")
    else:
        print(f"  {typ}: '{q}' -> NOT FOUND")

c.close()
