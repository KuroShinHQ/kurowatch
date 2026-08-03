import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

cur.execute("SELECT COUNT(*) FROM episode WHERE url LIKE '%hdfilmcehennemi%' AND url LIKE '%/film/%'")
print(f'Our DB: {cur.fetchone()[0]} episodes with /film/ prefix')

cur.execute("SELECT COUNT(*) FROM episode WHERE url LIKE '%hdfilmcehennemi%' AND url LIKE '%.nl/%'")
print(f'Our DB: {cur.fetchone()[0]} episodes with .nl domain')

cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE '%hdfilmcehennemi%' AND site_url LIKE '%www.%'")
print(f'Our DB: {cur.fetchone()[0]} sites with www prefix')

cur.execute("SELECT site_url FROM site WHERE site_url LIKE '%hdfilmcehennemi%' LIMIT 3")
for row in cur.fetchall():
    print(f'  Site URL: {row[0][:70]}')

db.close()
