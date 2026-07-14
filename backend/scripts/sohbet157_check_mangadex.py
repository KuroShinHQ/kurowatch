import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

cur.execute("SELECT id, content_id, site_name, site_url, is_primary, is_dead FROM site WHERE site_name LIKE '%MangaDex%' OR site_url LIKE '%mangadex%'")
print("=== EXISTING MANGADEX SITES ===")
for r in cur.fetchall():
    print(f"  ID={r[0]} content_id={r[1]} name={r[2]} url={r[3]} primary={r[4]} dead={r[5]}")

cur.execute("SELECT id, title, type, external_id FROM content WHERE external_id LIKE 'mdx:%'")
print("\n=== EXISTING MDX EXTERNAL IDS ===")
for r in cur.fetchall():
    print(f"  ID={r[0]} {r[1][:40]:40s} {r[2]:10s} {r[3]}")

cur.execute("SELECT substr(external_id,1,20) as prefix, COUNT(*) as cnt FROM content WHERE external_id IS NOT NULL GROUP BY prefix ORDER BY cnt DESC")
print("\n=== EXTERNAL ID PREFIXES ===")
for r in cur.fetchall():
    print(f"  {r[0]:20s}  {r[1]}")

db.close()
