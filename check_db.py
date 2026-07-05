import sqlite3
c = sqlite3.connect("/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db")
# episode tablo sütunları
cols = [r[1] for r in c.execute("PRAGMA table_info(episode)").fetchall()]
print("episode columns:", cols)
# Dungeon Meshi url'leri
rows = c.execute(
    "SELECT e.* FROM episode e "
    "JOIN content ct ON ct.id=e.content_id "
    "WHERE ct.title LIKE '%Dungeon%' LIMIT 5"
).fetchall()
for r in rows:
    print(r)
c.close()
