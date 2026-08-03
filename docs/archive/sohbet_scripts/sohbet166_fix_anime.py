"""SOHBET-166 — Fix anime: tranimaci.com → tranimeizle.org.tr for ALL anime/cartoon episodes.
Also fix the backend startup error and test download."""
import sqlite3, os, httpx, asyncio

DB = os.path.join("memory", "kurowatch.db")
db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

# 1. Count anime with tranimaci.com episode URLs
cur = db.execute("""
    SELECT COUNT(*) as cnt FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE c.type IN ('anime', 'cartoon') AND e.url LIKE '%tranimaci.com%'
""")
tranimaci_count = cur.fetchone()["cnt"]
print(f"Anime/cartoon episodes with tranimaci.com: {tranimaci_count}")

# 2. For each content with tranimaci episode URLs, check if tranimeizle.org.tr site exists
cur = db.execute("""
    SELECT DISTINCT c.id, c.title
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE c.type IN ('anime', 'cartoon') AND e.url LIKE '%tranimaci.com%'
""")
contents_with_tranimaci = [dict(r) for r in cur.fetchall()]
print(f"Contents with tranimaci episodes: {len(contents_with_tranimaci)}")

# 3. For each, find the tranimeizle.org.tr site URL
updated = 0
for c in contents_with_tranimaci:
    cid = c["id"]
    # Find tranimeizle.org.tr site
    cur2 = db.execute("SELECT id, site_url FROM site WHERE content_id=? AND site_url LIKE '%tranimeizle.org.tr%'", (cid,))
    tr_site = cur2.fetchone()
    
    if tr_site:
        # Make tranimeizle primary
        db.execute("UPDATE site SET is_primary=0 WHERE content_id=? AND site_url LIKE '%tranimaci%'", (cid,))
        db.execute("UPDATE site SET is_primary=1, is_dead=0 WHERE id=?", (tr_site["id"],))
        
        # Update episode URLs to tranimeizle series URL
        # tranimeizle.org.tr/{slug}/ is the series page — stream_finder will find episodes
        series_url = tr_site["site_url"]
        db.execute("UPDATE episode SET url=? WHERE content_id=? AND url LIKE '%tranimaci.com%'", (series_url, cid))
        updated += 1
    else:
        # No tranimeizle site — try Anizm (tranimeizle.xyz or similar)
        cur3 = db.execute("SELECT id, site_url FROM site WHERE content_id=? AND (site_url LIKE '%tranimeizle%' OR site_url LIKE '%anizm%' OR site_name LIKE '%Anizm%') AND (is_dead=0 OR is_dead IS NULL)", (cid,))
        alt_site = cur3.fetchone()
        if alt_site:
            db.execute("UPDATE site SET is_primary=1, is_dead=0 WHERE id=?", (alt_site["id"],))
            db.execute("UPDATE site SET is_primary=0 WHERE content_id=? AND site_url LIKE '%tranimaci%'", (cid,))
            db.execute("UPDATE episode SET url=? WHERE content_id=? AND url LIKE '%tranimaci.com%'", (alt_site["site_url"], cid))
            updated += 1

db.commit()
print(f"Updated: {updated}/{len(contents_with_tranimaci)} contents (tranimaci → tranimeizle/Anizm)")

# 4. Check Shinchou Yuusha specifically
print("\n=== Shinchou Yuusha (538/539) ===")
for cid in [538, 539]:
    cur = db.execute("SELECT id, title FROM content WHERE id=?", (cid,))
    c = cur.fetchone()
    cur2 = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=? ORDER BY is_primary DESC, is_dead ASC", (cid,))
    sites = cur2.fetchall()
    cur3 = db.execute("SELECT number, url FROM episode WHERE content_id=? LIMIT 3", (cid,))
    eps = cur3.fetchall()
    print(f"  c.id={cid} {c['title'][:40]}")
    for s in sites[:3]:
        print(f"    site: {s['site_name']:15s} primary={s['is_primary']} dead={s['is_dead']} | {s['site_url'][:60]}")
    for e in eps:
        print(f"    ep#{e['number']}: {e['url'][:70]}")

# 5. Verify — check no tranimaci.com primary URLs remain
cur = db.execute("""
    SELECT COUNT(*) as cnt FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE c.type IN ('anime', 'cartoon') AND s.is_primary=1 AND s.site_url LIKE '%tranimaci.com%'
""")
remaining = cur.fetchone()["cnt"]
print(f"\nAnime/cartoon with tranimaci.com as primary: {remaining}")

db.close()
print("\n=== DONE ===")
