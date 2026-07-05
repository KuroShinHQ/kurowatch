import sqlite3
c = sqlite3.connect("/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db")

# mangatr.net icerikleri + episode sayisi
rows = c.execute("""
    SELECT ct.id, ct.title, ct.type, s.site_url, COUNT(e.id) as ep_count
    FROM content ct
    JOIN site s ON s.content_id = ct.id
    LEFT JOIN episode e ON e.content_id = ct.id
    WHERE s.site_url LIKE '%mangatr%'
    GROUP BY ct.id
    ORDER BY ep_count DESC
    LIMIT 10
""").fetchall()
print(f"mangatr.net icerikleri:")
for r in rows:
    print(f"  id={r[0]} [{r[2]}] {r[1]} | ep={r[4]} | {r[3]}")

# Episode olan varsa goster
for r in rows:
    if r[4] > 0:
        eps = c.execute(
            "SELECT number, url FROM episode WHERE content_id=? ORDER BY number LIMIT 3", (r[0],)
        ).fetchall()
        print(f"\ncontent_id={r[0]} bolumler:")
        for e in eps:
            print(f"  Bolum {e[0]}: {e[1]}")
        break
c.close()
