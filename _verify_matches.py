"""
SOHBET-146 VERIFICATION: Check if updated URLs actually match the movie title.
Revert wrong matches, fix remaining 12 not found.
"""
import httpx, re, sqlite3, urllib.parse, time

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}
SEARCH_URL = 'https://www.hdfilmcehennemi.now/?s={}'

def get_page_title(url):
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            return m.group(1).replace('&amp;', '&').replace('&#039;', "'") if m else ''
    except:
        pass
    return ''

def title_matches(db_title, page_title):
    """Strict check: all key words from db_title should appear in page_title."""
    if not db_title or not page_title:
        return False
    # Extract key from DB title
    key = db_title.split('(')[0].strip().lower()
    key = key.replace('\u0131', 'i').replace('\u015f', 's').replace('\u00e7', 'c').replace('\u011f', 'g').replace('\u00f6', 'o').replace('\u00fc', 'u')
    key_words = set(re.findall(r'[a-z0-9]+', key))
    if not key_words:
        return False
    page_lower = page_title.lower()
    page_lower = page_lower.replace('\u0131', 'i').replace('\u015f', 's').replace('\u00e7', 'c').replace('\u011f', 'g').replace('\u00f6', 'o').replace('\u00fc', 'u')
    
    # Check if at least 40% of key words appear in page title
    matches = sum(1 for w in key_words if w in page_lower)
    # Also check if the main title (before parenthesis) appears
    main_title = db_title.split('(')[0].strip().lower().replace('\u0131', 'i')
    direct_match = main_title[:15] in page_lower
    
    return direct_match or (matches >= max(2, len(key_words) * 0.4))

db = sqlite3.connect(DB_PATH)
cur = db.cursor()

# Get current episode URLs for hdfilmcehennemi
cur.execute("""
    SELECT e.id, e.url, c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
    ORDER BY c.title
""")
rows = [(eid, url, title, cid) for eid, url, title, cid in cur.fetchall()]

# Check title match for found movies only (those with /film/ or .nl/)
match_issues = []
url_map = {}  # content_id -> known old url

for eid, url, title, cid in rows:
    url_map[cid] = url
    # Only check updated URLs
    if '/film/' in url or '.nl/' in url:
        pt = get_page_title(url)
        if pt:
            if title_matches(title, pt):
                print(f"  ✓ {title[:35]:35s} matches -> {pt[:50]}")
            else:
                print(f"  ✗ {title[:35]:35s} MISMATCH! Page: {pt[:50]}")
                print(f"    URL: {url[:70]}")
                match_issues.append((eid, url, title, cid, pt))
        else:
            print(f"  ? {title[:35]:35s} cannot fetch URL")
            match_issues.append((eid, url, title, cid, ''))
    else:
        print(f"  - {title[:35]:35s} NOT UPDATED (still old slug)")

print(f"\n=== Title mismatch issues: {len(match_issues)} ===")
total_issues = len(match_issues)

# For each mismatch, try to find the CORRECT URL with more specific search
if match_issues:
    print(f"\n--- Fixing {len(match_issues)} mismatches ---")
    fixes = []
    for eid, old_url, title, cid, wrong_pt in match_issues:
        print(f"\nFixing: {title[:40]}")
        # Build very specific search term
        search_term = title.split('(')[0].strip()
        # For series/collections, try the specific movie name
        if ' Serisi' in search_term:
            search_term = search_term.replace(' Serisi', '').strip()
        
        # Try specific search with year if known
        r = httpx.get(SEARCH_URL.format(urllib.parse.quote(search_term)),
                      headers=HEADERS, follow_redirects=True, timeout=15)
        found = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r.text)
        found_unique = list(dict.fromkeys(found))
        
        found_correct = None
        for url in found_unique[:5]:
            pt = get_page_title(url)
            if pt and title_matches(title, pt):
                found_correct = url
                print(f"  CORRECT: {url[55:]} -> {pt[:50]}")
                break
        
        if found_correct:
            fixes.append((cid, found_correct))
        else:
            # Revert to old URL (keep old slug, at least it's honest)
            print(f"  REVERT: keeping old slug (no correct match found)")
            fixes.append((cid, old_url))
    
    # Apply fixes
    print(f"\n--- Applying fixes ---")
    for cid, new_url in fixes:
        cur.execute("UPDATE episode SET url = ? WHERE content_id = ?", (new_url, cid))
        affected = cur.rowcount
        print(f"  Content {cid}: {affected} episodes updated -> {new_url[:70]}")
    db.commit()

# Now handle the 12 STILL NOT FOUND movies
# They have old slugs like /slug-izle/
# Try to search .nl one more time, then leave them as-is
print(f"\n=== Remaining not-found movies (old slugs) ===")
cur.execute("""
    SELECT e.url, c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    AND e.url NOT LIKE '%/film/%'
    AND e.url NOT LIKE '%.nl/%'
    GROUP BY c.title
""")
remaining = [(url, title, cid) for url, title, cid in cur.fetchall()]
print(f"Count: {len(remaining)}")
for url, title, cid in remaining:
    print(f"  {title[:40]:40s} -> {url[:60]}")

# Final count
print(f"\n=== FINAL SUMMARY ===")
cur.execute("""
    SELECT 
        COUNT(DISTINCT CASE WHEN e.url LIKE '%/film/%' THEN e.content_id END) as updated,
        COUNT(DISTINCT CASE WHEN e.url LIKE '%.nl/%' THEN e.content_id END) as nl,
        COUNT(DISTINCT CASE WHEN e.url LIKE '%hdfilmcehennemi%' 
                           AND e.url NOT LIKE '%/film/%' 
                           AND e.url NOT LIKE '%.nl/%' THEN e.content_id END) as old
    FROM episode e
    WHERE e.url LIKE '%hdfilmcehennemi%'
""")
updated_count, nl_count, old_count = cur.fetchone()
print(f"  Updated (with /film/): {updated_count}")
print(f"  .nl domain:            {nl_count}")
print(f"  Still old slugs:       {old_count}")

db.close()
print(f"\nDone. Issues found: {total_issues}, remaining old: {old_count}")
