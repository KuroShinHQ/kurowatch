"""
SOHBET-146 — FULL MIGRATION v3
hdfilmcehennemi URL güncellemesi: .now search + doğrulama
"""
import httpx, re, sqlite3, urllib.parse, time
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
HEADERS = {'User-Agent': UA}
SEARCH_URL = 'https://www.hdfilmcehennemi.now/?s={}'
NOW_BASE = 'https://www.hdfilmcehennemi.now'

stats = {'total': 0, 'found_now': 0, 'found_nl': 0, 'not_found': 0,
         'updated_episodes': 0, 'updated_sites': 0}
updated_urls = {}
not_found_list = []

# Alternate names for tricky titles
ALT_NAMES = {
    'Chihiro Gidişi': ['Ruhların Kaçışı', 'Spirited Away', 'Sen to Chihiro no Kamikakushi'],
    'Cem Yılmaz Fundamentals': ['Cem Yılmaz'],
    'Corpse Bride': ['Ölü Gelin', 'Tim Burton Corpse Bride'],
    'Dabbe Serisi': ['Dabbe'],
    'Howl\'s Moving Castle (Yürüyen Şato)': ['Yürüyen Şato', 'Howls Moving Castle'],
    'Batman Serisi (Kara Şövalye ve Tüm Filmler)': ['Batman', 'Kara Şövalye', 'Batman Filmleri'],
    'Harry Potter Serisi': ['Harry Potter'],
    'Ice Age (Buz Devri Serisi)': ['Buz Devri', 'Ice Age'],
    'Yüzüklerin Efendisi Serisi': ['Yüzüklerin Efendisi', 'Lord of the Rings'],
    'Marvel': ['Marvel'],
}

def get_page_title(url):
    try:
        r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
        if r.status_code == 200:
            m = re.search(r'<title>([^<]+)</title>', r.text)
            page_title = m.group(1) if m else ''
            # Clean HTML entities
            page_title = page_title.replace('&amp;', '&').replace('&#039;', "'")
            return page_title
    except:
        pass
    return ''

def title_similar(db_title, page_title):
    if not db_title or not page_title:
        return False
    key = db_title.split('(')[0].strip().lower()
    key_words = set(re.findall(r'[a-z0-9ığüşöç]+', key))
    page_lower = page_title.lower()
    raw_match = any(kw in page_lower for kw in [key, key.replace(' ', '')])
    matches = sum(1 for w in key_words if w in page_lower)
    return raw_match or (len(key_words) > 0 and matches >= max(2, len(key_words) * 0.4))

def search_now(title_raw, retry=0):
    """Search .now. Try multiple search terms."""
    # Build search terms list
    search_terms = [title_raw.split('(')[0].strip()]
    
    # Add alt names
    if title_raw in ALT_NAMES:
        search_terms.extend(ALT_NAMES[title_raw])
    
    # Try removing parenthetical info
    if '(' in title_raw:
        search_terms.append(title_raw.split('(')[0].strip().split(' - ')[0].strip())
    
    seen = set()
    for term in search_terms:
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
                if pt and title_similar(title_raw, pt):
                    return url, 'now'
            
            # No title match among results - return first that returns 200
            for url in found_unique[:3]:
                try:
                    r2 = httpx.head(url, headers=HEADERS, follow_redirects=True, timeout=10)
                    if r2.status_code == 200:
                        return url, 'now_fuzzy'
                except:
                    pass
        except:
            pass
    return None, None

def search_nl(title_raw):
    """Try .nl with slug patterns."""
    slug = re.sub(r'[^a-z0-9]', '-', title_raw.split('(')[0].strip().lower()).strip('-')
    slug = re.sub(r'-+', '-', slug)
    for pattern in [slug, f'{slug}-izle']:
        url = f'https://www.hdfilmcehennemi.nl/{pattern}/'
        try:
            r = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=10)
            if r.status_code == 200:
                t = get_page_title(url)
                if t and '404' not in t and 'bulunamad' not in t.lower():
                    if title_similar(title_raw, t):
                        return url
        except:
            pass
    return None

def main():
    print("=" * 70)
    print("SOHBET-146 — hdfilmcehennemi URL Güncellemesi v3")
    print(f"Başlangıç: {datetime.now().isoformat()}")
    print("=" * 70)
    
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    cur.execute("""
        SELECT DISTINCT c.id, c.title, e.url
        FROM episode e
        JOIN content c ON c.id = e.content_id
        WHERE e.url LIKE '%hdfilmcehennemi%'
        ORDER BY c.title
    """)
    contents = [(cid, title, url) for cid, title, url in cur.fetchall()]
    stats['total'] = len(contents)
    print(f"\nToplam içerik: {stats['total']}")
    
    print(f"\n{'='*70}")
    print("AŞAMA 1: .now search + doğrulama")
    print(f"{'='*70}")
    
    for idx, (cid, title, old_url) in enumerate(contents, 1):
        new_url = None
        source = None
        
        new_url, source = search_now(title)
        
        if not new_url:
            found_nl = search_nl(title)
            if found_nl:
                new_url = found_nl
                source = 'nl'
        
        if new_url:
            updated_urls[old_url] = new_url
            tag = '✓' if source == 'now' else ('~' if source == 'now_fuzzy' else '◎')
            stats['found_now' if source in ('now','now_fuzzy') else 'found_nl'] += 1
            print(f"  [{idx:2d}/{stats['total']}] {tag} {title[:40]:40s} → {new_url[55:]}")
        else:
            stats['not_found'] += 1
            not_found_list.append((cid, title, old_url))
            print(f"  [{idx:2d}/{stats['total']}] ✗ {title[:40]:40s}")
        
        time.sleep(0.2)
    
    # Update episodes
    print(f"\n{'='*70}")
    print("AŞAMA 2: Episode güncelle")
    print(f"{'='*70}")
    for old_url, new_url in updated_urls.items():
        cur.execute("UPDATE episode SET url = ? WHERE url = ?", (new_url, old_url))
        stats['updated_episodes'] += cur.rowcount
    db.commit()
    print(f"  Güncelleme: {stats['updated_episodes']} satır")
    
    # Update sites
    print(f"\n{'='*70}")
    print("AŞAMA 3: Site güncelle")
    print(f"{'='*70}")
    cur.execute("SELECT id, site_url FROM site WHERE site_url LIKE '%hdfilmcehennemi%'")
    for sid, site_url in cur.fetchall():
        new_site_url = site_url.replace('hdfilmcehennemi.now', 'www.hdfilmcehennemi.now')
        if 'www.' not in new_site_url:
            new_site_url = new_site_url.replace('://', '://www.')
        if new_site_url != site_url:
            cur.execute("UPDATE site SET site_url = ? WHERE id = ?", (new_site_url, sid))
            stats['updated_sites'] += cur.rowcount
    db.commit()
    print(f"  Güncelleme: {stats['updated_sites']} satır")
    
    # Not found
    if not_found_list:
        print(f"\n{'='*70}")
        print(f"AŞAMA 4: Bulunamayanlar ({len(not_found_list)})")
        print(f"{'='*70}")
        for cid, title, old_url in not_found_list:
            print(f"  [{cid}] {title[:45]:45s} {old_url[:60]}")
    
    # Summary
    now_count = stats['found_now']
    nl_count = stats['found_nl']
    nf_count = stats['not_found']
    total_found = now_count + nl_count
    pct = total_found / stats['total'] * 100 if stats['total'] > 0 else 0
    
    print(f"\n{'='*70}")
    print(f"ÖZET — {total_found}/{stats['total']} bulundu (%{pct:.1f})")
    print(f"{'='*70}")
    print(f"  .now search ile:        {now_count}")
    print(f"  .nl ile:                {nl_count}")
    print(f"  Hiç bulunamadı:         {nf_count}")
    print(f"  Güncellenen episode:    {stats['updated_episodes']}")
    print(f"  Güncellenen site:       {stats['updated_sites']}")
    
    db.close()
    print(f"\nBitiş: {datetime.now().isoformat()}")
    
    with open('_sohbet146_sonuc.txt', 'w', encoding='utf-8') as f:
        f.write(f"SOHBET-146 Sonuçları\n")
        f.write(f"Bitiş: {datetime.now().isoformat()}\n")
        f.write(f"Bulunan: {total_found}/{stats['total']} ({pct:.1f}%)\n\n")
        f.write("Güncellenen URL'ler:\n")
        for old, new in updated_urls.items():
            f.write(f"  {old} -> {new}\n")
        f.write("\nBulunamayan:\n")
        for cid, title, old in not_found_list:
            f.write(f"  [{cid}] {title}: {old}\n")
    
    print("\nSonuç: _sohbet146_sonuc.txt")
    return stats, not_found_list

if __name__ == '__main__':
    main()
