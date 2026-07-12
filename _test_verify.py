"""
SOHBET-146: Verify .now movie pages actually have players,
then build the full migration script.
"""
import httpx, re, sqlite3, urllib.parse

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# --- First verify: search-found movies have working players ---
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Get movie titles
cur.execute("""
    SELECT DISTINCT c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    ORDER BY c.title
""")
all_titles = [r[0] for r in cur.fetchall()]

# Test search on .now for first 10, check if page has player
print("=== Verifying .now movie pages have players ===")
verified = 0
for title in all_titles[:10]:
    search_term = title.split('(')[0].strip()
    r = httpx.get(f'https://www.hdfilmcehennemi.now/?s={urllib.parse.quote(search_term)}',
                  headers=HEADERS, follow_redirects=True, timeout=10)
    found = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r.text)
    
    if found:
        movie_url = found[0]
        # Fetch the movie page
        r2 = httpx.get(movie_url, headers=HEADERS, follow_redirects=True, timeout=10)
        page_size = len(r2.text)
        title_match = re.search(r'<title>([^<]+)</title>', r2.text)
        page_title = title_match.group(1) if title_match else 'N/A'
        
        # Check for player iframe/src
        has_iframe = bool(re.search(r'<iframe[^>]+src=["\']', r2.text))
        has_player = bool(re.search(r'(player|embed|watch|video|1080p|720p)', r2.text, re.I))
        
        # Also check for alternatives: maybe the player is loaded in an iframe
        iframe_srcs = re.findall(r'<iframe[^>]+src=["\']([^"\']+)', r2.text)
        alt_srcs = re.findall(r'src=["\'](https?://[^"\']+play[^"\']*)', r2.text)
        
        status = 'OK' if (has_iframe or has_player) else 'NO_PLAYER'
        if status == 'OK':
            verified += 1
        
        print(f'  [{status}] {title[:35]:35s} -> {r2.status_code} ({page_size} bytes)')
        print(f'           Title: {page_title[:60]}')
        if iframe_srcs:
            print(f'           Iframe: {iframe_srcs[0][:80]}')
        if alt_srcs:
            print(f'           Player: {alt_srcs[0][:80]}')
    else:
        print(f'  [NOSRCH] {title[:35]:35s} -> search returned nothing')

print(f'\nVerified with players: {verified}/{min(10, len(all_titles))}')

# --- Now test: does .now redirect from old slug to new? ---
print('\n=== Testing if .now redirects old slugs ===')
cur.execute("""
    SELECT e.url, c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
    LIMIT 5
""")
for old_url, title in cur.fetchall():
    # Try the old slug directly on .now
    parsed = httpx.URL(old_url.replace('https://', 'https://www.'))
    direct_url = str(parsed)
    r3 = httpx.get(direct_url, headers=HEADERS, follow_redirects=True, timeout=10)
    final_url = str(r3.url)
    print(f'  {title[:35]:35s}')
    print(f'    Old: {direct_url[:70]}')
    print(f'    Res: {r3.status_code} -> {final_url[:70]}')

db.close()
