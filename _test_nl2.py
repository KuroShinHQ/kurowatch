"""
SOHBET-146: .nl is working (200)! Just different slug structure.
Let me explore .nl category pages and try to map DB movies to .nl slugs.
"""
import httpx, re, sqlite3

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

db = sqlite3.connect('memory/kurowatch.db')
cur = db.cursor()

# Get all movie titles
cur.execute("""
    SELECT DISTINCT c.title, c.id
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    ORDER BY c.title
""")
movies = {title: cid for title, cid in cur.fetchall()}
print(f'Movies to fix: {len(movies)}')

# --- Explore .nl structure ---
# Check if .nl has a sitemap or category pages
print('\n--- .nl menu/sitemap links ---')
r = httpx.get('https://www.hdfilmcehennemi.nl/', headers=HEADERS, follow_redirects=True, timeout=15)
links = re.findall(r'href=["\']([^"\']+)', r.text)

# Find navigation / menu links
nav_links = set()
for l in links:
    if '.nl/' in l and not any(x in l for x in ['assets/', 'cdn-cgi/', '.png', '.ico', '.css', '.js', '.json', 'wp-']):
        path = l.split('.nl')[-1]
        if path and path.count('/') <= 2 and path != '/':
            nav_links.add(path)

print('Interesting .nl paths:')
for p in sorted(nav_links)[:40]:
    print(f'  {p}')

# --- Check pagination ---
print('\n--- Pagination on .nl category pages ---')
for cat_path in ['/category/film-izle-2/', '/yil/2024-filmleri-izle-3/']:
    url = f'https://www.hdfilmcehennemi.nl{cat_path}'
    r2 = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
    movie_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.nl/[^"\']+)', r2.text)
    actual = [l for l in movie_links if not any(x in l for x in ['assets/', 'cdn-cgi/', 'category/', 'dil/', 'tur/', 'yil/', '.png', '.ico'])]
    print(f'  {cat_path}: {r2.status_code}, {len(actual)} interesting links')
    for l in actual[:5]:
        print(f'    {l}')

# --- Try to access individual pages from .nl to see slug patterns ---
# The .nl slugs from homepage:
nl_slugs = [
    '/28-years-later-the-bone-temple-7',
    '/above-and-below',
    '/adios-buenos-aires-2023',
    '/avatar-fire-and-ash-51',
    '/black-box-flight-298',
    '/boulevard-2026',
    '/bridget-jones-mad-about-the-boy',
    '/facesof-death-2026-3',
    '/girls-like-girls',
    '/give-a-little-beat',
    '/her-private-hell',
    '/ice-skater-2026',
    '/ikka-2026',
    '/insidious-out-of-the-further',
    '/ip-man-kung-fu-legend-2026',
    '/lee-cronin-s-the-mummy-6',
    '/mortal-kombat-ii-2026-4',
    '/nothing-to-lose-hdfc-2026',
    '/obsession-2026-hdfc-31',
    '/one-mile-chapter-one',
    '/passenger-2026-5',
    '/pinocchio-unstrung-1',
    '/rental-family-2',
    '/rise-of-the-conqueror-2026-5',
]

# Try to get title for each
print('\n--- Verifying .nl movie pages work (200) ---')
works = 0
for s in nl_slugs[:10]:
    url = f'https://www.hdfilmcehennemi.nl{s}/'
    r3 = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
    title_match = re.search(r'<title>([^<]+)</title>', r3.text)
    page_title = title_match.group(1) if title_match else 'N/A'
    print(f'  [{r3.status_code}] {page_title[:50]:50s} {url}')
    if r3.status_code == 200:
        works += 1

# That worked! Now let's try to bulk-fetch .nl movie pages
# The .nl slugs follow: /{english-or-turkish-slug}-{year}/
# We need to search for each movie

# Check if .nl has search
print('\n--- .nl search functionality ---')
for title_val in ['Esaretin Bedeli', 'Fight Club', 'Harry Potter']:
    url = f'https://www.hdfilmcehennemi.nl/?s={title_val.replace(" ", "+")}'
    r4 = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
    result_links = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.nl/[^"\']+)', r4.text)
    actual_links = [l for l in result_links if not any(x in l for x in 
                    ['assets/', 'cdn-cgi/', '.png', '.ico', '.css', '.js', '.json', 'wp-', 'category/', 'dil/', 'tur/', 'yil/'])]
    print(f'  Search "{title_val}": {r4.status_code}, {len(actual_links)} results')
    for l in actual_links[:3]:
        print(f'    {l}')

db.close()
