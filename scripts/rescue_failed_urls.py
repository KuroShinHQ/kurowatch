"""
Rescue failed episode URLs by trying the same content on working domains.
Strategy: same content might have different slug on different sites.
Try slug variations on known-working domains, test ep1+ep2.
"""
import asyncio, sys, os, re, time, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.tools.url_ping import http_ping

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# ── Failed items (from mass_ping_test.py) ──
FAILED_IDS = [
    679, 3, 6, 7, 14, 15, 13, 17, 11, 12, 16, 21, 22, 31,
    27, 32, 26, 34, 36, 38, 39, 41, 51, 43, 54, 45, 29, 33,
    58, 59, 60, 37, 65, 66, 61, 68, 69, 35, 81, 85, 71, 76,
    72, 82, 93, 84, 90, 78, 88,
    30, 40, 28, 47, 50, 57, 63, 46, 48, 79, 53, 49, 83, 52,
    73, 80, 87, 75, 86
]

# ── Working domains with known URL formats ──
DOMAINS = {
    "mangatr.net": "/manga/{slug}/bolum-{n}/",
    "merlintoon.com": "/seri/{slug}/bolum-{n}/",
    "mangadenizi.com": "/manga/{slug}/bolum-{n}/",
}

def slugify(text):
    s = text.lower().strip()
    tr = str.maketrans("şçğğıöüıŞÇĞĞİÖÜİ", "scggioiuSCGGIOUI")
    s = s.translate(tr)
    s = re.sub(r'[^a-z0-9\- ]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    s = re.sub(r'-+', '-', s)
    return s

def extract_slugs_from_sites(sites):
    """Extract slugs from existing site URLs for alternative naming"""
    slugs = set()
    for s in sites:
        url = s['site_url']
        # mangatr.net/manga/SLUG/bolum-N/
        m = re.search(r'/manga/([^/]+)', url)
        if m:
            slugs.add(m.group(1))
        # mangaokutr.com/SLUG-bolum-N/
        m = re.search(r'\.com?/([^/]+)-bolum', url)
        if m:
            slugs.add(m.group(1))
        # merlintoon.com/seri/SLUG/bolum-N/
        m = re.search(r'/seri/([^/]+)', url)
        if m:
            slugs.add(m.group(1))
    return slugs

async def test_url(url, timeout=8.0):
    r = await http_ping(url, timeout)
    return r

async def main():
    fixed = []
    failed = []
    not_tested = []

    sem = asyncio.Semaphore(15)

    async def test_url_sem(url, timeout=8.0):
        async with sem:
            return await test_url(url, timeout)

    for cid in FAILED_IDS:
        row = conn.execute("SELECT id, type, title, title_tr FROM content WHERE id=?", (cid,)).fetchone()
        if not row:
            continue

        title = row['title']
        title_tr = row['title_tr']
        ctype = row['type']
        sites = conn.execute("SELECT site_name, site_url, is_primary FROM site WHERE content_id=?", (cid,)).fetchall()

        # Generate candidate slugs
        candidates = set()
        candidates.add(slugify(title))
        if title_tr:
            candidates.add(slugify(title_tr))
        # Extract from existing site URLs
        for s in extract_slugs_from_sites(sites):
            candidates.add(s)

        print(f"\n#{cid} [{ctype}] {title[:50]}")
        print(f"  Trying {len(candidates)} slug candidates on {len(DOMAINS)} domains...")

        # Try each domain + slug combination
        found = False
        for domain, url_fmt in DOMAINS.items():
            for slug in list(candidates)[:5]:  # max 5 slug variants
                ep1_url = f"https://{domain}{url_fmt.format(slug=slug, n=1)}"
                ep2_url = f"https://{domain}{url_fmt.format(slug=slug, n=2)}"

                r1 = await test_url_sem(ep1_url)
                if not r1.is_ok():
                    continue

                r2 = await test_url_sem(ep2_url)
                if not r2.is_ok():
                    continue

                # BOTH ep1 and ep2 pass!
                print(f"  ✅ FOUND: {ep1_url}")
                print(f"     {ep2_url}")
                fixed.append((cid, title, ep1_url, domain, slug))
                found = True
                break
            if found:
                break

        if not found:
            print(f"  ❌ No working URL found for any slug/domain")
            failed.append(cid)

    # ── Summary ──
    print(f"\n\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Fixed: {len(fixed)}")
    print(f"Still failed: {len(failed)}")

    if fixed:
        print(f"\n--- Working URLs found ({len(fixed)}) ---")
        for cid, title, url, domain, slug in fixed:
            print(f"  #{cid} {title[:40]}")
            print(f"    Domain: {domain}, Slug: {slug}")
            print(f"    URL: {url}")

    if failed:
        print(f"\n--- Still failing ({len(failed)} items) ---")
        for cid in failed:
            row = conn.execute("SELECT title, type FROM content WHERE id=?", (cid,)).fetchone()
            if row:
                print(f"  #{cid} [{row['type']}] {row['title'][:50]}")

    # Save results
    result = {"fixed": fixed, "failed": failed}
    with open("rescue_results.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to rescue_results.json")

asyncio.run(main())
conn.close()
