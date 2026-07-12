"""Check all Naruto sites in DB"""
import sqlite3
conn = sqlite3.connect("memory/kurowatch.db")
c = conn.cursor()

c.execute("SELECT * FROM site WHERE content_id=469")
cols = [d[0] for d in c.description]
print("=== All Naruto Sites ===")
for row in c.fetchall():
    d = dict(zip(cols, row))
    print(f"  id={d['id']} name={d.get('site_name','')} primary={d.get('is_primary')} dead={d.get('is_dead')}")
    print(f"    url={d.get('site_url','')[:120]}")

# Count episodes total
c.execute("SELECT COUNT(*) FROM episode WHERE content_id=469")
print(f"\nTotal episodes: {c.fetchone()[0]}")

# Show a few with different domains
c.execute("SELECT DISTINCT url FROM episode WHERE content_id=469 LIMIT 20")
for row in c.fetchall():
    print(f"  {row[0][:80] if row[0] else None}")

conn.close()
