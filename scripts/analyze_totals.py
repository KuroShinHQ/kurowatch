"""
Check total_episodes / total_chapters for EP_YOK items.
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# EP_YOK items
rows = conn.execute("""
    SELECT c.id, c.type, c.title, c.total_episodes, c.total_chapters, c.my_progress
    FROM content c
    LEFT JOIN episode e ON e.content_id = c.id
    WHERE e.id IS NULL
    ORDER BY c.type, c.title
""").fetchall()

print(f"=== TOPLAM (HIC EPISODE YOK): {len(rows)} ===")
print()

by_type = {}
for r in rows:
    t = r['type']
    if t not in by_type:
        by_type[t] = {"total": 0, "has_total": 0, "no_total": []}
    by_type[t]["total"] += 1
    if t == 'anime':
        if r['total_episodes']:
            by_type[t]["has_total"] += 1
        else:
            by_type[t]["no_total"].append(r['title'])
    elif t in ('manga', 'manhwa'):
        if r['total_chapters']:
            by_type[t]["has_total"] += 1
        else:
            by_type[t]["no_total"].append(r['title'])
    elif t == 'game':
        by_type[t]["has_total"] += 1

for t, data in by_type.items():
    print(f"[{t}] Total: {data['total']}, Has total value: {data['has_total']}")
    if data['no_total']:
        print(f"  NO TOTAL ({len(data['no_total'])}):")
        for title in data['no_total']:
            print(f"    - {title}")
    print()

# Also check items that have wrong total (0 or very small)
print("=== TOTAL_EPISODES DAĞILIMI (anime) ===")
anime_totals = conn.execute("""
    SELECT c.id, c.title, c.total_episodes
    FROM content c
    LEFT JOIN episode e ON e.content_id = c.id
    WHERE e.id IS NULL AND c.type = 'anime'
    ORDER BY c.total_episodes
""").fetchall()
for r in anime_totals:
    print(f"  #{r['id']}: total_episodes={r['total_episodes']} - {r['title']}")

print()
print("=== TOTAL_CHAPTERS DAĞILIMI (manga/manhwa) ===")
manga_totals = conn.execute("""
    SELECT c.id, c.type, c.title, c.total_chapters
    FROM content c
    LEFT JOIN episode e ON e.content_id = c.id
    WHERE e.id IS NULL AND c.type IN ('manga', 'manhwa')
    ORDER BY c.total_chapters
""").fetchall()
for r in manga_totals:
    print(f"  #{r['id']} [{r['type']}]: total_chapters={r['total_chapters']} - {r['title']}")

conn.close()
