"""
SOHBET-146 FIX 2: Kalan hdfilmcehennemi.now hataları için site entry düzeltmesi
"""
import sqlite3, httpx, re

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

db = sqlite3.connect(DB_PATH)
cur = db.cursor()

# Get all content IDs with hdfilmcehennemi.now sites that are still broken
# First, find which content has the issue
cur.execute("""
    SELECT c.id, c.title, COUNT(*) as site_count
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE s.site_url LIKE '%hdfilmcehennemi.now%'
    GROUP BY c.id
    HAVING site_count > 1
    ORDER BY c.title
""")
multi_site = cur.fetchall()
print(f"Content with multiple hdfilmcehennemi site entries: {len(multi_site)}")
for cid, title, cnt in multi_site:
    print(f"  [{cid}] {title[:40]:40s} ({cnt} entries)")

# Let's see what the duplicate entries look like
print("\nSample multi-site entries:")
cur.execute("""
    SELECT c.id, c.title, s.id, s.site_url
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE s.site_url LIKE '%hdfilmcehennemi.now%'
    AND c.id IN (SELECT c2.id FROM content c2 
                 JOIN site s2 ON s2.content_id = c2.id 
                 WHERE s2.site_url LIKE '%hdfilmcehennemi.now%'
                 GROUP BY c2.id HAVING COUNT(*) > 1)
    ORDER BY c.title, s.id
""")
samples = cur.fetchall()
current_title = None
for cid, title, sid, url in samples:
    if title != current_title:
        print(f"\n  {title[:40]}:")
        current_title = title
    print(f"    [site_id={sid}] {url[:70]}")

# Now check if content with only 1 hdfilmcehennemi site entry still fails
cur.execute("""
    SELECT c.id, c.title, s.site_url
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE s.site_url LIKE '%hdfilmcehennemi.now%'
    AND c.id IN (SELECT c2.id FROM content c2 
                 JOIN site s2 ON s2.content_id = c2.id 
                 WHERE s2.site_url LIKE '%hdfilmcehennemi.now%'
                 GROUP BY c2.id HAVING COUNT(*) = 1)
    AND s.site_url NOT LIKE '%/film/%'
    ORDER BY c.title
""")
single_broken = cur.fetchall()
print(f"\n\nContent with single hdfilmcehennemi site entry (broken, no /film/): {len(single_broken)}")
for cid, title, url in single_broken:
    print(f"  [{cid}] {title[:40]:40s} {url[:60]}")

# Strategy: For each content with /film/ episode URLs, make sure FIRST site entry matches
# Delete duplicate hdfilmcehennemi entries that match the wrong format
# Update remaining to match the episode URL

print("\n\n=== FIXING: Updating all hdfilmcehennemi site entries to match episode URL ===")
fix_count = 0
delete_count = 0

# Get all content with hdfilmcehennemi episodes that have /film/
cur.execute("""
    SELECT DISTINCT c.id, c.title, e.url
    FROM content c
    JOIN episode e ON e.content_id = c.id
    WHERE e.url LIKE '%hdfilmcehennemi%' AND e.url LIKE '%/film/%'
    ORDER BY c.title
""")
content_with_film = cur.fetchall()

for cid, title, ep_url in content_with_film:
    # Get hdfilmcehennemi site entries for this content
    cur.execute("""
        SELECT id, site_url FROM site 
        WHERE content_id = ? AND site_url LIKE '%hdfilmcehennemi%'
        ORDER BY id
    """, (cid,))
    site_entries = cur.fetchall()
    
    if len(site_entries) <= 1:
        continue  # already handled
    
    # Extract the correct /film/ slug from episode URL
    match = re.search(r'(/film/[^/]+/)', ep_url)
    if not match:
        continue
    
    correct_path = match.group(1)
    correct_slug = correct_path.rstrip('/').split('/')[-1]
    correct_url = f'https://www.hdfilmcehennemi.now{correct_path}'
    
    # Check if any site entry already has this correct URL
    has_correct = any(correct_url == s[1] for s in site_entries)
    
    if not has_correct:
        # Update the FIRST site entry to the correct URL
        first_id = site_entries[0][0]
        cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (correct_url, first_id))
        fix_count += 1
        print(f"  UPDATED [{cid}] {title[:35]:35s} entry={first_id} -> {correct_url[55:]}")
    
    # Delete other hdfilmcehennemi entries that don't match the correct slug
    for sid, surl in site_entries:
        if surl == correct_url:
            continue  # keep the correct one
        # If this is a hdfilmcehennemi entry with different URL, delete it
        # (only if it's not the only entry)
        if 'hdfilmcehennemi.now' in surl or 'hdfilmcehennemi.nl' in surl:
            cur.execute("DELETE FROM site WHERE id = ?", (sid,))
            delete_count += 1
            print(f"  DELETED [{cid}] {title[:35]:35s} entry={sid} ({surl[55:]:25s})")

db.commit()
print(f"\nGüncellenen: {fix_count}, Silinen: {delete_count}")

# Final check: how many hdfilmcehennemi sites remain?
cur.execute("SELECT COUNT(*) FROM site WHERE site_url LIKE '%hdfilmcehennemi.now%'")
remaining = cur.fetchone()[0]
print(f"Kalan hdfilmcehennemi.now site entry: {remaining}")

db.close()
