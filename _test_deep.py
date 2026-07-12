"""
SOHBET-146: Deep analysis of hdfilmcehennemi URL patterns

The problem: DB has 62 unique episode URLs from hdfilmcehennemi.now
but the slug patterns dont match the actual working movie pages.
"""
import httpx, re, sqlite3
from urllib.parse import unquote

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# --- 1. Get ALL movie slugs from .now homepage ---
r = httpx.get('https://www.hdfilmcehennemi.now/', headers=HEADERS, follow_redirects=True, timeout=15)
links = re.findall(r'href=["\']([^"\']+)', r.text)
now_movie_slugs = set()
for l in links:
    if '.now/' in l and '/film/' in l and not any(x in l for x in ['assets/', 'cdn-cgi', '.png', '.ico']):
        slug = l.split('.now')[-1].rstrip('/')
        now_movie_slugs.add(slug)

print(f'.now homepage: {len(now_movie_slugs)} movie slugs found')
for s in sorted(now_movie_slugs)[:20]:
    print(f'  {s}')

# --- 2. Get ALL movie slugs from .nl homepage ---
r2 = httpx.get('https://www.hdfilmcehennemi.nl/', headers=HEADERS, follow_redirects=True, timeout=15)
links2 = re.findall(r'href=["\']([^"\']+)', r2.text)
nl_movie_slugs = set()
for l in links2:
    if '.nl/' in l and not any(x in l for x in ['assets/', 'cdn-cgi/', '.png', '.ico', '.css', '.js', '.json',
                                                  'category/', 'dil/', 'tur/', 'yil/', 'en-cok', 'film-robotu',
                                                  'film-istekleri', 'apk/', 'site.webmanifest']):
        slug = l.split('.nl')[-1].rstrip('/')
        if slug and slug != '' and slug.count('/') <= 1:  # simple paths not deep
            nl_movie_slugs.add(slug)

print(f'\n.nl homepage: {len(nl_movie_slugs)} slugs found')
for s in sorted(nl_movie_slugs)[:30]:
    print(f'  {s}')

# --- 3. Analyze DB slugs ---
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()
cur.execute("""
    SELECT e.url, c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
    ORDER BY c.title
""")
db_entries = cur.fetchall()
db_slugs = {}
for url, title, cid in db_entries:
    parsed = httpx.URL(url.replace('https://', 'https://www.'))
    db_slugs[parsed.path.rstrip('/')] = (title, cid)

print(f'\nDB: {len(db_slugs)} unique movie slugs')

# --- 4. Try .nl with the same slug path ---
print('\n--- Testing DB slugs on .nl domain ---')
for slug, (title, cid) in list(db_slugs.items())[:20]:
    url = f'https://www.hdfilmcehennemi.nl{slug}'
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            print(f'  [200] {title[:35]:35s} {url}')
        else:
            print(f'  [{r.status_code}] {title[:35]:35s} {url}')
    except Exception as e:
        print(f'  [ERR] {title[:35]:35s} {str(e)[:30]}')

# --- 5. Try .nl with stripped slug (remove -izle suffix) ---
print('\n--- Testing modified slugs on .nl ---')
for slug, (title, cid) in list(db_slugs.items())[:10]:
    modified = slug.replace('-izle', '')
    url = f'https://www.hdfilmcehennemi.nl{modified}'
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            print(f'  [200] {title[:35]:35s} {url}')
        else:
            print(f'  [{r.status_code}] {title[:35]:35s} {url}')
    except Exception as e:
        print(f'  [ERR] {title[:35]:35s} {str(e)[:30]}')

# --- 6. Try .now with correct /film/ prefix ---
print('\n--- Testing DB slugs with /film/ prefix on .now ---')
works = 0
fails = 0
for slug, (title, cid) in db_slugs.items():
    url = f'https://www.hdfilmcehennemi.now/film{slug}/'
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200 and '404' not in r.text[:800]:
            works += 1
        else:
            fails += 1
    except:
        fails += 1

print(f'  .now /film/ prefix: {works} works, {fails} fails out of {len(db_slugs)}')

db.close()
