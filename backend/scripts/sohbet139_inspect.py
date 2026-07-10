import sqlite3, os

db = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
conn = sqlite3.connect(db)

print("=== mangaokutr.com sites ===")
cur = conn.execute("SELECT id, content_id, site_url, is_dead FROM site WHERE site_url LIKE '%mangaokutr.com%'")
for r in cur.fetchall():
    print(f"  site#{r[0]}: content#{r[1]}, dead={r[2]}, url={r[3][:80]}")

print("\n=== Content IDs with mangaokutr ===")
cur = conn.execute("SELECT DISTINCT content_id FROM site WHERE site_url LIKE '%mangaokutr.com%'")
cids = [r[0] for r in cur.fetchall()]
print(f"  affected: {len(cids)} -> {cids}")

print("\n=== Episodes with mangaokutr URLs ===")
cur = conn.execute("SELECT COUNT([id]) FROM episode WHERE url LIKE '%mangaokutr.com%'")
print(f"  count: {cur.fetchone()[0]}")

print("\n=== Dexter ===")
cur = conn.execute("""
    SELECT c.id, c.title, c.type, s.id, s.site_url, s.is_dead
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE c.title LIKE '%Dexter%'
""")
for r in cur.fetchall():
    print(f"  content#{r[0]} '{r[1]}' ({r[2]}): site#{r[3]} dead={r[5]} url={r[4][:60]}")

cur = conn.execute("""
    SELECT COUNT(e.[id]),
           COUNT(e.[url]) FILTER(WHERE e.[url] IS NOT NULL AND e.[url] != '')
    FROM episode e
    JOIN content c ON e.content_id = c.id
    WHERE c.title LIKE '%Dexter%'
""")
cnt, url_cnt = cur.fetchone()
print(f"  Dexter episodes: {cnt} total, {url_cnt} with URLs")

print("\n=== Episode URL coverage by type ===")
cur = conn.execute("""
    SELECT c.type, COUNT(e.[id]),
           COUNT(e.[url]) FILTER(WHERE e.[url] IS NOT NULL AND e.[url] != '')
    FROM episode e
    JOIN content c ON e.content_id = c.id
    GROUP BY c.type ORDER BY c.type
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} eps, {r[2]} with URLs")

print("\n=== Series/movie/cartoon missing URLs ===")
cur = conn.execute("""
    SELECT c.type, COUNT(DISTINCT c.id)
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE c.type IN ('series','movie','cartoon')
      AND (e.url IS NULL OR e.url = '')
    GROUP BY c.type
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]} contents have episodes without URLs")

# Find a sample manga content that uses mangaokutr
print("\n=== Sample manga using mangaokutr ===")
cur = conn.execute("""
    SELECT c.id, c.title, c.type
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_url LIKE '%mangaokutr.com%'
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  content#{r[0]}: '{r[1]}' ({r[2]})")
    # Find first episode URL
    cur2 = conn.execute("SELECT url FROM episode WHERE content_id = ? AND url IS NOT NULL AND url != '' LIMIT 1", (r[0],))
    ep = cur2.fetchone()
    print(f"    episode URL: {ep[0][:80] if ep else 'NONE'}")

conn.close()
