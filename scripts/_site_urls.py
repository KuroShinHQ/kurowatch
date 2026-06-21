import sqlite3

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
SELECT s.id as site_id, s.site_name, s.site_url, s.is_dead, c.title, c.type
FROM site s JOIN content c ON c.id = s.content_id
WHERE s.site_url IS NOT NULL AND s.site_url != ''
ORDER BY s.site_name, c.id
""")
rows = cur.fetchall()

sites = {}
for r in rows:
    name = r['site_name']
    if name not in sites:
        sites[name] = {
            'url': r['site_url'],
            'title': r['title'],
            'type': r['type'],
            'dead': r['is_dead']
        }

for k, v in sorted(sites.items()):
    dead_str = "DEAD" if v['dead'] else "ok  "
    print(k[:30].ljust(30), "|", v['type'][:8].ljust(8), "|", dead_str, "|", v['title'][:35].ljust(35), "|", v['url'][:80])

conn.close()
