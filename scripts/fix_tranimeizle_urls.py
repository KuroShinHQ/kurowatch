"""
Tranimeizle bozuk URL'leri duzelt.
 - /anime/{slug}-izle → /{slug}-1-bolum-izle
 - Episode URL'lerini site_url'den yeniden turet
"""
import sqlite3, re, sys

DB = '/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db'
DRY_RUN = '--dry-run' in sys.argv


def extract_slug_from_anime_page(url: str) -> str | None:
    """tranimeizle.top/anime/the-red-ranger-...-izle → the-red-ranger-..."""
    m = re.search(r'/anime/(.+?)(?:-izle)?/?$', url, re.IGNORECASE)
    return m.group(1) if m else None


def derive_ep_url(site_url: str, current_ep: int, target_ep: int) -> str | None:
    if not site_url or not current_ep or current_ep == target_ep:
        return site_url if current_ep == target_ep else None
    s, t = str(current_ep), str(target_ep)
    priority = [
        (r'-' + re.escape(s) + r'-bolum', f'-{t}-bolum'),
        (r'bolum[/-]' + re.escape(s), f'bolum-{t}'),
        (r'[/-]' + re.escape(s) + r'-bolum', f'/{t}-bolum'),
        (r'chapter[/-]' + re.escape(s), f'chapter-{t}'),
    ]
    for pat, rep in priority:
        m = re.search(pat, site_url, re.IGNORECASE)
        if m:
            return site_url[:m.start()] + rep + site_url[m.end():]
    return None


def extract_ep_from_url(url: str) -> int | None:
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


conn = sqlite3.connect(DB)

# --- 1. Bozuk site URL'lerini duzelt ---
bozuk_sites = conn.execute(
    "SELECT id, content_id, site_url FROM site "
    "WHERE site_url LIKE '%tranimeizle%' AND site_url LIKE '%/anime/%'"
).fetchall()

print(f"Bozuk site kaydi: {len(bozuk_sites)}")
for sid, cid, old_url in bozuk_sites:
    slug = extract_slug_from_anime_page(old_url)
    if not slug:
        print(f"  [ATLA] Slug cikarilamadi: {old_url}")
        continue
    domain = re.search(r'(https?://[^/]+)', old_url).group(1)
    new_url = f"{domain}/{slug}-1-bolum-izle"
    print(f"  FIX site id={sid} content={cid}")
    print(f"    {old_url}")
    print(f"    → {new_url}")
    if not DRY_RUN:
        conn.execute("UPDATE site SET site_url=? WHERE id=?", (new_url, sid))

# --- 2. Episode URL'lerini yeniden turet ---
# Tum tranimeizle siteleri al (duzeltilmis dahil)
all_sites = conn.execute(
    "SELECT content_id, site_url FROM site WHERE site_url LIKE '%tranimeizle%'"
).fetchall()

updated = skipped = 0
for cid, site_url in all_sites:
    current_ep = extract_ep_from_url(site_url)
    if not current_ep:
        continue  # site_url'den ep cikarilmiyor, atla

    episodes = conn.execute(
        "SELECT id, number, url FROM episode WHERE content_id=? AND season=1",
        (cid,)
    ).fetchall()

    for eid, num, old_ep_url in episodes:
        if old_ep_url and 'tranimeizle' in old_ep_url:
            continue  # Zaten dogru, dokunma
        new_ep_url = derive_ep_url(site_url, current_ep, num)
        if new_ep_url:
            if not DRY_RUN:
                conn.execute("UPDATE episode SET url=? WHERE id=?", (new_ep_url, eid))
            updated += 1
        else:
            skipped += 1

print(f"\nEpisode URL guncelleme: {updated} guncellendi, {skipped} atlandı")

if not DRY_RUN:
    conn.commit()
    print("Commit tamam.")
else:
    print("DRY RUN — hicbir sey yazilmadi.")

conn.close()
