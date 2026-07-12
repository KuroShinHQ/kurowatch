"""
Check remaining hdfilmcehennemi.now failures:
Find content where episode URL has /film/ but site URL doesn't
"""
import sqlite3

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Failed hdfilmcehennemi.now content IDs (from report)
failed_ids = [472, 363, 344, 345, 342, 341, 227, 219, 215, 211, 210, 205, 204, 
              641, 334, 354, 418, 498, 603, 633, 607, 360, 499]

print("Checking each failed hdfilmcehennemi.now content:")
for cid in failed_ids:
    cur.execute("""
        SELECT e.url, c.title 
        FROM episode e 
        JOIN content c ON c.id = e.content_id 
        WHERE e.content_id = ? 
        LIMIT 1
    """, (cid,))
    ep = cur.fetchone()
    ep_url = ep[0] if ep else 'NO EPISODE'
    title = ep[1] if ep else '?'
    
    cur.execute("""
        SELECT id, site_url FROM site 
        WHERE content_id = ? AND site_url LIKE '%hdfilmcehennemi%'
    """, (cid,))
    sites = cur.fetchall()
    
    ep_has_film = '/film/' in ep_url
    site_has_film = any('/film/' in s[1] for s in sites)
    
    if ep_has_film and not site_has_film:
        print(f"  [{cid}] {title[:35]:35s} EP has /film/ but SITE doesn't!")
        print(f"    EP: {ep_url[:65]}")
        print(f"    SITE: {sites[0][1][:65] if sites else 'NONE'}")
    elif not ep_has_film and site_has_film:
        print(f"  [{cid}] {title[:35]:35s} EP old format, SITE has /film/ (still 404)")
        print(f"    EP: {ep_url[:65]}")
        if sites:
            print(f"    SITE: {sites[0][1][:65]}")
    elif not ep_has_film and not site_has_film:
        print(f"  [{cid}] {title[:35]:35s} BOTH old format")
        print(f"    EP: {ep_url[:65]}")
    else:
        print(f"  [{cid}] {title[:35]:35s} Both have /film/ - still 404?")
        print(f"    EP: {ep_url[:65]}")
        if sites:
            print(f"    SITE: {sites[0][1][:65]}")

db.close()
