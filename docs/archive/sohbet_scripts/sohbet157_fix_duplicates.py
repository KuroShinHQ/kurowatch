"""Fix duplicate MangaDex UUIDs from fuzzy matches"""
import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Check for duplicate mdx UUIDs
cur.execute("""
    SELECT external_id, COUNT(*) as cnt
    FROM content 
    WHERE external_id LIKE 'mdx:%'
    GROUP BY external_id
    HAVING cnt > 1
""")
print("=== DUPLICATE MDX UUIDs ===")
for r in cur.fetchall():
    cur2 = db.cursor()
    cur2.execute("SELECT id, title FROM content WHERE external_id=?", (r[0],))
    items = cur2.fetchall()
    print(f"  {r[0][:20]}... shared by:")
    for item in items:
        print(f"    ID={item[0]}: {item[1]}")
    
    # Keep earliest ID, remove duplicates
    items.sort()
    keep_id = items[0][0]
    for cid, title in items[1:]:
        print(f"    -> Removing MangaDex from ID={cid} '{title}'")
        cur.execute("DELETE FROM site WHERE content_id=? AND site_name='MangaDex'", (cid,))
        cur.execute("UPDATE content SET external_id=NULL WHERE id=?", (cid,))

db.commit()

# Final counts
cur.execute("SELECT COUNT(*) FROM content WHERE external_id LIKE 'mdx:%'")
print(f"\nUnique mdx external_ids: {cur.fetchone()[0]}")

cur.execute("""
    SELECT c.type, COUNT(*) FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id = c.id
        AND (s.is_dead IS NULL OR s.is_dead = 0)
    )
    GROUP BY c.type
    ORDER BY c.type
""")
print("\n=== FINAL ORPHAN COUNT ===")
all_rows = cur.fetchall()
for r in all_rows:
    cur2 = db.cursor()
    cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],))
    total = cur2.fetchone()[0]
    print(f"  {r[0]:10s}  {r[1]:3d}/{total}")
total_orphan = sum(r[1] for r in all_rows)
print(f"  TOTAL: {total_orphan}")

db.close()
