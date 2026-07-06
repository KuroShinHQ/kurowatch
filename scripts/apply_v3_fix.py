"""
Update DB with V3 findings - schema-corrected version.
"""
import sys, os, re, json, sqlite3

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, "memory", "kurowatch.db")

with open(os.path.join(ROOT, "rescue_v3_results.json")) as f:
    v3 = json.load(f)
with open(os.path.join(ROOT, "rescue_v2_results.json")) as f:
    v2 = json.load(f)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def add_site(content_id, site_name, site_url, is_primary=True):
    exists = cur.execute(
        "SELECT id FROM site WHERE content_id=? AND site_url=?",
        (content_id, site_url)
    ).fetchone()
    if exists:
        return f"EXISTS (id={exists['id']})"
    cur.execute(
        "INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead) VALUES (?, ?, ?, ?, 0)",
        (content_id, site_name, site_url, 1 if is_primary else 0)
    )
    return f"INSERTED (id={cur.lastrowid})"

def get_ep_count(row):
    """Get total episode/chapter count"""
    if row['type'] == 'anime':
        return row['total_episodes'] or 0
    else:
        return row['total_chapters'] or 0

def add_episodes(content_id, base_url, start=1, count=5):
    added = 0
    for n in range(start, start + count):
        ep_url = base_url.format(n=n)
        exists = cur.execute(
            "SELECT id FROM episode WHERE content_id=? AND url=?",
            (content_id, ep_url)
        ).fetchone()
        if not exists:
            cur.execute(
                "INSERT INTO episode (content_id, number, url, is_watched, is_new) VALUES (?, ?, ?, 0, 1)",
                (content_id, n, ep_url)
            )
            added += 1
    return added

# --- Step 1: Add monomanga entries for V3 found items ---
print("=== Adding monomanga.com.tr for V3 found items ===")
mono_added = 0
mono_ep_added = 0

for cid, title, slug, domain in v3["found"]:
    row = cur.execute("SELECT * FROM content WHERE id=?", (cid,)).fetchone()
    if not row:
        print(f"  #{cid} {str(title)[:40]} -> CONTENT NOT FOUND")
        continue
    
    base_url = f"https://monomanga.com.tr/manga/{slug}/bolum-{{n}}"
    result = add_site(cid, "monomanga.com.tr", base_url.format(n=1), True)
    if "INSERTED" in result:
        mono_added += 1
    
    ep_count = get_ep_count(row)
    if ep_count > 0:
        eps = add_episodes(cid, base_url, 1, min(ep_count, 200))
        mono_ep_added += eps
        print(f"  #{cid} {str(row['title'])[:40]} -> {result.split()[0]}, {eps} eps")
    else:
        print(f"  #{cid} {str(row['title'])[:40]} -> {result.split()[0]}, ep_count=0")

# --- Step 2: Replace mangawow.org (403) with monomanga ---
print("\n=== Replacing mangawow.org (403) with monomanga ===")
for item in v2["found"]:
    cid, title, slug, domain, _ = item
    if domain != "mangawow.org":
        continue
    
    row = cur.execute("SELECT * FROM content WHERE id=?", (cid,)).fetchone()
    if not row:
        continue
    
    mono_url = f"https://monomanga.com.tr/manga/{slug}/bolum-1"
    existing = cur.execute(
        "SELECT id FROM site WHERE content_id=? AND site_url=?",
        (cid, mono_url)
    ).fetchone()
    
    if not existing:
        result = add_site(cid, "monomanga.com.tr", mono_url, True)
        base_url = f"https://monomanga.com.tr/manga/{slug}/bolum-{{n}}"
        ep_count = get_ep_count(row)
        eps = add_episodes(cid, base_url, 1, min(ep_count or 1, 200))
        print(f"  #{cid} {str(row['title'])[:40]} -> REPLACED, {eps} eps")
    else:
        print(f"  #{cid} {str(row['title'])[:40]} -> already has monomanga")

# --- Step 3: Verify merlintoon.com items ---
print("\n=== Verifying merlintoon.com items ===")
for item in v2["found"]:
    cid, title, slug, domain, ep1_url = item
    if domain != "merlintoon.com":
        continue
    
    site_row = cur.execute(
        "SELECT id FROM site WHERE content_id=? AND site_url=?",
        (cid, ep1_url)
    ).fetchone()
    if site_row:
        eps_count = cur.execute(
            "SELECT COUNT(*) as c FROM episode WHERE content_id=? AND url LIKE ?",
            (cid, f"https://merlintoon.com%")
        ).fetchone()['c']
        print(f"  #{cid} {str(title)[:40]} -> site={site_row['id']}, {eps_count} eps")
    else:
        row = cur.execute("SELECT * FROM content WHERE id=?", (cid,)).fetchone()
        base_url = f"https://merlintoon.com/seri/{slug}/bolum-{{n}}/"
        add_site(cid, "merlintoon.com", base_url.format(n=1), True)
        ep_count = get_ep_count(row)
        eps = add_episodes(cid, base_url, 1, min(ep_count or 1, 200))
        print(f"  #{cid} {str(title)[:40]} -> ADDED, {eps} eps")

conn.commit()

# Summary
total_mono = cur.execute(
    "SELECT COUNT(*) as c FROM site WHERE site_url LIKE 'https://monomanga.com.tr%'"
).fetchone()['c']
total_sites = cur.execute("SELECT COUNT(*) as c FROM site").fetchone()['c']
total_eps = cur.execute("SELECT COUNT(*) as c FROM episode").fetchone()['c']

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Monomağa sites added: {mono_added}")
print(f"Monomağa episodes added: {mono_ep_added}")
print(f"Total monomanga sites in DB: {total_mono}")
print(f"Total sites in DB: {total_sites}")
print(f"Total episodes in DB: {total_eps}")

conn.close()
