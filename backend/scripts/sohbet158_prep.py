"""SOHBET-158: Check DB content titles and cartoon availability"""
import asyncio, httpx, sqlite3, re

async def check(client, url, label):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
        return label, r.status_code, len(r.text), r.status_code == 200 and len(r.text) > 5000
    except:
        return label, None, 0, False

async def main():
    db = sqlite3.connect('memory/kurowatch.db')
    cur = db.cursor()

    # Sample anime titles
    cur.execute("SELECT id, title, title_tr, external_id FROM content WHERE type='anime' ORDER BY id LIMIT 30")
    print("=== SAMPLE ANIME TITLES ===")
    for r in cur.fetchall():
        print(f"  ID={r[0]:3d} ext={str(r[3] or '')[:20]:20s} {r[1][:50]:50s}")

    # Series titles
    print("\n=== SAMPLE SERIES TITLES ===")
    cur.execute("SELECT id, title, external_id FROM content WHERE type='series' ORDER BY id")
    for r in cur.fetchall():
        print(f"  ID={r[0]:3d} {r[1][:60]:60s}")

    # Cartoon content
    print("\n=== ALL CARTOON CONTENT ===")
    cur.execute("SELECT id, title, external_id FROM content WHERE type='cartoon' ORDER BY id")
    cartoons = cur.fetchall()
    for r in cartoons:
        print(f"  ID={r[0]:3d} {r[1][:60]:60s}")

    # Check cartoon titles on tranimeizle
    print("\n=== CARTOON AVAILABILITY ON TRANIMEIZLE ===")
    async with httpx.AsyncClient(timeout=15) as cl:
        for cid, title, ext in cartoons[:10]:
            slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
            slug = re.sub(r'\([^)]*\)', '', slug).strip('-')
            slug = re.sub(r'-+', '-', slug)
            label, status, size, ok = await check(cl, f"https://tranimeizle.org.tr/{slug}/", f"cartoon/{slug}")
            if ok:
                print(f"  ✅ /{slug}/: HTTP {status} ({size}B) - '{title}'")
            else:
                print(f"  ❌ /{slug}/: HTTP {status} ({size}B) - '{title}'")
            await asyncio.sleep(0.3)

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
