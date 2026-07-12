import httpx, re, sqlite3

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# Analyze the .nl site structure more deeply
r = httpx.get('https://www.hdfilmcehennemi.nl/', headers=HEADERS, follow_redirects=True, timeout=15)
# Find ALL links
links = re.findall(r'href=["\']([^"\']+)', r.text)
print('Unique path patterns on .nl:')
paths = set()
for l in links:
    if '.nl/' in l:
        p = l.split('.nl')[-1] if '.nl' in l else l
        if '/' in p and not any(x in p for x in ['assets/', 'cdn-cgi', '.png', '.ico', '.css', '.js', '.json']):
            paths.add(p)
for p in sorted(paths)[:30]:
    print(f'  {p}')

# Check .now site structure (works!)
r2 = httpx.get('https://www.hdfilmcehennemi.now/', headers=HEADERS, follow_redirects=True, timeout=15)
links2 = re.findall(r'href=["\']([^"\']+)', r2.text)
print('\nUnique path patterns on .now (select movie links):')
now_movie_links = set()
for l in links2:
    if '.now/' in l and '/film/' in l and not any(x in l for x in ['assets/', 'cdn-cgi', '.png', '.ico']):
        now_movie_links.add(l.split('.now')[-1])
for p in sorted(now_movie_links)[:30]:
    print(f'  {p}')

# Now check: does .now actually work for ALL types of movie pages?
# Let's test the slugs from DB
db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()
cur.execute("""
    SELECT e.url, c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
    LIMIT 30
""")
print('\n\nTesting URLs from DB on .now domain:')
for row in cur.fetchall():
    db_url = row[0]
    title = row[1]
    
    # Clean the URL
    db_url = db_url.replace('https://', 'https://www.')
    parsed = httpx.URL(db_url)
    
    # Test 1: direct slug
    url1 = str(parsed)
    # Test 2: with /film/ prefix
    path = parsed.path
    if not path.startswith('/film/'):
        url2 = f'{parsed.scheme}://{parsed.host}/film{path}'
    else:
        url2 = url1
    
    try:
        r = httpx.get(url2, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200 and '404' not in r.text[:500]:
            status = 'WORKS'
        else:
            status = f'{r.status_code}'
        print(f'  [{status}] {title[:30]:30s} {url2[:70]}')
    except Exception as e:
        print(f'  [ERR] {title[:30]:30s} {str(e)[:30]}')

db.close()
