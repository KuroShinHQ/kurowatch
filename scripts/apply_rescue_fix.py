"""
Apply rescue results to DB:
1. Add mangatr.net as site record (primary)
2. Regenerate episode URLs using mangatr.net URL format
"""
import sqlite3, os, re, sys, json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
DRY_RUN = '--apply' not in sys.argv

if DRY_RUN:
    print("=== DRY RUN ===")
else:
    print("=== APPLY MODE ===")

# Load rescue results
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rescue_results.json")) as f:
        results = json.load(f)
except:
    print("ERROR: run rescue_failed_urls.py first")
    sys.exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def derive_ep_urls(base_url, current_ep, target_total):
    """Generate episode URLs from a base URL with known ep number pattern"""
    if not base_url or not current_ep:
        return []
    urls = []
    for n in range(1, target_total + 1):
        s, t = str(current_ep), str(n)
        priority = [
            (r'-' + re.escape(s) + r'-bolum', f'-{t}-bolum'),
            (r'bolum[/-]' + re.escape(s), f'bolum-{t}'),
            (r'[/-]' + re.escape(s) + r'-bolum', f'/{t}-bolum'),
            (r'chapter[/-]' + re.escape(s), f'chapter-{t}'),
            (r'/' + re.escape(s) + r'/?$', f'/{t}/'),
        ]
        found = False
        for pat, rep in priority:
            m = re.search(pat, base_url, re.IGNORECASE)
            if m:
                urls.append(base_url[:m.start()] + rep + base_url[m.end():])
                found = True
                break
        if not found:
            urls.append(base_url)
    return urls

def extract_ep_from_url(url):
    patterns = [
        r'-(\d+)-bolum', r'bolum[\-](\d+)',
        r'[\-](\d+)[.-]?bolum', r'chapter[/-](\d+)',
        r'[/-](\d+)/?$',
    ]
    for pat in patterns:
        m = re.search(pat, url or '', re.IGNORECASE)
        if m:
            try: return int(m.group(1))
            except: pass
    return None

fixed_count = 0
for cid, title, ep1_url, domain, slug in results['fixed']:
    # Get content info
    row = conn.execute("SELECT type, total_episodes, total_chapters FROM content WHERE id=?", (cid,)).fetchone()
    if not row:
        continue
    
    ctype = row['type']
    total = row['total_episodes'] if ctype == 'anime' else row['total_chapters'] or 1
    
    current_ep = extract_ep_from_url(ep1_url)
    if not current_ep:
        print(f"  # Skipping #{cid} {title[:30]}: can't extract ep from {ep1_url}")
        continue
    
    # 1. Add mangatr.net as site record (if not exists)
    existing = conn.execute(
        "SELECT id FROM site WHERE content_id=? AND site_name=?", (cid, 'mangatr')
    ).fetchone()
    
    if not existing:
        mangatr_base = f"https://mangatr.net/manga/{slug}/bolum-{current_ep}/"
        if not DRY_RUN:
            conn.execute(
                "INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead) VALUES (?, 'mangatr', ?, 1, 0)",
                (cid, mangatr_base)
            )
            # Mark old primary as dead
            conn.execute(
                "UPDATE site SET is_primary=0, is_dead=1 WHERE content_id=? AND site_name NOT IN ('mangatr')",
                (cid,)
            )
        print(f"  #{cid} [{ctype}] {title[:40]}")
        print(f"    +site mangatr: {mangatr_base}")
        fixed_count += 1
    else:
        print(f"  #{cid} {title[:30]}: mangatr zaten var")
    
    # 2. Delete old episode records and re-create with mangatr URLs
    ep_urls = derive_ep_urls(ep1_url, current_ep, total)
    
    if not DRY_RUN:
        conn.execute("DELETE FROM episode WHERE content_id=?", (cid,))
        for n, url in enumerate(ep_urls, 1):
            conn.execute(
                "INSERT INTO episode (content_id, season, number, url, is_watched, is_new) VALUES (?, 1, ?, ?, 0, 0)",
                (cid, n, url)
            )
    print(f"    {len(ep_urls)} episode URL (ep1={ep1_url[:60]})")

if not DRY_RUN:
    conn.commit()
    print(f"\n✓ DB COMMITTED — {fixed_count} items fixed")
else:
    print(f"\n[DRY RUN] {fixed_count} items ready. Run --apply to write.")

conn.close()
