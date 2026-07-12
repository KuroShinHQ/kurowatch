"""Query Naruto content from DB"""
import sqlite3
conn = sqlite3.connect("memory/kurowatch.db")
c = conn.cursor()

print("=== Schema ===")
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='episode'")
print(c.fetchone()[0])
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='site'")
print(c.fetchone()[0])

print("\n=== Naruto Episodes ===")
c.execute("SELECT e.id, e.number, e.url FROM episode e WHERE e.content_id=469 ORDER BY e.number LIMIT 10")
for row in c.fetchall():
    print(f"  id={row[0]} num={row[1]} url={row[2][:100] if row[2] else None}")

print("\n=== Naruto Sites ===")
c.execute("SELECT * FROM site WHERE content_id=469")
cols = [d[0] for d in c.description]
for row in c.fetchall():
    d = dict(zip(cols, row))
    url = d.get("site_url", "")
    print(f"  id={d['id']} domain={d.get('domain_or_url','')} url={url[:100]}")

conn.close()
