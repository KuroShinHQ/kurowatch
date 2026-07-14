"""SOHBET-161: Toplu manga/manhwa site güncelleme — eski Madara sitelerini monomanga'ya taşı"""
import sqlite3, os, re, asyncio, httpx
from urllib.parse import urlparse

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.normpath(os.path.join(script_dir, "..", "..", "memory", "kurowatch.db"))
db = sqlite3.connect(db_path)
db.row_factory = sqlite3.Row
db.execute("PRAGMA journal_mode=WAL")

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

# Known dead Madara domains
DEAD_DOMAINS = [
    'merlintoon.com', 'mangasehri.net', 'mangasehri.com',
    'manga-sehri.net', 'manga-sehri.com', 'mangatr.app',
    'mangawow.com', 'mangawow.org', 'hayalistic.com.tr',
    'ragnarscans.com', 'ragnarscans.net', 'golgebahcesi.com',
    'mangadenizi.com', 'mangaokutr.com', 'turkcemangaoku.com',
    'mangatepesi.com', 'merlinscans.com', 'mangatr.me',
    'turkmanga.com.tr', 'tempestfansub.com', 'ruyamanga2.com',
    'mangakoleji.com', 'mangakeyf.com', 'mangahost.net',
    'okumangatr.com', 'turkmanga.net', 'mangaturk.org',
    'asurascans.com.tr',
]

def is_dead_domain(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lstrip('www.')
        return any(host == d or host.endswith('.' + d) for d in DEAD_DOMAINS)
    except Exception:
        return False

def is_monomanga_url(url: str) -> bool:
    return 'monomanga.com.tr' in url

# Phase 1: Mark all dead domain sites as is_dead=1
print("=== Phase 1: Mark dead sites ===")
marked = 0
for domain in DEAD_DOMAINS:
    cur = db.execute("SELECT id, content_id, site_url FROM site WHERE site_url LIKE ? AND (is_dead IS NULL OR is_dead = 0)", (f'%{domain}%',))
    rows = cur.fetchall()
    for row in rows:
        db.execute("UPDATE site SET is_dead = 1 WHERE id = ?", (row['id'],))
        marked += 1
db.commit()
print(f"  Marked {marked} sites as dead")

# Phase 2: Set monomanga as primary for all manga/manhwa
print("\n=== Phase 2: Set monomanga as primary ===")
cur = db.execute("""
    SELECT c.id, c.title, c.type, s.id as sid, s.site_url
    FROM content c
    JOIN site s ON s.content_id = c.id
    WHERE c.type IN ('manga','manhwa')
      AND s.site_name LIKE '%monomanga%'
      AND (s.is_primary IS NULL OR s.is_primary = 0)
""")
rows = cur.fetchall()
for row in rows:
    # First unset any existing primary
    db.execute("UPDATE site SET is_primary = 0 WHERE content_id = ?", (row['id'],))
    # Set monomanga as primary
    db.execute("UPDATE site SET is_primary = 1 WHERE id = ?", (row['sid'],))
db.commit()
print(f"  Set monomanga as primary for {len(rows)} manga/manhwa")

# Phase 3: Update all manga/manhwa episode URLs to monomanga
print("\n=== Phase 3: Update episode URLs to monomanga ===")
cur = db.execute("""
    SELECT e.id, e.content_id, e.number, e.url, c.title
    FROM episode e
    JOIN content c ON c.id = e.content_id
    WHERE c.type IN ('manga','manhwa')
      AND e.url IS NOT NULL
      AND e.url != ''
""")
rows = cur.fetchall()
updated_eps = 0
skipped_no_mono = 0
skipped_already = 0

for row in rows:
    if is_monomanga_url(row['url']):
        skipped_already += 1
        continue
    
    # Find monomanga URL for this content
    mono_site = db.execute("""
        SELECT site_url FROM site 
        WHERE content_id = ? AND site_name LIKE '%monomanga%'
        LIMIT 1
    """, (row['content_id'],)).fetchone()
    
    if not mono_site:
        skipped_no_mono += 1
        continue
    
    # Extract slug from monomanga URL
    mono_url = mono_site['site_url']
    slug_match = re.search(r'/manga/([^/]+)/', mono_url)
    if not slug_match:
        skipped_no_mono += 1
        continue
    
    slug = slug_match.group(1)
    ch_num = row['number']
    new_url = f"https://monomanga.com.tr/manga/{slug}/bolum-{ch_num}"
    
    db.execute("UPDATE episode SET url = ? WHERE id = ?", (new_url, row['id']))
    updated_eps += 1
    
    if updated_eps % 50 == 0:
        db.commit()
        print(f"  ... {updated_eps} updated")

db.commit()
print(f"  Updated: {updated_eps} episodes")
print(f"  Already monomanga: {skipped_already}")
print(f"  Skipped (no monomanga site): {skipped_no_mono}")

# Phase 4: Also update primary site URL for monomanga entries to proper format
print("\n=== Phase 4: Fix monomanga primary site URLs ===")
cur = db.execute("""
    SELECT s.id, s.site_url, c.title
    FROM site s
    JOIN content c ON c.id = s.content_id
    WHERE s.site_name LIKE '%monomanga%'
      AND s.is_primary = 1
""")
rows = cur.fetchall()
for row in rows:
    # Ensure URL ends with /bolum-1 (chapter format)
    if not row['site_url'].rstrip('/').endswith('/bolum-1'):
        url = row['site_url'].rstrip('/') + '/bolum-1'
        db.execute("UPDATE site SET site_url = ? WHERE id = ?", (url, row['id']))
print(f"  Fixed {len(rows)} primary monomanga URLs")

db.close()

print("\n=== Summary ===")
print(f"  Dead sites marked: {marked}")
print(f"  Primary set to monomanga: {len(rows)}")
print(f"  Episodes updated: {updated_eps}")
print("DONE")
