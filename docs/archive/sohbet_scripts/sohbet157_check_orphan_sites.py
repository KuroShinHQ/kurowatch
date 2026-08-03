"""Check existing site records for orphan manga/manhwa"""
import sqlite3, json
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

cur.execute("""
    SELECT c.id, c.title, c.type, c.external_id
    FROM content c WHERE c.type IN ('manga', 'manhwa')
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    ORDER BY c.id
""")
items = cur.fetchall()
print(f"Orphan manga/manhwa: {len(items)}")

for cid, title, ctype, ext in items:
    cur.execute("SELECT site_name, site_url, is_dead FROM site WHERE content_id=? ORDER BY is_dead", (cid,))
    sites = cur.fetchall()
    print(f"\nID={cid} '{title}' ({ctype}) ext={ext}")
    for s in sites:
        dead_str = "" if s[2] is None or s[2] == 0 else "DEAD"
        print(f"  {s[0]:25s} {s[1][:70]:70s} {dead_str}")

db.close()
