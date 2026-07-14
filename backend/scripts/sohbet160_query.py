import sqlite3, json, os
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "..", "..", "memory", "kurowatch.db")
db_path = os.path.normpath(db_path)

db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row

# Count by type
cur = db.execute("SELECT type, COUNT(*) FROM content GROUP BY type")
for r in cur.fetchall():
    print(f"  {r['type']}: {r['COUNT(*)']}")

# Manga/Manhwa
cur = db.execute("SELECT id, title, type FROM content WHERE type IN ('manga','manhwa') ORDER BY id")
manga = [dict(r) for r in cur.fetchall()]
print(f"\nManga/Manhwa: {len(manga)}")
for m in manga:
    print(f"  {m['type']}: {m['title']}")

# Existing monomanga sites
cur = db.execute("""SELECT c.id, c.title, s.site_name, s.site_url FROM content c
    JOIN site s ON c.id = s.content_id
    WHERE s.site_name LIKE '%monomanga%'""")
existing = [dict(r) for r in cur.fetchall()]
print(f"\nExisting monomanga sites: {len(existing)}")
for e in existing:
    print(f"  {e['title']}: {e['site_url']}")

# Films
cur = db.execute("SELECT id, title FROM content WHERE type='movie' ORDER BY id")
films = [dict(r) for r in cur.fetchall()]
print(f"\nTotal films: {len(films)}")

# Films with hdfc site
cur = db.execute("""SELECT c.id FROM content c
    WHERE c.type='movie' AND c.id IN (
        SELECT content_id FROM site WHERE site_name LIKE '%hdfilmcehennemi%'
    )""")
has_hdfc = set(r['id'] for r in cur.fetchall())
print(f"Films with hdfc site: {len(has_hdfc)}")
orphan = [f for f in films if f['id'] not in has_hdfc]
print(f"Orphan films (no hdfc): {len(orphan)}")
for o in orphan:
    print(f"  {o['title']}")
