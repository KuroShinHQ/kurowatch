"""
V2: Use ONLY verified real-content manga sites.
mangawow.org -> /manga/{slug}/bolum-{n}/
merlintoon.com -> /seri/{slug}/bolum-{n}/

Verification: check for images in HTML (not just HTTP 200).
"""
import asyncio, sys, os, re, json, httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Failed items (from mass_ping_test.py)
FAILED_IDS = [
    679, 3, 6, 7, 14, 15, 13, 17, 11, 12, 16, 21, 22, 31,
    27, 32, 26, 34, 36, 38, 39, 41, 51, 43, 54, 45, 29, 33,
    58, 59, 60, 37, 65, 66, 61, 68, 69, 35, 81, 85, 71, 76,
    72, 82, 93, 84, 90, 78, 88,
    30, 40, 28, 47, 50, 57, 63, 46, 48, 79, 53, 49, 83, 52,
    73, 80, 87, 75, 86
]

DOMAINS = {
    "mangawow.org": "/manga/{slug}/bolum-{n}/",
    "merlintoon.com": "/seri/{slug}/bolum-{n}/",
}

def slugify(text):
    s = text.lower().strip()
    tr = str.maketrans("şçğğıöüıŞÇĞĞİÖÜİ", "scggioiuSCGGIOUI")
    s = s.translate(tr)
    s = re.sub(r'[^a-z0-9\- ]', '', s)
    s = re.sub(r'\s+', '-', s).strip('-')
    s = re.sub(r'-+', '-', s)
    return s

def extract_slugs(sites):
    slugs = set()
    for s in sites:
        url = s['site_url']
        for pat in [r'/manga/([^/]+)', r'/seri/([^/]+)']:
            m = re.search(pat, url)
            if m: slugs.add(m.group(1))
        m = re.search(r'\.com?/([^/]+)-bolum', url)
        if m: slugs.add(m.group(1))
    return slugs

_HTTP = None
async def get_http():
    global _HTTP
    if not _HTTP:
        _HTTP = httpx.AsyncClient(timeout=12, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
                     "Accept": "text/html,*/*"})
    return _HTTP

async def check_real(url):
    """Return True if URL serves real manga content (has images)"""
    client = await get_http()
    try:
        r = await client.get(url)
        if r.status_code != 200:
            return False
        body = r.text
        if any(x in body for x in [".jpg", ".png", "wp-content/uploads", "data-src=", "page-break"]):
            return True
        return False
    except:
        return False

async def main():
    sem = asyncio.Semaphore(10)
    
    async def check(url):
        async with sem:
            return await check_real(url)
    
    found = []
    not_found = []
    
    for cid in FAILED_IDS:
        row = conn.execute("SELECT type, title, title_tr FROM content WHERE id=?", (cid,)).fetchone()
        if not row: continue
        
        title = row['title']
        title_tr = row['title_tr']
        sites = conn.execute("SELECT site_url FROM site WHERE content_id=?", (cid,)).fetchall()
        
        # Generate slugs
        candidates = [slugify(title)]
        if title_tr:
            candidates.append(slugify(title_tr))
        for s in extract_slugs(sites):
            candidates.append(s)
        # Remove duplicates preserving order
        seen = set()
        candidates = [x for x in candidates if not (x in seen or seen.add(x))]
        
        print(f"\n#{cid} [{row['type']}] {title[:45]}")
        
        matched = False
        for slug in candidates[:8]:
            for domain, fmt in DOMAINS.items():
                url = f"https://{domain}{fmt.format(slug=slug, n=1)}"
                if await check(url):
                    # ep2 also
                    url2 = f"https://{domain}{fmt.format(slug=slug, n=2)}"
                    if await check(url2):
                        print(f"  ✅ {domain}: {slug} (ep1+ep2 OK, real content)")
                        found.append((cid, title, slug, domain, url))
                        matched = True
                        break
            if matched:
                break
        
        if not matched:
            print(f"  ❌ No match on any domain")
            not_found.append(cid)
    
    # Close
    if _HTTP:
        await _HTTP.aclose()
    
    # Summary
    print(f"\n\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Found on mangawow/merlintoon: {len(found)}")
    print(f"Still failed: {len(not_found)}")
    
    if not_found:
        print(f"\n--- Still Failing ({len(not_found)}) ---")
        for cid in not_found:
            r = conn.execute("SELECT title, type FROM content WHERE id=?", (cid,)).fetchone()
            if r: print(f"  #{cid} [{r['type']}] {r['title'][:50]}")
    
    result = {"found": found, "not_found": not_found}
    with open("rescue_v2_results.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

asyncio.run(main())
conn.close()
