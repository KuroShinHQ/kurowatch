"""
Analyze all content items with EP_YOK status.
Outputs detailed info: type distribution, site URLs, working status.
"""
import sqlite3, re, sys, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Find all content items
total = conn.execute("SELECT COUNT(*) FROM content").fetchone()[0]
by_type = conn.execute("SELECT type, COUNT(*) FROM content GROUP BY type ORDER BY type").fetchall()

print(f"=== TOPLAM IÇERIK: {total} ===")
for t, c in by_type:
    print(f"  {t}: {c}")

# Find items with no episodes at all
print(f"\n=== EPISODE KAYDI OLMAYAN ICERIKLER ===")
no_ep = conn.execute("""
    SELECT c.* FROM content c
    LEFT JOIN episode e ON e.content_id = c.id
    WHERE e.id IS NULL
    ORDER BY c.type, c.title
""").fetchall()

for row in no_ep:
    sites = conn.execute("SELECT site_name, site_url, is_primary FROM site WHERE content_id=?", (row['id'],)).fetchall()
    print(f"\n#{row['id']} [{row['type']}] {row['title']}")
    if row['title_tr']:
        print(f"  TR: {row['title_tr']}")
    for s in sites:
        star = " ⭐" if s['is_primary'] else ""
        print(f"  SITE: {s['site_name']} -> {s['site_url']}{star}")

print(f"\n=== TOPLAM (HIC EPISODE YOK): {len(no_ep)} ===")
type_dist = {}
for r in no_ep:
    type_dist[r['type']] = type_dist.get(r['type'], 0) + 1
for t, c in sorted(type_dist.items()):
    print(f"  {t}: {c}")

# Also find items with episodes but all URLs are null
print(f"\n=== EPISODE VAR AMA URL'LERI NULL ===")
ep_null = conn.execute("""
    SELECT c.*, COUNT(e.id) as ep_count
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE c.id NOT IN (
        SELECT DISTINCT e2.content_id FROM episode e2 WHERE e2.url IS NOT NULL
    )
    GROUP BY c.id
    ORDER BY c.type, c.title
""").fetchall()

for row in ep_null:
    sites = conn.execute("SELECT site_name, site_url, is_primary FROM site WHERE content_id=?", (row['id'],)).fetchall()
    print(f"\n#{row['id']} [{row['type']}] {row['title']} (episodes: {row['ep_count']})")
    if row['title_tr']:
        print(f"  TR: {row['title_tr']}")
    for s in sites:
        star = " ⭐" if s['is_primary'] else ""
        print(f"  SITE: {s['site_name']} -> {s['site_url']}{star}")

print(f"\n=== TOPLAM (EP VAR EP_URL YOK): {len(ep_null)} ===")
type_dist2 = {}
for r in ep_null:
    type_dist2[r['type']] = type_dist2.get(r['type'], 0) + 1
for t, c in sorted(type_dist2.items()):
    print(f"  {t}: {c}")

# Also count items where episode 1 URL is null
ep1_null = conn.execute("""
    SELECT COUNT(DISTINCT c.id)
    FROM content c
    JOIN episode e ON e.content_id = c.id AND e.number = 1 AND e.season = 1
    WHERE e.url IS NULL
""").fetchone()[0]
print(f"\n=== EPISODE 1 URL NULL OLAN ICERIK: {ep1_null} ===")

conn.close()
