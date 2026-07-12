"""
SOHBET-146 FIX 2: Kalan hdfilmcehennemi.now hataları için
just update ALL hdfilmcehennemi site URLs to the correct /film/ slug.
Don't delete anything.
"""
import sqlite3, httpx, re

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

db = sqlite3.connect(DB_PATH)
cur = db.cursor()

# Get all content with hdfilmcehennemi episodes that have /film/
cur.execute("""
    SELECT DISTINCT c.id, c.title, e.url
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE e.url LIKE '%hdfilmcehennemi%' AND e.url LIKE '%/film/%'
    ORDER BY c.title
""")
content_with_film = cur.fetchall()
print(f"Content with /film/ episode URLs: {len(content_with_film)}")

fix_count = 0
for cid, title, ep_url in content_with_film:
    # Get all hdfilmcehennemi site entries for this content
    cur.execute("""
        SELECT id, site_url FROM site 
        WHERE content_id = ? AND site_url LIKE '%hdfilmcehennemi%'
        ORDER BY id
    """, (cid,))
    site_entries = cur.fetchall()
    
    if not site_entries:
        continue
    
    # Extract the correct /film/ slug from episode URL
    match = re.search(r'(/film/[^/]+/)', ep_url)
    if not match:
        continue
    
    correct_path = match.group(1)
    correct_url = f'https://www.hdfilmcehennemi.now{correct_path}'
    
    # Verify the correct URL works
    try:
        r = httpx.get(correct_url, headers={'User-Agent': UA}, follow_redirects=True, timeout=10)
        if r.status_code != 200:
            continue
    except:
        continue
    
    # Update ALL hdfilmcehennemi site entries to the correct URL
    for sid, surl in site_entries:
        if surl != correct_url:
            cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (correct_url, sid))
            fix_count += 1
            
db.commit()
print(f"Güncellenen site entry: {fix_count}")

# Now also handle content with .nl episode URLs
cur.execute("""
    SELECT DISTINCT c.id, c.title, e.url
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE e.url LIKE '%.nl/%'
    ORDER BY c.title
""")
nl_content = cur.fetchall()
nl_fix = 0
for cid, title, ep_url in nl_content:
    nl_url = ep_url  # already the correct URL
    cur.execute("""
        SELECT id, site_url FROM site 
        WHERE content_id = ? AND site_url LIKE '%hdfilmcehennemi%'
    """, (cid,))
    for sid, surl in cur.fetchall():
        if surl != nl_url:
            cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (nl_url, sid))
            nl_fix += 1
db.commit()
print(f"Güncellenen .nl site entry: {nl_fix}")

# Final count
cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE '%hdfilmcehennemi.now%'")
now_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE '%.nl%'")
nl_count = cur.fetchone()[0]
cur.execute("""
    SELECT COUNT(*) FROM site 
    WHERE site_url LIKE '%hdfilmcehennemi%' 
    AND site_url NOT LIKE '%/film/%' 
    AND site_url NOT LIKE '%.nl/%'
""")
old_count = cur.fetchone()[0]
print(f"\nSon durum: .now/ film: {now_count}, .nl: {nl_count}, old format: {old_count}")

db.close()
