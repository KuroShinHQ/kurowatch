"""
SOHBET-146: Discover all movie slugs on hdfilmcehennemi.now
and try to match DB movies to correct slugs.
Also try .nl for classic movies.
"""
import httpx, re, sqlite3, urllib.parse

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Get all hdfilm-cehennemi movies
cur.execute("""
    SELECT DISTINCT c.title, c.id, e.url
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    ORDER BY c.title
""")
movies = [(title, cid, url) for title, cid, url in cur.fetchall()]
print(f'Movies in DB: {len(movies)}')
for t, c, u in movies[:5]:
    print(f'  {t[:40]:40s} {u[:60]}')

# --- Check .now sitemap.xml ---
print('\n--- .now sitemap.xml ---')
for sitemap_path in ['/sitemap.xml', '/sitemap_index.xml', '/wp-sitemap.xml', '/sitemap-1.xml']:
    try:
        r = httpx.get(f'https://www.hdfilmcehennemi.now{sitemap_path}', 
                      headers=HEADERS, follow_redirects=True, timeout=10)
        print(f'  {sitemap_path}: {r.status_code} ({len(r.text)} bytes)')
        if r.status_code == 200 and '<?xml' in r.text[:100]:
            # Find all URLs
            urls = re.findall(r'<loc>([^<]+)</loc>', r.text)
            film_urls = [u for u in urls if '/film/' in u]
            print(f'    Total URLs: {len(urls)}, Film URLs: {len(film_urls)}')
            for u in film_urls[:5]:
                print(f'      {u}')
            break
    except Exception as e:
        print(f'  {sitemap_path}: ERR {str(e)[:30]}')

# --- Check .now category pages for more content ---
print('\n--- .now category/pagination discovery ---')
# Try to access .now categories
cat_paths = [
    '/film/',
    '/category/film-izle-2/',
    '/yil/2024-filmleri-izle-3/',
    '/en-cok-begenilen-filmleri-izle-4/',
    '/tavsiye-filmler-izle2/',
]
all_now_movies = set()
for cat in cat_paths:
    r2 = httpx.get(f'https://www.hdfilmcehennemi.now{cat}', 
                   headers=HEADERS, follow_redirects=True, timeout=10)
    film_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r2.text)
    all_now_movies.update(film_links)
    print(f'  {cat}: {r2.status_code}, found {len(film_links)} films (total: {len(all_now_movies)})')

print(f'\nTotal unique film URLs on .now: {len(all_now_movies)}')
for u in sorted(all_now_movies)[:10]:
    print(f'  {u}')

# --- Try to search on .now with different parameters ---
print('\n--- .now search with various titles ---')
search_results = {}
for title_raw, cid, old_url in movies[:20]:
    # Extract slug-part from title for searching
    title_search = title_raw.split('(')[0].strip()
    r3 = httpx.get(f'https://www.hdfilmcehennemi.now/?s={urllib.parse.quote(title_search)}',
                   headers=HEADERS, follow_redirects=True, timeout=10)
    found_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r3.text)
    if found_links:
        search_results[title_raw] = found_links[0]
        print(f'  FOUND: {title_raw[:35]:35s} -> {found_links[0][:60]}')
    else:
        print(f'  NOT FOUND: {title_raw[:35]:35s}')

print(f'\nFound via search: {len(search_results)}/{min(20, len(movies))}')

# --- Try .nl with various classic movie titles ---
print('\n--- .nl - do classic movies exist? ---')
for title_raw, cid, old_url in movies[:20]:
    # Try English-like slug from title
    slug = re.sub(r'[^a-z0-9]', '-', title_raw.split('(')[0].strip().lower()).strip('-')
    for url_try in [
        f'https://www.hdfilmcehennemi.nl/{slug}/',
        f'https://www.hdfilmcehennemi.nl/{slug}-izle/',
    ]:
        try:
            r4 = httpx.get(url_try, headers=HEADERS, follow_redirects=True, timeout=10)
            if r4.status_code == 200:
                title_match = re.search(r'<title>([^<]+)</title>', r4.text)
                page_title = title_match.group(1) if title_match else ''
                if '404' not in page_title and 'bulunamad' not in page_title:
                    print(f'  FOUND: {title_raw[:30]:30s} -> {url_try}')
                    break
        except:
            pass
    else:
        print(f'  NOT FOUND: {title_raw[:30]:30s}')

db.close()
