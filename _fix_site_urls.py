"""
SOHBET-146 FIX: Site URL'lerini episode'daki doğru /film/ slug ile güncelle
"""
import sqlite3

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Get all content with hdfilmcehennemi sites
cur.execute("""
    SELECT DISTINCT c.id, c.title, s.id as site_id, s.site_url
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE s.site_url LIKE '%hdfilmcehennemi%'
    AND s.site_url NOT LIKE '%.nl/%'
    ORDER BY c.title
""")
rows = cur.fetchall()
print(f"Toplam hdfilmcehennemi site entry: {len(rows)}")

# For each content, get the episode URL (which has correct /film/ slug)
updates = 0
content_site_updates = 0

for cid, title, site_id, site_url in rows:
    # Get the episode URL for this content (first one)
    cur.execute("""
        SELECT url FROM episode 
        WHERE content_id = ? AND url LIKE '%hdfilmcehennemi%' AND url LIKE '%/film/%'
        LIMIT 1
    """, (cid,))
    ep_row = cur.fetchone()
    
    if ep_row:
        correct_url = ep_row[0]
        # Extract the /film/slug/ part
        import re
        match = re.search(r'(/film/[^/]+/)', correct_url)
        if match:
            new_site_url = f'https://www.hdfilmcehennemi.now{match.group(1)}'
            # Verify it works before updating
            import httpx
            UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            try:
                r = httpx.get(new_site_url, headers={'User-Agent': UA}, follow_redirects=True, timeout=10)
                if r.status_code == 200:
                    if new_site_url != site_url:
                        cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (new_site_url, site_id))
                        updates += 1
                        print(f"  ✓ {title[:35]:35s} {site_url[55:]:30s} -> {new_site_url[55:]}")
                        content_site_updates += 1
                    else:
                        print(f"  = {title[:35]:35s} (already correct)")
                else:
                    print(f"  ✗ VERIFY FAILED: {title[:35]:35s} {new_site_url[55:]} ({r.status_code})")
            except Exception as e:
                print(f"  ✗ VERIFY ERR: {title[:35]:35s} {str(e)[:30]}")
    else:
        # No episode with /film/ URL
        # Check if site URL works as-is
        import httpx
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        try:
            r = httpx.get(site_url, headers={'User-Agent': UA}, follow_redirects=True, timeout=10)
            if r.status_code == 200:
                print(f"  SITE OK: {title[:35]:35s} {site_url[55:]}")
            else:
                print(f"  SITE BROKEN: {title[:35]:35s} {site_url[55:]} ({r.status_code})")
        except Exception as e:
            print(f"  SITE ERR: {title[:35]:35s} {str(e)[:30]}")

db.commit()
print(f"\nGüncellenen site URL: {updates}")
print(f"Kontrol edilen content: {content_site_updates}")

# Also check: are there site URLs that are already correct?
cur.execute("""
    SELECT s.site_url 
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_url LIKE '%hdfilmcehennemi%'
    AND s.site_url NOT LIKE '%.nl/%'
    LIMIT 5
""")
print("\nSite URL'leri son durum:")
for row in cur.fetchall():
    print(f"  {row[0][:70]}")

db.close()
