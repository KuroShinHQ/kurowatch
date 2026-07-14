"""SOHBET-158: Batch verify slugs and add site records for anime/cartoon/series"""
import asyncio, httpx, sqlite3, re, json, sys
sys.setrecursionlimit(10000)
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'

def make_slug(title):
    """Convert title to URL-friendly slug"""
    s = title.lower()
    s = re.sub(r'\(s\d+\)', '', s)  # (S2), (S7) etc.
    s = re.sub(r'\([^)]*\)', '', s)  # Any parenthetical content
    s = s.replace('&', 'and')
    s = s.replace('ç', 'c').replace('ğ', 'g').replace('ş', 's').replace('ü', 'u').replace('ö', 'o').replace('ı', 'i')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    s = re.sub(r'-+', '-', s)
    return s

async def check_slug(client, base_url, slug, label=""):
    url = f"{base_url}/{slug}/"
    try:
        r = await client.get(url, timeout=15, follow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                     'Accept-Language': 'tr-TR,tr;q=0.9'})
        ok = r.status_code == 200 and len(r.text) > 5000
        return ok, r.status_code, len(r.text)
    except Exception as e:
        return False, None, 0

async def try_alt_slugs(client, base_url, title, orig_slug):
    """Try alternative slug patterns when the main one fails"""
    alt_tries = []
    
    # Try without any numbers at end
    s2 = re.sub(r'-\d+$', '', orig_slug)
    if s2 != orig_slug:
        alt_tries.append(s2)
    
    # Try the Japanese/English alt title if available
    # e.g., "Shingeki no Kyojin" for "Attack on Titan"
    title_lower = title.lower()
    
    # Season variations
    season_map = {
        's2': '2-sezon', 's3': '3-sezon', 's4': '4-sezon',
        '2-sezon': '2-sezon', '3-sezon': '3-sezon',
        'second-season': '2-sezon', 'third-season': '3-sezon', 'fourth-season': '4-sezon',
    }
    
    for alt_slug in alt_tries:
        ok, status, size = await check_slug(client, base_url, alt_slug, label=f"alt:{alt_slug}")
        if ok:
            return ok, alt_slug
        await asyncio.sleep(0.2)
    
    return False, orig_slug

async def main():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    # Get all anime, cartoon, series
    cur.execute("""
        SELECT c.id, c.title, c.type
        FROM content c
        WHERE c.type IN ('anime', 'cartoon', 'series')
        AND NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
        ORDER BY c.type, c.id
    """)
    items = cur.fetchall()
    print(f"Total items to process: {len(items)}")
    
    # Group by type
    by_type = {}
    for item in items:
        by_type.setdefault(item[2], []).append(item)
    
    for t, lst in by_type.items():
        print(f"  {t}: {len(lst)}")
    
    # Generate slugs
    slugged = []
    for cid, title, ctype in items:
        slug = make_slug(title)
        slugged.append((cid, title, slug, ctype))
    
    site_config = {
        'anime': {'base': 'https://tranimeizle.org.tr', 'site_name': 'Anizm'},
        'cartoon': {'base': 'https://tranimeizle.org.tr', 'site_name': 'Anizm'},
        'series': {'base': 'https://www.dizimag.com.tr/dizi', 'site_name': 'Dizimag'},
    }
    
    found = 0
    failed = 0
    results = []
    sem = asyncio.Semaphore(10)  # 10 concurrent requests
    
    async with httpx.AsyncClient(timeout=15) as client:
        async def check_one(cid, title, slug, ctype):
            nonlocal found, failed
            config = site_config[ctype]
            
            async with sem:
                ok, status, size = await check_slug(client, config['base'], slug, label=f"{cid}")
                
                if ok:
                    found += 1
                    results.append((cid, ctype, slug, status, size, True))
                    return (cid, slug, True, status, size)
                else:
                    # Try alternative slug
                    alt_ok, alt_slug = await try_alt_slugs(client, config['base'], title, slug)
                    if alt_ok:
                        found += 1
                        results.append((cid, ctype, alt_slug, status, size, True))
                        return (cid, alt_slug, True, status, size)
                    else:
                        failed += 1
                        results.append((cid, ctype, slug, status, size, False))
                        return (cid, slug, False, status, size)
        
        # Process in batches to show progress
        batch_size = 20
        all_found = []
        
        for i in range(0, len(slugged), batch_size):
            batch = slugged[i:i+batch_size]
            tasks = [check_one(cid, title, slug, ctype) for cid, title, slug, ctype in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for cid, slug, ok, status, size in batch_results:
                if ok:
                    all_found.append((cid, slug))
            
            pct = min(100, (i + batch_size) * 100 // len(slugged))
            print(f"  Progress: {min(i+batch_size, len(slugged))}/{len(slugged)} ({pct}%) - found: {found}, failed: {failed}")
            
            await asyncio.sleep(0.5)  # Small delay between batches
    
    print(f"\n=== VERIFICATION RESULTS ===")
    print(f"  Found: {found}/{len(slugged)}")
    print(f"  Failed: {failed}/{len(slugged)}")
    
    # Add site records for verified slugs
    print(f"\n=== ADDING SITE RECORDS ===")
    sites_added = 0
    for cid, slug in all_found:
        # Get content type
        cur.execute("SELECT type FROM content WHERE id=?", (cid,))
        ctype = cur.fetchone()[0]
        config = site_config[ctype]
        
        if ctype in ('anime', 'cartoon'):
            site_url = f"https://tranimeizle.org.tr/{slug}/"
            site_name = "Anizm"
        else:  # series
            site_url = f"https://www.dizimag.com.tr/dizi/{slug}/"
            site_name = "Dizimag"
        
        # Check if site already exists for this content
        cur.execute("SELECT id FROM site WHERE content_id=? AND site_url=?", (cid, site_url))
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
                VALUES (?, ?, ?, 1, 0)
            """, (cid, site_name, site_url))
            sites_added += 1
        
        if sites_added % 50 == 0 and sites_added > 0:
            db.commit()
            print(f"  Committed {sites_added} sites...")
    
    db.commit()
    print(f"  Sites added: {sites_added}")
    
    # Final stats
    print(f"\n=== FINAL ORPHAN COUNT ===")
    cur.execute("""
        SELECT c.type, COUNT(*) FROM content c
        WHERE NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
        GROUP BY c.type
        ORDER BY c.type
    """)
    all_rows = cur.fetchall()
    for r in all_rows:
        cur2 = db.cursor()
        cur2.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],))
        total = cur2.fetchone()[0]
        print(f"  {r[0]:10s}  orphan: {r[1]:3d}/{total}  alive: {total - r[1]}")
    total_orphan = sum(r[1] for r in all_rows)
    total_all = sum(cur.execute("SELECT COUNT(*) FROM content WHERE type=?", (r[0],)).fetchone()[0] for r in all_rows)
    print(f"\n  TOTAL: {total_orphan}/{total_all} orphan ({100-100*total_orphan//total_all}% alive)")
    
    # Save results
    with open('docs/sohbet158_results.json', 'w', encoding='utf-8') as f:
        json.dump([{"content_id": r[0], "type": r[1], "slug": r[2], "status": r[3], "size": r[4], "found": r[5]} for r in results], f, ensure_ascii=False, indent=2)
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
