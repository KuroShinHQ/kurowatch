import json, sqlite3

with open('/mnt/c/Kuroshin/kurowatch/scripts/ta_romaji_cache.json') as f:
    cache = {str(x['id']): x for x in json.load(f)}

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
check_ids = [204, 205, 232, 235, 242, 381, 404, 496, 244, 238]
for cid in check_ids:
    row = conn.execute('SELECT title, external_id FROM content WHERE id=?', (cid,)).fetchone()
    if not row: continue
    c = cache.get(str(cid), {})
    romaji = c.get('romaji') or '-'
    english = c.get('english') or '-'
    print(f"[{cid}] {row[0][:25]:25} ext={str(row[1]):15} romaji={romaji} | english={english}")
conn.close()
