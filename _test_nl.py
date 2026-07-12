import httpx, re

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# .nl homepage
r = httpx.get('https://www.hdfilmcehennemi.nl/', headers=HEADERS, follow_redirects=True, timeout=15)
print(f'.nl homepage: {r.status_code} ({len(r.text)} bytes)')

# Find movie links
links = re.findall(r'href=["\']([^"\']+)', r.text)
movie_links = []
for l in links:
    if '.nl/' in l and ('/film/' in l or 'izle' in l) \
       and not any(x in l for x in ['assets/', 'cdn-cgi', 'wp-', '.png', '.ico', '.js', '.css', '.json', 'favicon']):
        movie_links.append(l)

print(f'\nFound {len(movie_links)} movie/episode links on .nl:')
for l in movie_links[:15]:
    print(f'  {l}')

# Test specific .now slugs on .nl
print('\nTesting .now slugs on .nl domain (GET):')
test_urls = [
    'https://www.hdfilmcehennemi.nl/howls-moving-castle-yuruyen-sato-izle/',
    'https://www.hdfilmcehennemi.nl/doctor-strange-izle/',
    'https://www.hdfilmcehennemi.nl/film/3-aptal-2009-izle-2/',
]
for url in test_urls:
    try:
        r2 = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        print(f'  [{r2.status_code}] {url[:70]}')
        if r2.status_code == 200:
            iframes = re.findall(r'src=["\'](https?://[^"\']+player[^"\']+)', r2.text)
            print(f'    Players: {len(iframes)}')
            for ifr in iframes[:1]:
                print(f'      {ifr[:100]}')
    except Exception as e:
        print(f'  [ERR] {url[:70]} -> {str(e)[:40]}')

# Also test .now directly (some might still work)
print('\nTesting .now domain directly (GET):')
for url in test_urls:
    url_now = url.replace('.nl', '.now')
    try:
        r3 = httpx.get(url_now, headers=HEADERS, follow_redirects=True, timeout=10)
        print(f'  [{r3.status_code}] {url_now[:70]} ({len(r3.text)} bytes)')
    except Exception as e:
        print(f'  [ERR] {url_now[:70]} -> {str(e)[:40]}')
