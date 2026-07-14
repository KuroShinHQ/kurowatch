"""Check impact of MangaDex sync on orphan content"""
import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Content with NO alive sites (after MangaDex sync)
cur.execute("""
    SELECT c.type, COUNT(*)
    FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s 
        WHERE s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    GROUP BY c.type
    ORDER BY c.type
""")
print("=== ORPHAN CONTENT AFTER MANGADEX SYNC ===")
total_orphan = 0
for r in cur.fetchall():
    cur2 = db.cursor()
    cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],))
    total = cur2.fetchone()[0]
    print(f"  {r[0]:10s}  {r[1]:3d}/{total} orphan ({100-100*r[1]//total}% alive)")
    total_orphan += r[1]
print(f"\n  TOTAL ORPHAN: {total_orphan}")

# Status BEFORE MangaDex (from earlier): 157 had at least 1 alive, 557 orphan
# Status AFTER: MangaDex added for 111 items
print(f"\n  ESTIMATED IMPACT: 557 -> {total_orphan} (saved {557 - total_orphan})")

# Content with MangaDex site now
cur.execute("""
    SELECT COUNT(DISTINCT s.content_id)
    FROM site s
    WHERE s.site_name = 'MangaDex' AND (s.is_dead IS NULL OR s.is_dead = 0)
""")
mdx_count = cur.fetchone()[0]
print(f"\n  Content with MangaDex site: {mdx_count}")

# Content with NO external_id
cur.execute("SELECT COUNT(*) FROM content WHERE external_id IS NULL")
print(f"  Content with NO external_id: {cur.fetchone()[0]}")

# Check if any manga/manhwa still have NO alive site (even after MangaDex)
cur.execute("""
    SELECT c.id, c.title, c.type
    FROM content c
    WHERE c.type IN ('manga', 'manhwa')
    AND NOT EXISTS (
        SELECT 1 FROM site s 
        WHERE s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    ORDER BY c.type, c.id
""")
still_orphan = cur.fetchall()
print(f"\n=== MANGA/MANHWA STILL ORPHAN (even after MangaDex) ===")
for r in still_orphan:
    print(f"  ID={r[0]:3d}  {r[2]:10s}  {r[1]}")
print(f"  Total: {len(still_orphan)}")

# Current alive site distribution
cur.execute("""
    SELECT s.site_name, COUNT(DISTINCT s.content_id) as cnt
    FROM site s
    WHERE s.is_dead IS NULL OR s.is_dead = 0
    GROUP BY s.site_name
    ORDER BY cnt DESC
""")
print(f"\n=== ALIVE SITES AFTER SYNC (by content count) ===")
for r in cur.fetchall():
    print(f"  {r[0]:30s}  {r[1]}")

db.close()
