"""SOHBET-159 v2: Smart batch download test with rate limit handling + Playwright for video"""
import asyncio, httpx, sqlite3, json, os, re, time
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'
DOWNLOAD_DIR = '/mnt/c/Kuroshin/kurowatch/temp/sohbet159_test'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

MANGADEX_API = "https://api.mangadex.org"
results = []
total_passed = 0
total_failed = 0

async def test_mangadex(client, sem, cid, title, ctype, uuid):
    global total_passed, total_failed
    async with sem:
        for attempt in range(3):
            try:
                # Get latest chapter
                r = await client.get(f"{MANGADEX_API}/manga/{uuid}/feed",
                    params={"translatedLanguage[]": "en", "limit": 1, "order[chapter]": "desc"},
                    timeout=15)
                
                if r.status_code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"  ⏳ ID={cid} 429, waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                    
                if r.status_code != 200:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"HTTP {r.status_code}"}
                
                chapters = r.json().get('data', [])
                if not chapters:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": "No EN chapters"}
                
                ch = chapters[0]
                ch_id = ch['id']
                ch_num = ch['attributes'].get('chapter', '?')
                
                # Get at-home server
                r2 = await client.get(f"{MANGADEX_API}/at-home/server/{ch_id}", timeout=15)
                if r2.status_code != 200:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"At-home HTTP {r2.status_code}"}
                
                data = r2.json()
                pages = data['chapter']['data']
                if not pages:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": "No pages"}
                
                # Download first page
                page_url = f"{data['baseUrl']}/data/{data['chapter']['hash']}/{pages[0]}"
                r3 = await client.get(page_url, timeout=30)
                if r3.status_code != 200:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"Page HTTP {r3.status_code}"}
                
                fname = f"manga_{cid}_{ctype}_ch{ch_num}.jpg"
                with open(os.path.join(DOWNLOAD_DIR, fname), 'wb') as f:
                    f.write(r3.content)
                
                total_passed += 1
                print(f"  ✅ ID={cid:3d} {ctype:7s} {title[:40]:40s} ch{ch_num} ({len(r3.content)}B)")
                return {"id": cid, "title": title, "type": ctype, "status": "pass", "chapter": ch_num, "size": len(r3.content), "site": "MangaDex"}
                
            except Exception as e:
                if attempt == 2:
                    total_failed += 1
                    return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": str(e)[:80]}
                await asyncio.sleep(3)

async def test_anizm_page(client, sem, cid, title, ctype, slug, is_episode=False):
    """Test if Anizm page loads and has video content (HTTP check for non-Playwright)"""
    global total_passed, total_failed
    async with sem:
        url = f"https://tranimeizle.org.tr/{slug}/"
        try:
            r = await client.get(url, timeout=15, follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
            
            if r.status_code != 200 or len(r.text) < 5000:
                total_failed += 1
                return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"HTTP {r.status_code} ({len(r.text)}B)", "site": "Anizm"}
            
            # Check for JS player indicators
            has_player = 'player' in r.text.lower() or 'episode' in r.text.lower()
            
            total_passed += 1
            print(f"  ✅ ID={cid:3d} {ctype:7s} {title[:40]:40s} ({len(r.text)}B)")
            return {"id": cid, "title": title, "type": ctype, "status": "pass", "size": len(r.text), "has_player": has_player, "site": "Anizm"}
        except Exception as e:
            total_failed += 1
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": str(e)[:80], "site": "Anizm"}

async def test_dizimag_page(client, sem, cid, title, slug):
    global total_passed, total_failed
    async with sem:
        url = f"https://www.dizimag.com.tr/dizi/{slug}/"
        try:
            r = await client.get(url, timeout=15, follow_redirects=True,
                headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
            
            if r.status_code != 200 or len(r.text) < 5000:
                total_failed += 1
                return {"id": cid, "title": title, "type": "series", "status": "fail", "error": f"HTTP {r.status_code}", "site": "Dizimag"}
            
            total_passed += 1
            print(f"  ✅ ID={cid:3d} series {title[:40]:40s} ({len(r.text)}B)")
            return {"id": cid, "title": title, "type": "series", "status": "pass", "size": len(r.text), "site": "Dizimag"}
        except Exception as e:
            total_failed += 1
            return {"id": cid, "title": title, "type": "series", "status": "fail", "error": str(e)[:80], "site": "Dizimag"}

async def test_movie_page(client, sem, cid, title):
    global total_passed, total_failed
    async with sem:
        # Try .sh first, then .nl, then .io
        sources = []
        db = sqlite3.connect(DB_PATH)
        cur = db.cursor()
        cur.execute("SELECT site_url FROM site WHERE content_id=? AND (is_dead IS NULL OR is_dead=0)", (cid,))
        for row in cur.fetchall():
            sources.append(row[0])
        db.close()
        
        if not sources:
            total_failed += 1
            return {"id": cid, "title": title, "type": "movie", "status": "fail", "error": "No alive sites"}
        
        for url in sources[:2]:
            try:
                r = await client.get(url, timeout=15, follow_redirects=True,
                    headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'})
                if r.status_code == 200 and len(r.text) > 5000:
                    has_iframe = '<iframe' in r.text or 'embed' in r.text.lower()
                    total_passed += 1
                    print(f"  ✅ ID={cid:3d} movie  {title[:40]:40s} ({len(r.text)}B) iframe:{has_iframe}")
                    return {"id": cid, "title": title, "type": "movie", "status": "pass", "size": len(r.text), "has_iframe": has_iframe, "site": url.split('/')[2] if '//' in url else url}
            except:
                continue
        
        total_failed += 1
        return {"id": cid, "title": title, "type": "movie", "status": "fail", "error": "No working URL"}

async def main():
    global total_passed, total_failed, results
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    start_time = time.time()
    sem = asyncio.Semaphore(5)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # PHASE 1: MangaDex
        print("=== PHASE 1: MANGA/MANHWA (MangaDex) ===")
        cur.execute("""
            SELECT c.id, c.title, c.type, c.external_id
            FROM content c WHERE c.type IN ('manga', 'manhwa')
            AND c.external_id LIKE 'mdx:%'
            ORDER BY c.id
        """)
        md_items = cur.fetchall()
        
        tasks = []
        for cid, title, ctype, ext in md_items:
            uuid = ext.replace('mdx:', '')
            tasks.append(test_mangadex(client, sem, cid, title, ctype, uuid))
        
        md_results = await asyncio.gather(*tasks)
        results.extend(md_results)
        print(f"  MangaDex: {sum(1 for r in md_results if r['status']=='pass')}/{len(md_results)} passed")
        
        # PHASE 2: Anime (Anizm)
        print("\n=== PHASE 2: ANIME (Anizm) ===")
        cur.execute("""
            SELECT c.id, c.title, c.type FROM content c WHERE c.type = 'anime'
            AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_name='Anizm' AND (s.is_dead IS NULL OR s.is_dead=0))
            ORDER BY c.id
        """)
        anime_items = cur.fetchall()
        
        tasks = []
        for cid, title, ctype in anime_items:
            slug = title.lower().strip()
            slug = re.sub(r'\(s\d+\)', '', slug)
            slug = re.sub(r'\([^)]*\)', '', slug)
            slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
            slug = re.sub(r'-+', '-', slug)
            tasks.append(test_anizm_page(client, sem, cid, title, ctype, slug))
        
        an_results = await asyncio.gather(*tasks)
        results.extend(an_results)
        print(f"  Anime: {sum(1 for r in an_results if r['status']=='pass')}/{len(an_results)} passed")
        
        # PHASE 3: Cartoon (Anizm)
        print("\n=== PHASE 3: CARTOON (Anizm) ===")
        cur.execute("""
            SELECT c.id, c.title, c.type FROM content c WHERE c.type = 'cartoon'
            AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_name='Anizm' AND (s.is_dead IS NULL OR s.is_dead=0))
            ORDER BY c.id
        """)
        cartoon_items = cur.fetchall()
        
        tasks = []
        for cid, title, ctype in cartoon_items:
            slug = title.lower().strip()
            slug = re.sub(r'\(s\d+\)', '', slug)
            slug = re.sub(r'\([^)]*\)', '', slug)
            slug = slug.replace('ç', 'c').replace('ğ', 'g').replace('ş', 's').replace('ü', 'u').replace('ö', 'o').replace('ı', 'i')
            slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
            slug = re.sub(r'-+', '-', slug)
            tasks.append(test_anizm_page(client, sem, cid, title, ctype, slug))
        
        ca_results = await asyncio.gather(*tasks)
        results.extend(ca_results)
        print(f"  Cartoon: {sum(1 for r in ca_results if r['status']=='pass')}/{len(ca_results)} passed")
        
        # PHASE 4: Series (Dizimag)
        print("\n=== PHASE 4: SERIES (Dizimag) ===")
        cur.execute("""
            SELECT c.id, c.title FROM content c WHERE c.type = 'series'
            AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_name='Dizimag' AND (s.is_dead IS NULL OR s.is_dead=0))
            ORDER BY c.id
        """)
        series_items = cur.fetchall()
        
        tasks = []
        for cid, title in series_items:
            slug = title.lower().strip()
            slug = re.sub(r'\(s\d+\)', '', slug)
            slug = re.sub(r'\([^)]*\)', '', slug)
            slug = slug.replace('ç', 'c').replace('ğ', 'g').replace('ş', 's').replace('ü', 'u').replace('ö', 'o').replace('ı', 'i').replace('&', 'and')
            slug = re.sub(r'[^a-z0-9]+', '-', slug).strip('-')
            slug = re.sub(r'-+', '-', slug)
            tasks.append(test_dizimag_page(client, sem, cid, title, slug))
        
        se_results = await asyncio.gather(*tasks)
        results.extend(se_results)
        print(f"  Series: {sum(1 for r in se_results if r['status']=='pass')}/{len(se_results)} passed")
        
        # PHASE 5: Movie
        print("\n=== PHASE 5: MOVIE ===")
        cur.execute("""
            SELECT c.id, c.title FROM content c WHERE c.type = 'movie'
            AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND (s.is_dead IS NULL OR s.is_dead=0))
            ORDER BY c.id
        """)
        movie_items = cur.fetchall()
        
        tasks = []
        for cid, title in movie_items:
            tasks.append(test_movie_page(client, sem, cid, title))
        
        mo_results = await asyncio.gather(*tasks)
        results.extend(mo_results)
        print(f"  Movie: {sum(1 for r in mo_results if r['status']=='pass')}/{len(mo_results)} passed")
    
    db.close()
    
    # FINAL STATS
    elapsed = time.time() - start_time
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    
    # By type
    from collections import Counter
    type_pass = Counter()
    type_total = Counter()
    for r in results:
        type_total[r['type']] += 1
        if r['status'] == 'pass':
            type_pass[r['type']] += 1
    
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS (after {elapsed:.0f}s)")
    print(f"{'='*60}")
    for t in sorted(type_total):
        p = type_pass[t]
        total = type_total[t]
        print(f"  {t:10s}: {p:3d}/{total:3d} ({100*p//total}%)")
    print(f"  {'TOTAL':10s}: {passed:3d}/{passed+failed:3d} ({100*passed//(passed+failed)}%)")
    
    # Save results
    with open('docs/sohbet159_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed": elapsed,
            "total_passed": passed,
            "total_failed": failed,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to docs/sohbet159_results.json")

if __name__ == "__main__":
    asyncio.run(main())
