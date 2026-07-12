"""
SOHBET-146: Kalan 16 bulunamayan film için advanced search
"""
import httpx, re, sqlite3, urllib.parse

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}
SEARCH_URL = 'https://www.hdfilmcehennemi.now/?s={}'
NOW_BASE = 'https://www.hdfilmcehennemi.now'

db = sqlite3.connect(DB_PATH)
cur = db.cursor()

# Not found movies from the migration
not_found = [
    (257, 'Cem Yılmaz Fundamentals'),
    (267, 'Corpse Bride'),
    (310, 'Fetih 1453'),
    (334, 'Gladio'),
    (354, "Howl's Moving Castle (Yürüyen Şato)"),
    (358, 'I Am Legend (Ben Efsaneyim)'),
    (360, 'Ice Age (Buz Devri Serisi)'),
    (418, 'Kurtlar Vadisi Irak'),
    (432, 'Léon: The Professional (Sevginin Gücü)'),
    (442, 'Matrix Serisi'),
    (485, 'Pacific Rim (Pasifik Savaşı Serisi)'),
    (498, 'Real Steel (Çelik Yumruk)'),
    (504, 'Resident Evil Serisi'),
    (607, 'The Scorpion King Serisi'),
    (633, 'Transformers Serisi'),
    (641, 'Undisputed (Yenilmez Serisi)'),
]

def get_page_title(url):
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            return m.group(1).replace('&amp;', '&').replace('&#039;', "'") if m else ''
    except:
        pass
    return ''

def search_multi(terms, title_raw):
    """Try multiple search terms."""
    seen = set()
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        try:
            r = httpx.get(SEARCH_URL.format(urllib.parse.quote(term)),
                          headers=HEADERS, follow_redirects=True, timeout=15)
            if r.status_code != 200:
                continue
            found = re.findall(r'href=["\'](https?://www\.hdfilmcehennemi\.now/film/[^"\']+)', r.text)
            found_unique = list(dict.fromkeys(found))
            for url in found_unique[:5]:
                pt = get_page_title(url)
                if pt:
                    # Check if page title contains any meaningful word from search term
                    for t in terms:
                        if t.lower() in pt.lower():
                            return url, pt
                    # Also check URL path
                    if any(re.sub(r'[^a-z]', '', t.lower()) in url.lower() for t in terms):
                        return url, pt
        except:
            pass
    return None, None

results_found = {}
results_not = []

print("=== Son 16 film için advanced search ===\n")
for cid, title in not_found:
    # Build alternative search terms
    clean = title.split('(')[0].strip()
    alt_terms = [clean]
    
    # Remove "Serisi" suffix for collections
    if 'Serisi' in clean:
        alt_terms.append(clean.replace(' Serisi', '').strip())
    
    # Add English equivalents
    if 'Howl' in clean:
        alt_terms.extend(['Howls Moving Castle', 'Yürüyen Şato'])
    if 'I Am Legend' in clean:
        alt_terms.append('Ben Efsaneyim')
    if 'Ice Age' in clean:
        alt_terms.append('Buz Devri')
    if 'Kurtlar Vadisi' in clean:
        alt_terms.append('Kurtlar Vadisi Irak 2006')
    if 'Léon' in clean:
        alt_terms.extend(['Leon Sevginin Gücü', 'Léon 1994'])
    if 'Matrix' in clean:
        alt_terms.append('Matrix 1999')
    if 'Pacific Rim' in clean:
        alt_terms.append('Pasifik Savaşı')
    if 'Real Steel' in clean:
        alt_terms.append('Çelik Yumruk')
    if 'Resident Evil' in clean:
        alt_terms.extend(['Resident Evil 2002', 'RE'])
    if 'Scorpion King' in clean:
        alt_terms.append('Scorpion King 2002')
    if 'Transformers' in clean:
        alt_terms.append('Transformers 2007')
    if 'Undisputed' in clean:
        alt_terms.extend(['Undisputed Yenilmez', 'Yenilmez 2002'])
    if 'Fetih' in clean:
        alt_terms.append('Fetih 1453 2012')
    if 'Gladio' in clean:
        alt_terms.append('Gladio 2025')
    if 'Cem Yılmaz' in clean:
        alt_terms.append('Cem Yilmaz Fundamentals 2014')
    if 'Corpse Bride' in clean:
        alt_terms.extend(['Corpse Bride 2005', 'Ölü Gelin'])
    
    url, pt = search_multi(alt_terms, title)
    if url:
        results_found[cid] = (title, url, pt)
        print(f"  ✓ {title[:40]:40s} → {url[55:]} ")
        print(f"    Title: {pt[:60]}")
    else:
        results_not.append((cid, title))
        print(f"  ✗ {title[:40]:40s} → hala bulunamadı")

print(f"\n\n=== İkinci turda bulunan: {len(results_found)} ===")
for cid, (title, url, pt) in results_found.items():
    print(f"  {title[:40]:40s} → {url[55:]}")

print(f"\n=== Hala bulunamayan: {len(results_not)} ===")
for cid, title in results_not:
    print(f"  {title[:40]:40s}")

# Check the old DB URLs for the not-found ones
print(f"\n=== Not-found movies' old URLs ===")
for cid, title in results_not:
    cur.execute("SELECT url FROM episode WHERE content_id = ? LIMIT 1", (cid,))
    row = cur.fetchone()
    if row:
        print(f"  {title[:40]:40s} -> {row[0]}")

# For each not-found, try to see if .nl has them or if we can guess .now slug
print(f"\n=== Trying .nl fallback for remaining ===")
for cid, title in results_not:
    slug = re.sub(r'[^a-z0-9]', '-', title.split('(')[0].strip().lower()).strip('-')
    slug = re.sub(r'-+', '-', slug)
    for pattern in [slug, f'{slug}-izle']:
        url = f'https://www.hdfilmcehennemi.nl/{pattern}/'
        try:
            r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
            if r.status_code == 200:
                t = get_page_title(url)
                if t and '404' not in t and 'bulunamad' not in t.lower():
                    print(f"  .nl FOUND: {title[:35]:35s} -> {url}")
                    results_found[cid] = (title, url, t)
                    results_not.remove((cid, title))
                    break
        except:
            pass
    else:
        print(f"  .nl NOT FOUND: {title[:35]:35s}")

# Now verify with current episode URL in DB
print(f"\n=== Current episode URLs after migration ===")
cur.execute("""
    SELECT e.url, c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE e.url LIKE '%hdfilmcehennemi%'
    GROUP BY e.url
    ORDER BY c.title
""")
for url, title in cur.fetchall():
    print(f"  {title[:40]:40s} -> {url[:70]}")

# Count new found
print(f"\n\n=== FINAL: Found {len(results_found)}, Still missing {len(results_not)} ===")
for cid, title in results_not:
    print(f"  MISSING: {title}")

db.close()
