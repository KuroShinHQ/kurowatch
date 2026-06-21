import sqlite3
conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

working_kws = ['turkanime', 'anizm', 'tranimaci', 'mangawow', 'ragnarscans', 'hayalistic']
cond = ' OR '.join([f"s.site_url LIKE '%{k}%'" for k in working_kws])

rows = conn.execute(f'''
    SELECT c.id, c.type, c.title
    FROM content c
    WHERE c.type IN ('anime', 'manhwa', 'manga')
    AND NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond})
    )
    ORDER BY c.type, c.title
''').fetchall()

cur_type = None
for cid, ctype, title in rows:
    if ctype != cur_type:
        cur_type = ctype
        print(f'\n=== {ctype.upper()} ===')
    print(f'  [{cid}] {title}')

print(f'\nToplam: {len(rows)}')
conn.close()
