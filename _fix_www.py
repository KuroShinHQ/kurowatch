"""
SOHBET-146 FIX: Site URL'lerindeki www.www. hatasını düzelt
"""
import sqlite3

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Find all hdfilmcehennemi site URLs
cur.execute("SELECT id, site_url FROM site WHERE site_url LIKE '%hdfilmcehennemi%'")
sites = cur.fetchall()

print(f"Toplam hdfilmcehennemi site kaydı: {len(sites)}")

fixes = 0
for sid, site_url in sites:
    old_url = site_url
    
    # Fix 1: Remove double www
    site_url = site_url.replace('www.www.', 'www.')
    
    # Fix 2: Make sure there's no stray http://www.www. patterns
    site_url = site_url.replace('www.http://', 'http://www.')
    site_url = site_url.replace('www.https://', 'https://www.')
    
    if site_url != old_url:
        cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (site_url, sid))
        fixes += cur.rowcount
        print(f"  FIXED: {old_url[:60]} -> {site_url[:60]}")

db.commit()
print(f"\nDüzeltilen site URL: {fixes}")

# Verify current state
cur.execute("SELECT site_url FROM site WHERE site_url LIKE '%hdfilmcehennemi%' LIMIT 5")
print("\nGüncel site URL'leri:")
for row in cur.fetchall():
    print(f"  {row[0][:70]}")

# Also check episodes for sanity
cur.execute("SELECT url FROM episode WHERE url LIKE '%hdfilmcehennemi%' AND url LIKE '%.nl/%' LIMIT 3")
print("\n.nl episode URL'leri:")
for row in cur.fetchall():
    print(f"  {row[0][:70]}")

# Check www. in episode URLs
cur.execute("SELECT url FROM episode WHERE url LIKE '%hdfilmcehennemi%' AND url LIKE '%www.www.%'")
wwww = cur.fetchall()
print(f"\nwww.www. hatası episode'larda: {len(wwww)}")
for row in wwww[:3]:
    print(f"  {row[0][:70]}")

# Fix episode URLs too if needed
cur.execute("UPDATE episode SET url = REPLACE(url, 'www.www.', 'www.') WHERE url LIKE '%www.www.%'")
print(f"Düzeltilen episode URL: {cur.rowcount}")
db.commit()

db.close()
