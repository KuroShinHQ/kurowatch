"""SOHBET-158: Check remaining orphans + verify success"""
import sqlite3, json
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Full orphan count
cur.execute("""
    SELECT c.type, COUNT(*) FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    GROUP BY c.type
    ORDER BY c.type
""")
print("=== ORPHAN CONTENT ===")
all_orphan = cur.fetchall()
total_content = 0
total_orphan = 0
for r in all_orphan:
    cur2 = db.cursor()
    cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],))
    total = cur2.fetchone()[0]
    total_content += total
    total_orphan += r[1]
    alive_pct = 100 - 100 * r[1] // total if total > 0 else 0
    print(f"  {r[0]:10s}  orphan: {r[1]:3d}/{total}  alive: {alive_pct}%")

# Also count types with 0 orphan
cur.execute("SELECT DISTINCT type FROM content")
all_types = set(r[0] for r in cur.fetchall())
types_with_orphan = set(r[0] for r in all_orphan)
zero_orphan = all_types - types_with_orphan
for t in sorted(zero_orphan):
    cur.execute("SELECT COUNT(*) FROM content WHERE type=?", (t,))
    total = cur.fetchone()[0]
    total_content += total
    print(f"  {t:10s}  orphan: {0:3d}/{total}  alive: 100%")

print(f"\n  TOTAL: {total_orphan}/{total_content} orphan ({100-100*total_orphan//total_content}% alive)")

# Check the 1 orphan series
cur.execute("""
    SELECT c.id, c.title FROM content c
    WHERE c.type = 'series'
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
""")
print(f"\n=== ORPHAN SERIES ===")
for r in cur.fetchall():
    print(f"  ID={r[0]}: '{r[1]}'")

# Check orphan manga/manhwa
cur.execute("""
    SELECT c.id, c.title, c.type FROM content c
    WHERE c.type IN ('manga', 'manhwa')
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    ORDER BY c.type, c.id
""")
print(f"\n=== ORPHAN MANGA/MANHWA ===")
for r in cur.fetchall():
    print(f"  ID={r[0]:3d} {r[2]:10s} {r[1]}")

# Check hdfilmcehennemi sites - how many movies have .io/.sh/.net?
cur.execute("SELECT COUNT(DISTINCT content_id) FROM site WHERE site_url LIKE '%hdfilmcehennemi.io%' AND (is_dead IS NULL OR is_dead = 0)")
io_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE '%hdfilmcehennemi.nl%' AND (is_dead IS NULL OR is_dead = 0)")
nl_count = cur.fetchone()[0]
print(f"\n=== MOVIE SITE STATUS ===")
print(f"  hdfilmcehennemi.io/sh/net alive: {io_count}")
print(f"  hdfilmcehennemi.nl still alive: {nl_count}")
print(f"  Total movies with any alive site: {io_count + nl_count}")

# Current site distribution (top 10)
cur.execute("""
    SELECT s.site_name, COUNT(DISTINCT s.content_id) as cnt
    FROM site s WHERE s.is_dead IS NULL OR s.is_dead = 0
    GROUP BY s.site_name ORDER BY cnt DESC LIMIT 10
""")
print(f"\n=== TOP ALIVE SITE NAMES ===")
for r in cur.fetchall():
    print(f"  {r[0]:30s}  {r[1]}")

db.close()
