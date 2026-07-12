"""
SOHBET-146: Check if we can access .nl with proper headers,
and explore .now pagination/categories for more movie URLs
"""
import httpx, re, sqlite3

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}
COOKIES = {'cf_clearance': ''}  # try without

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Get all content titles that have hdfilmcehennemi URLs
cur.execute("""
    SELECT DISTINCT c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    ORDER BY c.title
""")
movies = cur.fetchall()
print(f'Total movies to fix: {len(movies)}')

# --- Check if .now has search functionality ---
print('\n--- Checking .now search ---')
import urllib.parse
test_title = 'Esaretin Bedeli'
r = httpx.get(f'https://www.hdfilmcehennemi.now/?s={urllib.parse.quote(test_title)}', 
              headers=HEADERS, follow_redirects=True, timeout=10)
print(f'  Search "{test_title}": {r.status_code} ({len(r.text)} bytes)')
# Find results
results = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now[^"\']+)', r.text)
for res in results[:5]:
    print(f'    {res}')

# --- Check .now year pages ---
print('\n--- Checking .now year/category pages ---')
for year_path in ['/yil/2024-filmleri-izle-3/', '/category/film-izle-2/']:
    r2 = httpx.get(f'https://www.hdfilmcehennemi.now{year_path}', 
                   headers=HEADERS, follow_redirects=True, timeout=10)
    movie_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r2.text)
    print(f'  {year_path}: {r2.status_code}, {len(movie_links)} film links')

# --- Check .nl with different user agents and approach ---
print('\n--- Checking .nl with different methods ---')
test_url = 'https://www.hdfilmcehennemi.nl/boulevard-2026/'

# Method 1: Regular browser UA
r3 = httpx.get(test_url, headers=HEADERS, follow_redirects=True, timeout=10)
print(f'  Method 1 (browser UA): {r3.status_code} ({len(r3.text)} bytes)')
print(f'  First 200 chars: {r3.text[:200]}')

# Method 2: With Accept-Language header
headers2 = {**HEADERS, 'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'}
r4 = httpx.get(test_url, headers=headers2, follow_redirects=True, timeout=10)
print(f'  Method 2 (with lang): {r4.status_code}')

# Method 3: Try GET instead of HEAD (we used HEAD for .now tests, .nl might differ)
r5 = httpx.get('https://www.hdfilmcehennemi.nl/', headers=HEADERS, follow_redirects=True, timeout=10)
print(f'\n  .nl homepage GET: {r5.status_code} ({len(r5.text)} bytes)')
# Check if it has the same structure
if 'cloudflare' in r5.text[:500].lower():
    print('  Detected: Cloudflare challenge page')
elif 'film' in r5.text[:2000]:
    print('  Normal site content detected')
    
# --- Check: can we access .nl movie pages WITHOUT /film/ prefix like the slugs suggest? ---
print('\n--- Trying direct slug on .nl (the slug IS the path) ---')
# .nl slug format: /boulevard-2026/ (no /film/ prefix, no -izle suffix)
# DB format: /esaretin-bedeli-izle/ (has -izle suffix)
# So we need to strip -izle, add proper formatting

# Let me check if .nl even has these classic movies
test_slugs_nl = ['/esaretin-bedeli', '/fight-club', '/the-shawshank-redemption']
for s in test_slugs_nl:
    url = f'https://www.hdfilmcehennemi.nl{s}/'
    r6 = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
    print(f'  [{r6.status_code}] {url}')
    if r6.status_code == 200:
        # Check if it's actually a movie page or a 404 page
        title_match = re.search(r'<title>([^<]+)</title>', r6.text)
        if title_match:
            print(f'    Title: {title_match.group(1)[:60]}')

db.close()
