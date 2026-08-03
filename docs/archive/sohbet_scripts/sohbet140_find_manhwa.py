"""Find manhwa content with URLs and sites."""
import sqlite3, os
db = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
conn = sqlite3.connect(db)
# Find manhwa with URLs
cur = conn.execute("""
    SELECT c.id, c.title, COUNT(e.id) as e_cnt, COUNT(e.url) FILTER(WHERE e.url IS NOT NULL AND e.url != '') as u_cnt
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE c.type = 'manhwa'
    GROUP BY c.id
    HAVING u_cnt > 0
    ORDER BY c.title
    LIMIT 20
""")
print("=== Manhwa with URLs ===")
for r in cur.fetchall():
    print(f"  #{r[0]} '{r[1]}': {r[2]} eps, {r[3]} with URLs")

# Also search for Solo Leveling across all types
cur2 = conn.execute("SELECT id, title, type FROM content WHERE title LIKE '%Solo Leveling%' OR title LIKE '%solo leveling%'")
print("\n=== Solo Leveling ===")
for r in cur2.fetchall():
    print(f"  #{r[0]} '{r[1]}' ({r[2]})")

# Find a good manhwa with many URL'd eps
cur3 = conn.execute("""
    SELECT c.id, c.title, COUNT(e.id) as e_cnt, COUNT(e.url) FILTER(WHERE e.url IS NOT NULL AND e.url != '') as u_cnt
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE c.type = 'manhwa' AND e.url IS NOT NULL AND e.url != ''
    GROUP BY c.id
    HAVING u_cnt > 50
    ORDER BY u_cnt DESC
    LIMIT 5
""")
print("\n=== Manhwa with 50+ URLs ===")
for r in cur3.fetchall():
    print(f"  #{r[0]} '{r[1]}': {r[2]} eps, {r[3]} with URLs")

conn.close()
