import httpx, re

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# Check .now homepage for movie links
r = httpx.get('https://www.hdfilmcehennemi.now/', headers=HEADERS, follow_redirects=True, timeout=15)
print(f'.now homepage: {r.status_code} ({len(r.text)} bytes)')

# Find actual movie links
links = re.findall(r'href=["\']([^"\']+)', r.text)
movie_links = []
for l in links:
    if '/film/' in l and 'hdfilmcehennemi.now' in l:
        movie_links.append(l)

print(f'\nFilm links on .now ({len(movie_links)}):')
for l in movie_links[:10]:
    print(f'  {l}')

# Also get a sample .now movie page to see the player
if movie_links:
    test_url = movie_links[0]
    print(f'\nFetching sample movie page: {test_url}')
    r2 = httpx.get(test_url, headers=HEADERS, follow_redirects=True, timeout=15)
    print(f'  Status: {r2.status_code}, Size: {len(r2.text)}')
    
    # Find player iframe/src
    srcs = re.findall(r'src=["\'](https?://[^"\']+play[^"\']*)', r2.text)
    for s in srcs[:3]:
        print(f'  Player: {s[:120]}')
    
    # Find iframe sources
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)', r2.text)
    for i in iframes[:3]:
        print(f'  Iframe: {i[:120]}')

# Now check how many .now URLs have /film/ prefix vs direct slug
print('\n\nAnalyzing DB URL patterns...')
import sqlite3
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

cur.execute("""
    SELECT e.url
    FROM episode e
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
""")
db_urls = [r[0] for r in cur.fetchall()]
with_film = [u for u in db_urls if '/film/' in u]
without_film = [u for u in db_urls if '/film/' not in u]
print(f'  URLs with /film/: {len(with_film)}')
print(f'  URLs without /film/: {len(without_film)}')

# Sample comparisons
if without_film:
    print(f'\n  Sample without /film/:')
    for u in without_film[:3]:
        print(f'    {u}')

# Test if adding /film/ prefix fixes them
for u in without_film[:5]:
    parsed = httpx.URL(u)
    # Fix: add /film/ prefix to the path
    new_path = '/film' + parsed.path if not parsed.path.startswith('/film') else parsed.path
    new_url = f'{parsed.scheme}://{parsed.host}{new_path}'
    try:
        r3 = httpx.get(new_url, headers=HEADERS, follow_redirects=True, timeout=10)
        print(f'  [{r3.status_code}] {new_url[:80]}')
    except Exception as e:
        print(f'  [ERR] {new_url[:80]} -> {str(e)[:30]}')

db.close()
