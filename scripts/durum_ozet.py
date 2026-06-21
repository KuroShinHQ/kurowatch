import sqlite3
conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

total = conn.execute('SELECT COUNT(*) FROM content').fetchone()[0]
by_type = conn.execute('SELECT type, COUNT(*) FROM content GROUP BY type').fetchall()

print(f'=== TOPLAM: {total} ===')
for t, c in by_type:
    print(f'  {t}: {c}')

print()
print('--- Çalışan sitelerle kaç içerik ---')
sites = [
    ('turkanime', 'turkanime'),
    ('anizm', 'anizm'),
    ('tranimaci', 'tranimaci'),
    ('mangawow', 'mangawow'),
    ('ragnarscans', 'ragnarscans'),
    ('hayalistic', 'hayalistic'),
    ('tranimeizle (BOZUK-CF)', 'tranimeizle'),
    ('dizibox (BOZUK-CF)', 'dizibox'),
    ('hdfilmcehennemi (BOZUK-CF)', 'hdfilmcehennemi'),
]
for label, kw in sites:
    q = "SELECT COUNT(DISTINCT content_id) FROM site WHERE site_url LIKE ?"
    n = conn.execute(q, (f'%{kw}%',)).fetchone()[0]
    print(f'  {label}: {n}')

print()
# Hiçbir çalışan sitesi olmayan
working_kws = ['turkanime', 'anizm', 'tranimaci', 'mangawow', 'ragnarscans', 'hayalistic']
cond = ' OR '.join([f"s.site_url LIKE '%{k}%'" for k in working_kws])
no_working = conn.execute(f'''
    SELECT COUNT(DISTINCT c.id) FROM content c
    WHERE NOT EXISTS (
        SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond})
    )
    AND EXISTS (SELECT 1 FROM site s2 WHERE s2.content_id=c.id)
''').fetchone()[0]
print(f'Kayıtlı ama çalışan kaynak YOK: {no_working}')

no_site = conn.execute('''
    SELECT COUNT(*) FROM content c
    WHERE NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id)
''').fetchone()[0]
print(f'Hiç site kaydı olmayan: {no_site}')

# Çalışan kaynaktan en az 1'i olan
has_working = conn.execute(f'''
    SELECT COUNT(DISTINCT c.id) FROM content c
    WHERE EXISTS (
        SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond})
    )
''').fetchone()[0]
print(f'En az 1 ÇALIŞAN kaynağı olan: {has_working} / {total}')

conn.close()
