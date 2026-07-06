"""
V3: Test ALL potentially working manga sites for the 60 failed items.

Sites to test:
  - merlintoon.com       (verified working)
  - monomanga.com.tr     (Next.js, 200)
  - mangaoku.com.tr      (Next.js, 200)
  - golgebahcesi.com     (200, has skycdn refs)
  - amangaplanet.com.tr  (200, likely Next.js)
  - uzaymanga.com        (200 homepage, untested ep pages)
"""
import asyncio, sys, os, re, json, httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

FAILED_IDS = [679, 3, 6, 15, 13, 17, 12, 21, 22, 27, 32, 34, 36, 38, 39,
    41, 51, 43, 54, 29, 33, 58, 59, 60, 37, 65, 66, 61, 68, 69, 35, 81,
    85, 71, 76, 72, 93, 84, 90, 78, 88, 30, 40, 28, 47, 50, 57, 63, 46,
    48, 79, 53, 49, 83, 52, 73, 80, 87, 75, 86]

# Domain -> URL pattern for chapter 1
DOMAINS = {
    "merlintoon.com": "/seri/{slug}/bolum-{n}/",
    "monomanga.com.tr": "/manga/{slug}/bolum-{n}",
    "mangaoku.com.tr": "/manga/{slug}/bolum-{n}",
    "golgebahcesi.com": "/manga/{slug}/bolum/{n}",
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

async def check_page(url):
    """Return True if page 200s and is not an empty template"""
    client = await get_http()
    try:
        r = await client.get(url)
        if r.status_code != 200:
            return False
        body = r.text
        # Reject tiny empty pages (like mangatr.net scam: 6.9KB)
        if len(body) < 15000:
            return False
        # Accept pages with manga-related content signals
        signals = [
            ".jpg", ".png", ".webp",                    # image references
            "wp-content/uploads",                        # WordPress/Madara
            "data-src=", "page-break",                   # Madara reader
            "chapter", "bolum", "bölüm",                  # chapter indicators
            "reading-content", "reader-area",             # reader containers
            "__NEXT_DATA__",                              # Next.js data
        ]
        score = sum(1 for s in signals if s.lower() in body.lower())
        if score >= 2:
            return True
        # Even with 1 strong signal, accept if page is substantial
        if score == 1 and len(body) > 30000:
            return True
        return False
    except:
        return False

async def main():
    sem = asyncio.Semaphore(10)
    
    async def check(url):
        async with sem:
            return await check_page(url)
    
    found = []
    not_found = []
    
    for cid in FAILED_IDS:
        row = conn.execute("SELECT type, title, title_tr FROM content WHERE id=?", (cid,)).fetchone()
        if not row: continue
        
        title = row['title']
        title_tr = row['title_tr']
        sites = conn.execute("SELECT site_url FROM site WHERE content_id=?", (cid,)).fetchall()
        
        candidates = [slugify(title)]
        if title_tr:
            candidates.append(slugify(title_tr))
        for s in extract_slugs(sites):
            candidates.append(s)
        seen = set()
        candidates = [x for x in candidates if not (x in seen or seen.add(x))]
        
        print(f"\n#{cid} [{row['type']}] {title[:45]}")
        
        matched = False
        for slug in candidates[:8]:
            for domain, fmt in DOMAINS.items():
                url = f"https://{domain}{fmt.format(slug=slug, n=1)}"
                if await check(url):
                    url2 = f"https://{domain}{fmt.format(slug=slug, n=2)}"
                    if await check(url2):
                        print(f"  ✅ {domain}: {slug} (ep1+ep2 OK)")
                        found.append((cid, title, slug, domain))
                        matched = True
                        break
            if matched:
                break
        
        if not matched:
            print(f"  ❌ No match on any domain")
            not_found.append(cid)
    
    if _HTTP:
        await _HTTP.aclose()
    
    print(f"\n\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Found: {len(found)}")
    print(f"Still failed: {len(not_found)}")
    
    # Group found by domain
    by_domain = {}
    for cid, title, slug, domain in found:
        by_domain.setdefault(domain, []).append((cid, title, slug))
    for domain, items in by_domain.items():
        print(f"\n--- {domain} ({len(items)}) ---")
        for cid, title, slug in items:
            print(f"  #{cid} {title[:45]} -> {slug}")
    
    result = {"found": found, "not_found": not_found}
    with open("rescue_v3_results.json", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

asyncio.run(main())
conn.close()
