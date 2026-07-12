"""
Quick test: verify title matching and search for 10 sample movies
"""
import httpx, re, sqlite3, urllib.parse

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}
SEARCH_URL = 'https://www.hdfilmcehennemi.now/?s={}'

def get_page_title(url):
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            return m.group(1) if m else None
    except:
        pass
    return None

def title_similar(db_title, page_title):
    if not db_title or not page_title:
        return False
    key = db_title.split('(')[0].strip().lower()
    key_words = set(re.findall(r'[a-z0-9ığüşöç]+', key))
    page_lower = page_title.lower()
    raw_match = key in page_lower
    matches = sum(1 for w in key_words if w in page_lower)
    return raw_match or (len(key_words) > 0 and matches >= max(2, len(key_words) * 0.3))

db = sqlite3.connect(DB_PATH)
cur = db.cursor()
cur.execute("""
    SELECT DISTINCT c.title, c.id, e.url
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    ORDER BY c.title LIMIT 15
""")
rows = cur.fetchall()

print(f"{'Title':<40} {'Search Result':<60} {'Match'}")
print("-"*110)
for title, cid, old_url in rows:
    search_term = title.split('(')[0].strip()
    r = httpx.get(SEARCH_URL.format(urllib.parse.quote(search_term)), 
                  headers=HEADERS, follow_redirects=True, timeout=15)
    found = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r.text)
    found_unique = list(dict.fromkeys(found))
    
    if found_unique:
        url_from_search = found_unique[0]
        pt = get_page_title(url_from_search)
        match = '✓' if (pt and title_similar(title, pt)) else '✗(title mismatch)'
        print(f"{title[:38]:38s} {url_from_search[55:95]:40s} {match}")
        if pt:
            print(f"{'':38s} Page title: {pt[:55]}")
    else:
        print(f"{title[:38]:38s} {'SEARCH FAILED':<40s} ✗")

db.close()
