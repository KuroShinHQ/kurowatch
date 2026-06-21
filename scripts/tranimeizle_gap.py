import sqlite3

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

# Sadece tranimeizle URL'si olan, turkanime URL'si OLMAYAN animeler
q = """
    SELECT c.id, c.title, c.type, c.total_episodes
    FROM content c
    WHERE c.type = 'anime'
    AND EXISTS (
        SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%tranimeizle%'
    )
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%turkanime%'
    )
    ORDER BY c.title
"""
rows = conn.execute(q).fetchall()
print(f"Sadece tranimeizle var, turkanime YOK: {len(rows)} anime")
print()
for r in rows[:40]:
    print(f"  [{r[0]}] {r[1]} (ep:{r[3]})")
if len(rows) > 40:
    print(f"  ... +{len(rows)-40} tane daha")

print()
# Overlap: hem tranimeizle hem turkanime olan
q2 = """
    SELECT COUNT(*) FROM content c
    WHERE EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%tranimeizle%')
    AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%turkanime%')
"""
overlap = conn.execute(q2).fetchone()[0]
print(f"Hem tranimeizle hem turkanime var: {overlap} anime (zaten kurtarılmış)")

# Turkanime.tv'nin arama URL yapısı hakkında mevcut örnekler
print()
print("Mevcut turkanime.tv URL örnekleri (ilk 5):")
urls = conn.execute("SELECT site_url FROM site WHERE site_url LIKE '%turkanime%' LIMIT 5").fetchall()
for u in urls:
    print(f"  {u[0]}")

conn.close()
