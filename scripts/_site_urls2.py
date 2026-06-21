import sqlite3

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Hedef domainler
targets = [
    'turkanime.co', 'diziwatch.com', 'anizm.net',
    'dizibox.live', 'hdfilmcehennemi.nl',
    'tranimaci.com', 'mangadex.org',
    'ruyamanga.com', 'ruyamanga.net', 'asurascans.com.tr',
]

print("=== EPISODE tablosu ===")
for domain in targets:
    cur.execute("""
        SELECT e.url, c.title, c.type, e.number
        FROM episode e JOIN content c ON c.id = e.content_id
        WHERE e.url LIKE ?
        ORDER BY c.id, e.number
        LIMIT 1
    """, (f'%{domain}%',))
    row = cur.fetchone()
    if row:
        print(f"[EPISODE] {domain:30} | {row['type']:8} | ep={row['number']} | {row['title'][:30]:30} | {row['url'][:80]}")
    else:
        print(f"[EPISODE] {domain:30} | -- YOK --")

print()
print("=== SITE tablosu ===")
for domain in targets:
    cur.execute("""
        SELECT s.site_url, s.site_name, s.is_dead, c.title, c.type
        FROM site s JOIN content c ON c.id = s.content_id
        WHERE s.site_url LIKE ?
        ORDER BY c.id
        LIMIT 1
    """, (f'%{domain}%',))
    row = cur.fetchone()
    if row:
        print(f"[SITE]    {domain:30} | {row['type']:8} | dead={row['is_dead']} | {row['title'][:30]:30} | {row['site_url'][:80]}")
    else:
        print(f"[SITE]    {domain:30} | -- YOK --")

conn.close()
