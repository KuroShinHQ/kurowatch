"""SOHBET-160: Batch add monomanga + 720pizle sites"""
import sqlite3, os, sys, asyncio, httpx, re, json, time
from urllib.parse import quote

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "..", "..", "memory", "kurowatch.db")
db_path = os.path.normpath(db_path)
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
db.execute("PRAGMA journal_mode=WAL")

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

async def check_http(client, url, timeout=12):
    try:
        r = await client.get(url, timeout=timeout, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        return r.status_code, len(r.text), r.text[:300]
    except Exception as e:
        return None, 0, str(e)[:60]

async def test_monomanga_slugs():
    """Test all remaining manga/manhwa on monomanga"""
    cur = db.execute("""SELECT c.id, c.title, c.type FROM content c
        WHERE c.type IN ('manga','manhwa') AND c.id NOT IN (
            SELECT content_id FROM site WHERE site_name LIKE '%monomanga%'
        )
        ORDER BY c.id""")
    items = [dict(r) for r in cur.fetchall()]
    print(f"\nManga/Manhwa to test on monomanga: {len(items)}")

    async with httpx.AsyncClient(timeout=12, limits=httpx.Limits(max_keepalive_connections=5, max_connections=5)) as cl:
        matches = []
        fails = []
        for i, item in enumerate(items):
            title = item['title']
            # Try multiple slug forms
            slug = slugify(title)
            url = f"https://monomanga.com.tr/manga/{slug}/"
            status, size, text = await check_http(cl, url)
            ok = status == 200 and size > 10000
            if ok:
                print(f"  ✅ [{i+1}/{len(items)}] {title} -> {slug} (HTTP {status}, {size}B)")
                matches.append((item['id'], url, slug))
            else:
                print(f"  ❌ [{i+1}/{len(items)}] {title} -> {slug} (HTTP {status}, {size}B)")
                fails.append((item['id'], title, slug, status))

            if (i+1) % 10 == 0:
                print(f"  --- progress: {i+1}/{len(items)} ---")

    print(f"\nMonomanga matches: {len(matches)}")
    print(f"Monomanga fails: {len(fails)}")

    # Save fails for alternative site search
    with open(os.path.join(script_dir, "sohbet160_monomanga_fails.json"), "w", encoding="utf-8") as f:
        json.dump(fails, f, ensure_ascii=False, indent=2)

    added = 0
    for content_id, url, slug in matches:
        existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_name LIKE '%monomanga%'", (content_id,)).fetchone()
        if not existing:
            ch_url = url.rstrip('/') + '/bolum-1'
            db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary) VALUES (?, ?, ?, ?)",
                       (content_id, "monomanga.com.tr", ch_url, 0))
            added += 1
        if added > 0 and added % 20 == 0:
            db.commit()
    db.commit()
    print(f"Added {added} monomanga site records")
    return matches, fails

async def test_720pizle_films():
    """Test all films on 720pizle"""
    cur = db.execute("""SELECT c.id, c.title FROM content c WHERE c.type='movie' ORDER BY c.id""")
    films = [dict(r) for r in cur.fetchall()]
    print(f"\nFilms to test on 720pizle: {len(films)}")

    async with httpx.AsyncClient(timeout=15, limits=httpx.Limits(max_keepalive_connections=5, max_connections=5)) as cl:
        matches = []
        fails = []
        for i, film in enumerate(films):
            title = film['title']
            # Try RAW title as slug (with Turkish chars) + slugified
            raw_slug = title.lower().replace(' ', '-')
            raw_slug = re.sub(r'[^a-z0-9\sçğıöşü\-]', '', raw_slug)
            raw_slug = re.sub(r'-+', '-', raw_slug).strip('-')
            clean_slug = slugify(title)

            # Multiple pattern variants
            variants = set()
            for base in [raw_slug, clean_slug]:
                variants.add(f"https://720pizle.com/film/{base}-izle/")
                variants.add(f"https://720pizle.com/{base}-izle/")
                variants.add(f"https://720pizle.com/film/{base}/")

            found = False
            for url in sorted(variants):
                status, size, text = await check_http(cl, url)
                ok = status == 200 and size > 10000
                if ok:
                    print(f"  ✅ [{i+1}/{len(films)}] {title} -> {url} (HTTP {status}, {size}B)")
                    matches.append((film['id'], url))
                    found = True
                    break
                await asyncio.sleep(0.05)
            if not found:
                print(f"  ❌ [{i+1}/{len(films)}] {title} (raw={raw_slug})")
                fails.append((film['id'], title, raw_slug))

            if (i+1) % 20 == 0:
                print(f"  --- progress: {i+1}/{len(films)} ---")

    print(f"\n720pizle matches: {len(matches)}")
    print(f"720pizle fails: {len(fails)}")

    added = 0
    for content_id, url in matches:
        existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_name LIKE '%720pizle%'", (content_id,)).fetchone()
        if not existing:
            db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary) VALUES (?, ?, ?, ?)",
                       (content_id, "720pizle.com", url, 0))
            added += 1
        if added > 0 and added % 20 == 0:
            db.commit()
    db.commit()
    print(f"Added {added} 720pizle site records")
    return matches, fails

async def main():
    print("="*60)
    print("SOHBET-160: BATCH SITE ADD")
    print("="*60)

    # Phase 1: Test 720pizle for films
    print("\n### PHASE 1: 720pizle film test ###")
    film_matches, film_fails = await test_720pizle_films()

    # Phase 2: Test monomanga for manga/manhwa
    print("\n### PHASE 2: Monomanga manga/manhwa test ###")
    manga_matches, manga_fails = await test_monomanga_slugs()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"720pizle film matches: {len(film_matches)}/{113}")
    print(f"Monomanga manga matches: {len(manga_matches)}/{162 - 19} remaining")

    # Save fail slugs for manual review
    with open(os.path.join(script_dir, "sohbet160_720pizle_fails.json"), "w", encoding="utf-8") as f:
        json.dump(film_fails, f, ensure_ascii=False, indent=2)

    print("\nFails saved to sohbet160_720pizle_fails.json and sohbet160_monomanga_fails.json")

if __name__ == "__main__":
    asyncio.run(main())
