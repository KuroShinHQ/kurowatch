"""
Comprehensive EP_YOK fixer for all content types (anime, manga, manhwa).

Usage:
  python scripts/fix_all_ep_yok.py            # dry-run (read only)
  python scripts/fix_all_ep_yok.py --apply    # actually write to DB

Strategy:
  1. For all EP_YOK items with a usable site URL → derive episode 1 URL
  2. For items with total_chapters/total_episodes → create all episodes
  3. For items with dead primary site but working alternative → switch primary
  4. For items with only dead sites → report as unrepairable
"""
import sqlite3, re, os, sys, urllib.request, urllib.error, socket

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
DRY_RUN = '--apply' not in sys.argv

if DRY_RUN:
    print("=== DRY RUN MODE — nothing will be written ===")
else:
    print("=== APPLY MODE — DB will be modified ===")

# ── Known site status ──
# Verified working (return 200 or 301)
WORKING_DOMAINS = [
    'tranimaci.com', 'tranimeizle.co', 'tranimeizle.top',
    'merlintoon.com', 'asurascans.com.tr',
    'mangawow.com', 'mangawow.org', 'mangadenizi.com',
    'hayalistic.com.tr', 'hayalistic.blog',
    'ruyamanga.com', 'ruyamanga.net',
    'manga-sehri.net', 'mangasehri.net',
    'ragnarscans.com', 'ragnarscans.net',
    'majorscans.com', 'merlinscans.com',
    'tempestfansub.com', 'uzaymanga.com',
    'golgebahcesi.com', 'turkcemangaoku.com',
    'mangakoleji.com', 'mangatepesi.com',
    'turkmanga.com.tr',
    'w2.thegreatestestatedeveloper.site',
    'arcanescans.com',
]

# Verified dead/offline
DEAD_DOMAINS = [
    'mangaokutr.com',
    'mangatr.net', 'mangatr.me',
    'mangagezgini.com',
    'example.com',
]


def domain_from_url(url):
    m = re.search(r'https?://([^/]+)', url or '')
    return m.group(1).lower() if m else None


def is_working_domain(url):
    d = domain_from_url(url)
    if not d:
        return True  # can't determine, assume yes
    # Handle www prefix
    d = d.removeprefix('www.')
    return any(wd in d for wd in WORKING_DOMAINS)


def is_dead_domain(url):
    d = domain_from_url(url)
    if not d:
        return False
    d = d.removeprefix('www.')
    return any(dd in d for dd in DEAD_DOMAINS)


# ── URL derivation (from fix_tranimeizle_urls.py) ──
def derive_ep_url(site_url, current_ep, target_ep):
    if not site_url or not current_ep or current_ep == target_ep:
        return site_url if current_ep == target_ep else None
    s, t = str(current_ep), str(target_ep)
    priority = [
        (r'-' + re.escape(s) + r'-bolum', f'-{t}-bolum'),
        (r'bolum[/-]' + re.escape(s), f'bolum-{t}'),
        (r'[/-]' + re.escape(s) + r'-bolum', f'/{t}-bolum'),
        (r'chapter[/-]' + re.escape(s), f'chapter-{t}'),
        (r'-' + re.escape(s) + r'$', f'-{t}'),  # fallback: just change last number
    ]
    for pat, rep in priority:
        m = re.search(pat, site_url, re.IGNORECASE)
        if m:
            return site_url[:m.start()] + rep + site_url[m.end():]
    return site_url  # can't derive, use original


def extract_ep_from_url(url):
    patterns = [
        r'-(\d+)-bolum',
        r'bolum[\-](\d+)',
        r'[\-](\d+)[.-]?bolum',
        r'chapter[/-](\d+)',
        r'[/-](\d+)/?$',
    ]
    for pat in patterns:
        m = re.search(pat, url or '', re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


def extract_slug_from_anime_page(url):
    """tranimaci.com/anime/the-red-ranger-...-izle → the-red-ranger-..."""
    m = re.search(r'/anime/(.+?)(?:-izle)?/?$', url, re.IGNORECASE)
    return m.group(1) if m else None


def derive_tranimeizle_url(slug):
    """Convert slug from /anime/slug/ format to /slug-1-bolum-izle format"""
    return f"https://www.tranimaci.com/{slug}-1-bolum-izle"


# ── Connect DB ──
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = OFF")  # allow episode creation

# ── Stats ──
stats = {
    'anime_ok': 0, 'anime_skip': 0,
    'manga_ok': 0, 'manga_skip': 0,
    'manhwa_ok': 0, 'manhwa_skip': 0,
    'game_skip': 0,
    'site_switch': 0,
    'ep_created': 0,
    'ep_updated': 0,
    'dead_primary': 0,
    'no_working_site': 0,
    'need_manual': [],
}

# ── Get all EP_YOK items ──
rows = conn.execute("""
    SELECT c.* FROM content c
    LEFT JOIN episode e ON e.content_id = c.id
    WHERE e.id IS NULL
    ORDER BY c.type, c.title
""").fetchall()

print(f"\nProcessing {len(rows)} EP_YOK items...\n")

for row in rows:
    cid = row['id']
    ctype = row['type']
    title = row['title']
    total_eps = row['total_episodes']
    total_ch = row['total_chapters']

    if ctype == 'game':
        stats['game_skip'] += 1
        continue

    # Get sites for this content
    sites = conn.execute(
        "SELECT id, site_name, site_url, is_primary FROM site WHERE content_id=? ORDER BY is_primary DESC, id",
        (cid,)
    ).fetchall()

    if not sites:
        stats['no_working_site'] += 1
        stats['need_manual'].append(f"#{cid} [{ctype}] {title} — NO SITE")
        continue

    # Strategy for site selection:
    # - For DISPLAY: prefer working site as primary
    # - For URL DERIVATION: use ANY URL that has an extractable ep number
    #   (even dead sites, since their URL format has the ep pattern)

    primary = None
    working_alternatives = []

    for s in sites:
        if s['is_primary']:
            primary = s
        if is_working_domain(s['site_url']):
            working_alternatives.append(s)

    # Find the best URL for episode derivation (needs extractable ep number)
    derive_url = None
    derive_current_ep = None
    for s in sites:
        ep = extract_ep_from_url(s['site_url'])
        if ep:
            derive_url = s['site_url']
            derive_current_ep = ep
            break

    # If primary is dead but we have a working alternative, switch primary for display
    if primary and is_dead_domain(primary['site_url']) and working_alternatives:
        new_primary = working_alternatives[0]
        if DRY_RUN:
            print(f"  [SITE SWITCH] #{cid} [{ctype}] {title}")
            print(f"    {primary['site_name']}: {primary['site_url']} (DEAD)")
            print(f"    → {new_primary['site_name']}: {new_primary['site_url']}")
        else:
            conn.execute("UPDATE site SET is_primary=0 WHERE id=?", (primary['id'],))
            conn.execute("UPDATE site SET is_primary=1 WHERE id=?", (new_primary['id'],))
        primary = new_primary
        stats['site_switch'] += 1
    elif primary and is_dead_domain(primary['site_url']):
        stats['dead_primary'] += 1
    elif not primary and working_alternatives:
        primary = working_alternatives[0]
        if not DRY_RUN:
            conn.execute("UPDATE site SET is_primary=1 WHERE id=?", (primary['id'],))
            stats['site_switch'] += 1

    # Use derivation URL (must have ep number) or fallback to primary
    if not derive_url:
        derive_url = primary['site_url'] if primary else sites[0]['site_url']
        derive_current_ep = extract_ep_from_url(derive_url)

    # If no primary found, use first site
    if not primary and sites:
        primary = sites[0]
        if not DRY_RUN:
            conn.execute("UPDATE site SET is_primary=1 WHERE id=?", (primary['id'],))
            stats['site_switch'] += 1

    site_url = derive_url  # this is the URL used for episode URL derivation

    # ── ANIME ──
    if ctype == 'anime':
        # Check if the URL has a /anime/ prefix (2nd season format)
        anime_slug = extract_slug_from_anime_page(site_url)
        if anime_slug:
            # Convert /anime/slug/ to /slug-1-bolum-izle
            parts = site_url.split('/anime/')
            if len(parts) == 2:
                site_domain = parts[0]
                new_slug = anime_slug.rstrip('/')
                derived_url = f"{site_domain}/{new_slug}-1-bolum-izle"
                if not DRY_RUN:
                    conn.execute("UPDATE site SET site_url=? WHERE id=?", (derived_url, primary['id']))
                site_url = derived_url
                print(f"  [URL FIX] #{cid} [{ctype}] {title}")
                print(f"    /anime/ format → {derived_url}")

        current_ep = extract_ep_from_url(site_url)
        if not current_ep:
            print(f"  [SKIP] #{cid} [{ctype}] {title} — can't extract ep from URL: {site_url}")
            stats['anime_skip'] += 1
            continue

        # Determine episode count (default 1 for movie/unknown, 12 for typical season)
        target_total = total_eps or 1

        # Create episode records
        for ep_num in range(1, target_total + 1):
            ep_url = derive_ep_url(site_url, current_ep, ep_num)
            if not DRY_RUN:
                conn.execute(
                    "INSERT INTO episode (content_id, season, number, url, is_watched, is_new) VALUES (?, 1, ?, ?, 0, 0)",
                    (cid, ep_num, ep_url)
                )
            stats['ep_created'] += 1

        print(f"  [OK] #{cid} [{ctype}] {title} — {target_total} episodes")
        stats['anime_ok'] += 1
        continue

    # ── MANGA / MANHWA ──
    if ctype in ('manga', 'manhwa'):
        current_ep = extract_ep_from_url(site_url)
        if not current_ep:
            print(f"  [SKIP] #{cid} [{ctype}] {title} — can't extract ep from URL: {site_url}")
            stats['manga_skip' if ctype == 'manga' else 'manhwa_skip'] += 1
            continue

        target_total = total_ch or 1  # at least episode 1

        # For mangaokutr/Madara sites: URLs are like /slug-bolum-N/
        # Make sure the pattern works correctly
        for ep_num in range(1, target_total + 1):
            ep_url = derive_ep_url(site_url, current_ep, ep_num)
            if not DRY_RUN:
                conn.execute(
                    "INSERT INTO episode (content_id, season, number, url, is_watched, is_new) VALUES (?, 1, ?, ?, 0, 0)",
                    (cid, ep_num, ep_url)
                )
            stats['ep_created'] += 1

        label = f"[OK] #{cid} [{ctype}] {title} — {target_total} episodes"
        if is_dead_domain(site_url):
            label += " (DEAD SITE — URL will fail)"
            stats['need_manual'].append(f"#{cid} [{ctype}] {title} — DEAD SITE: {site_url}")
        print(f"  {label}")
        if ctype == 'manga':
            stats['manga_ok'] += 1
        else:
            stats['manhwa_ok'] += 1
        continue

# ── Also fix the 3 anime with episode records but null URLs ──
print(f"\n=== Fixing 3 anime with episodes but null URLs ===")
null_ep_rows = conn.execute("""
    SELECT DISTINCT c.id, c.title, c.type
    FROM content c
    JOIN episode e ON e.content_id = c.id AND e.url IS NULL
    WHERE c.id NOT IN (
        SELECT DISTINCT e2.content_id FROM episode e2 WHERE e2.url IS NOT NULL
    )
    AND c.type = 'anime'
""").fetchall()

for row in null_ep_rows:
    cid = row['id']
    title = row['title']
    sites = conn.execute("SELECT site_url FROM site WHERE content_id=? AND is_primary=1", (cid,)).fetchall()
    if not sites:
        sites = conn.execute("SELECT site_url FROM site WHERE content_id=?", (cid,)).fetchall()
    if not sites:
        continue

    site_url = sites[0]['site_url']
    current_ep = extract_ep_from_url(site_url)
    if not current_ep:
        continue

    eps = conn.execute("SELECT id, number FROM episode WHERE content_id=? AND url IS NULL", (cid,)).fetchall()
    for ep in eps:
        ep_url = derive_ep_url(site_url, current_ep, ep['number'])
        if not DRY_RUN:
            conn.execute("UPDATE episode SET url=? WHERE id=?", (ep_url, ep['id']))
        stats['ep_updated'] += 1

    print(f"  [FIX] #{cid} [{row['type']}] {title} — {len(eps)} episode URLs filled")

# ── Commit ──
if not DRY_RUN:
    conn.commit()
    print("\n✓ DB COMMITTED")
else:
    print("\n[DRY RUN] No changes written. Run with --apply to apply.")

conn.close()

# ── Summary ──
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Anime:   {stats['anime_ok']} fixed, {stats['anime_skip']} skipped")
print(f"Manga:   {stats['manga_ok']} fixed, {stats['manga_skip']} skipped")
print(f"Manhwa:  {stats['manhwa_ok']} fixed, {stats['manhwa_skip']} skipped")
print(f"Game:    {stats['game_skip']} skipped (expected)")
print(f"Episodes created: {stats['ep_created']}")
print(f"Episode URLs updated: {stats['ep_updated']}")
print(f"Site switches: {stats['site_switch']}")
print(f"Dead primary sites: {stats['dead_primary']}")
print(f"No working site at all: {stats['no_working_site']}")

if stats['need_manual']:
    print(f"\n⚠ NEED MANUAL FIX ({len(stats['need_manual'])} items):")
    for item in stats['need_manual']:
        print(f"  {item}")
