"""Mark remaining dead sites from SOHBET-156 discovery"""
import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Check which DEAD_DOMAINS from SOHBET-156 are still not marked
dead_domains = [
    'arcanescans.com', 'diziwatch.net', 'hayalistic.com.tr',
    'mangakoleji.com', 'mangatepesi.com', 'mangatr.me',
    'mangawow.com', 'manhwahentai.me', 'merlinscans.com',
    'ragnarscans.net', 'tempestfansub.com', 'turkcemangaoku.com',
    'turkmanga.com.tr', 'w2.thegreatestestatedeveloper.site',
    'www.dizibox.so', 'www.tranimaci.com',
]

cf_domains = [
    'asurascans.com.tr', 'hayalistic.blog',
    'manga-sehri.net', 'mangasehri.net',
    'merlintoon.com', 'ruyamanga.net', 'www.ruyamanga.net',
]

total_marked = 0
for domain in dead_domains:
    cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE ? AND (is_dead IS NULL OR is_dead = 0)", (f'%{domain}%',))
    count = cur.fetchone()[0]
    if count > 0:
        cur.execute("UPDATE site SET is_dead=1 WHERE site_url LIKE ?", (f'%{domain}%',))
        total_marked += count
        print(f"  {domain:50s} {count} sites marked dead")

for domain in cf_domains:
    cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE ? AND (is_dead IS NULL OR is_dead = 0)", (f'%{domain}%',))
    count = cur.fetchone()[0]
    if count > 0:
        cur.execute("UPDATE site SET is_dead=1 WHERE site_url LIKE ?", (f'%{domain}%',))
        total_marked += count
        print(f"  {domain:50s} {count} CF sites marked dead")

db.commit()
print(f"\nTotal newly marked: {total_marked}")

# Final stats
cur.execute("SELECT is_dead, COUNT(*) FROM site GROUP BY is_dead")
print("\n=== SITE DEATH STATS ===")
for r in cur.fetchall():
    print(f"  is_dead={r[0]}: {r[1]}")

db.close()
