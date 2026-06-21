import json, sqlite3

with open('/mnt/c/Kuroshin/kurowatch/scripts/ta_romaji_cache.json') as f:
    cache = {str(x['id']): x for x in json.load(f)}

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
# Şüpheli false positifler
sus = [213, 235, 515, 594, 612, 631, 637, 605, 390]
for cid in sus:
    row = conn.execute('SELECT title, external_id FROM content WHERE id=?', (cid,)).fetchone()
    if not row: continue
    c = cache.get(str(cid), {})
    r = c.get('romaji') or '-'
    e = c.get('english') or '-'
    print(f"[{cid}] {row[0][:28]:28} | romaji: {r[:35]:35} | eng: {e[:35]}")
conn.close()
