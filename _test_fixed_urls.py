"""
SOHBET-146: Test updated site URLs (new /film/ prefix, English slugs)
"""
import httpx, re

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}

# Test a sample of the fixed site URLs
test_urls = [
    'https://www.hdfilmcehennemi.now/film/3-aptal-2009-izle-2/',
    'https://www.hdfilmcehennemi.now/film/dovus-kulubu-1999-izle-2/',
    'https://www.hdfilmcehennemi.now/film/300/',
    'https://www.hdfilmcehennemi.now/film/esaretin-bedeli/',
    'https://www.hdfilmcehennemi.now/film/up/',
    'https://www.hdfilmcehennemi.now/film/fury/',
    'https://www.hdfilmcehennemi.now/film/gladiator/',
    'https://www.hdfilmcehennemi.now/film/fight-club/',
    'https://www.hdfilmcehennemi.now/film/titanic/',
    'https://www.hdfilmcehennemi.now/film/inception/',
    'https://www.hdfilmcehennemi.now/film/venom/',
    'https://www.hdfilmcehennemi.now/film/the-godfather/',
    'https://www.hdfilmcehennemi.now/film/v-for-vendetta/',
    'https://www.hdfilmcehennemi.now/film/wall-e/',
]

print("Testing fixed site URLs on hdfilmcehennemi.now:")
print("=" * 70)

works = 0
for url in test_urls:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        has_player = bool(re.search(r'(player|iframe|embed|youtube\.com/embed)', r.text, re.I))
        status = '✓' if r.status_code == 200 else '✗'
        title_match = re.search(r'<title>([^<]+)</title>', r.text)
        title = title_match.group(1)[:40] if title_match else ''
        print(f"  [{r.status_code}] {url[45:65]:25s} player={'yes' if has_player else 'no':4s} {title}")
        if r.status_code == 200:
            works += 1
    except Exception as e:
        print(f"  [ERR] {url[45:65]:25s} {str(e)[:30]}")

print(f"\nWorking: {works}/{len(test_urls)}")

# Now test the same URLs WITHOUT /film/ prefix (old style)
print("\n\nTesting old-format site URLs (no /film/ prefix):")
test_old = [
    'https://www.hdfilmcehennemi.now/up-izle/',
    'https://www.hdfilmcehennemi.now/fury-izle/',
    'https://www.hdfilmcehennemi.now/fight-club-izle/',
    'https://www.hdfilmcehennemi.now/esaretin-bedeli-izle/',
]
for url in test_old:
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        print(f"  [{r.status_code}] {url[45:]} ")
    except Exception as e:
        print(f"  [ERR] {url[45:]} {str(e)[:30]}")
