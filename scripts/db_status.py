import sqlite3

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

print('=== TOPLAM ÖZET ===')
total = conn.execute('SELECT COUNT(*) FROM content').fetchone()[0]
print(f'Toplam içerik: {total}')

for r in conn.execute('SELECT type, COUNT(*) FROM content GROUP BY type ORDER BY COUNT(*) DESC').fetchall():
    print(f'  {r[0]}: {r[1]}')

print()
print('=== SİTE URL DOMAİN DAĞILIMI ===')
q = """
    SELECT
        CASE
            WHEN site_url LIKE '%turkanime%' THEN 'turkanime.tv'
            WHEN site_url LIKE '%tranimeizle%' THEN 'tranimeizle.co'
            WHEN site_url LIKE '%tranimaci%' THEN 'tranimaci.com'
            WHEN site_url LIKE '%anizm%' THEN 'anizm.net'
            WHEN site_url LIKE '%ragnarscans%' THEN 'ragnarscans.com/net'
            WHEN site_url LIKE '%mangawow%' THEN 'mangawow.com'
            WHEN site_url LIKE '%hayalistic%' THEN 'hayalistic.com.tr'
            WHEN site_url LIKE '%dizibox%' THEN 'dizibox.so/live'
            WHEN site_url LIKE '%hdfilmcehennemi%' THEN 'hdfilmcehennemi.nl'
            WHEN site_url LIKE '%yabancidizi%' THEN 'yabancidizi.pro'
            WHEN site_url LIKE '%diziwatch%' THEN 'diziwatch.net'
            WHEN site_url LIKE '%mangatr%' THEN 'mangatr.net'
            WHEN site_url LIKE '%mangaoku%' THEN 'mangaokutr.com'
            WHEN site_url IS NULL OR site_url = '' THEN '(url yok)'
            ELSE 'diger'
        END as domain,
        COUNT(*) as cnt
    FROM site
    GROUP BY domain
    ORDER BY cnt DESC
"""
for r in conn.execute(q).fetchall():
    print(f'  {r[0]}: {r[1]}')

print()
print('=== URL KAPSAMI ===')
no_site = conn.execute('SELECT COUNT(*) FROM content c WHERE NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id)').fetchone()[0]
has_site = conn.execute('SELECT COUNT(*) FROM content c WHERE EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url IS NOT NULL AND s.site_url != "")').fetchone()[0]
print(f'URL kayıtlı: {has_site}  |  URL YOK: {no_site}')

print()
print('Tipe göre:')
q2 = """
    SELECT c.type,
        SUM(CASE WHEN EXISTS(SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url IS NOT NULL AND s.site_url != '') THEN 1 ELSE 0 END) as with_url,
        SUM(CASE WHEN NOT EXISTS(SELECT 1 FROM site s WHERE s.content_id=c.id) THEN 1 ELSE 0 END) as no_url,
        COUNT(*) as total
    FROM content c GROUP BY c.type ORDER BY total DESC
"""
for r in conn.execute(q2).fetchall():
    pct = round(r[1]/r[3]*100) if r[3] else 0
    print(f'  {r[0]:10s}: {r[1]}/{r[3]} URL var (%{pct})  |  {r[2]} URL yok')

print()
print('=== İNDİRİLEBİLİR ANİME SİTELER (turkanime+anizm+tranimaci) ===')
q3 = """
    SELECT COUNT(DISTINCT s.content_id)
    FROM site s
    WHERE s.site_url LIKE '%turkanime%'
       OR s.site_url LIKE '%anizm%'
       OR s.site_url LIKE '%tranimaci%'
"""
ok_anime = conn.execute(q3).fetchone()[0]
print(f'  Çalışan anime site URL: ~{ok_anime} içerik')

print()
print('=== İNDİRİLEBİLİR MANGA SİTELER (ragnar+mangawow+hayalistic) ===')
q4 = """
    SELECT COUNT(DISTINCT s.content_id)
    FROM site s
    WHERE s.site_url LIKE '%ragnarscans%'
       OR s.site_url LIKE '%mangawow%'
       OR s.site_url LIKE '%hayalistic%'
"""
ok_manga = conn.execute(q4).fetchone()[0]
print(f'  Çalışan manga site URL: ~{ok_manga} içerik')

print()
print('=== BÖLÜM SAYILARI ===')
ep_total = conn.execute('SELECT COUNT(*) FROM episode').fetchone()[0]
ep_watched = conn.execute('SELECT COUNT(*) FROM episode WHERE is_watched=1').fetchone()[0]
print(f'Toplam bölüm: {ep_total}  |  İzlendi: {ep_watched}')

conn.close()
