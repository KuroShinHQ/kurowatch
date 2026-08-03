"""SOHBET-157: Convert hdfilmcehennemi.nl movie URLs to .io/.sh/.net mirrors.
Test multiple URL patterns per movie and verify each returns HTTP 200.
"""
import asyncio, httpx, sqlite3, json, re

DB_PATH = 'memory/kurowatch.db'
MIRRORS = ['www.hdfilmcehennemi.io', 'www.hdfilmcehennemi.sh', 'www.hdfilmcehennemi.net']

async def check_url(client, url):
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        return r.status_code, len(r.text)
    except Exception as e:
        return None, str(e)[:50]

async def main():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()

    cur.execute("""
        SELECT c.id, c.title, s.id, s.site_url, s.is_primary
        FROM content c JOIN site s ON s.content_id = c.id
        WHERE c.type = 'movie'
        AND s.site_url LIKE '%hdfilmcehennemi.nl%'
        AND (s.is_dead IS NULL OR s.is_dead = 0)
        AND NOT EXISTS (
            SELECT 1 FROM site s2 WHERE s2.content_id = c.id
            AND (s2.site_url LIKE '%hdfilmcehennemi.io%'
                 OR s2.site_url LIKE '%hdfilmcehennemi.sh%'
                 OR s2.site_url LIKE '%hdfilmcehennemi.net%')
        )
        ORDER BY c.id
    """)
    movies = cur.fetchall()
    print(f"Movies to convert: {len(movies)}")

    found = 0
    failed = 0
    results = []

    async with httpx.AsyncClient(timeout=12) as client:
        for idx, (cid, title, sid, site_url, is_primary) in enumerate(movies):
            old_path = site_url.rstrip('/')
            segments = old_path.split('/')
            raw_slug = segments[-1] if segments else ''

            # Strip common suffixes
            for suffix in ['-izle-2', '-izle']:
                if raw_slug.endswith(suffix):
                    raw_slug = raw_slug[:-len(suffix)]

            # Generate candidate slugs
            cands = set()
            cands.add(raw_slug)
            # Original full segment
            cands.add(segments[-1] if segments else raw_slug)

            if '/film/' in site_url and len(segments) >= 2:
                # The slug after /film/ might be different
                film_idx = -1
                for i, seg in enumerate(segments):
                    if seg == 'film' and i+1 < len(segments):
                        film_idx = i
                        break
                if film_idx >= 0:
                    after_film = '/'.join(segments[film_idx+1:])
                    cands.add(after_film)
                    # Also try without suffix
                    for sfx in ['-izle-2', '-izle']:
                        if after_film.endswith(sfx):
                            cands.add(after_film[:-len(sfx)])

            best = None
            for mirror in MIRRORS:
                for slug in sorted(cands):
                    url = f"https://{mirror}/{slug}/"
                    status, size = await check_url(client, url)
                    if status == 200 and (isinstance(size, int) and size > 5000):
                        best = (mirror, slug, url)
                        print(f"  [{idx+1}] ID={cid} '{title}': {mirror}/{slug}/ -> HTTP {status} ({size} bytes)")
                        break
                if best:
                    break

            if best:
                mirror, slug, url = best
                cur.execute("UPDATE site SET is_dead=1 WHERE id=?", (sid,))
                cur.execute("""
                    INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
                    VALUES (?, ?, ?, ?, 0)
                """, (cid, mirror, url, is_primary))
                db.commit()
                found += 1
                results.append({"content_id": cid, "title": title, "mirror": mirror, "slug": slug, "status": "ok"})
            else:
                print(f"  [{idx+1}] ID={cid} '{title}': NO MATCH on any mirror")
                failed += 1
                results.append({"content_id": cid, "title": title, "status": "no_match"})

            if (idx + 1) % 5 == 0:
                await asyncio.sleep(0.5)

    print(f"\n=== MOVIE CONVERSION SUMMARY ===")
    print(f"  Converted: {found}/{len(movies)}")
    print(f"  Failed: {failed}/{len(movies)}")

    # Remaining orphan movies
    cur.execute("""
        SELECT COUNT(*) FROM content c
        WHERE c.type = 'movie'
        AND NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
    """)
    remaining = cur.fetchone()[0]
    print(f"  Still orphan movies: {remaining}")

    with open('docs/sohbet157_movie_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    db.close()

if __name__ == "__main__":
    asyncio.run(main())
