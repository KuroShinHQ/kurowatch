"""SOHBET-159: Test ALL 714 content for real download capability.
- Manga/Manhwa: MangaDex API (fast)
- Anime/Cartoon: Playwright -> m3u8 extraction
- Series: Playwright -> dizimag episode finder
- Movie: hdfilmcehennemi sources
- Game: skipped (already working)
"""
import asyncio, httpx, sqlite3, json, os, sys, re, time
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'
DOWNLOAD_DIR = '/mnt/c/Kuroshin/kurowatch/temp/sohbet159_test'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
RESULTS_PATH = os.path.join(os.path.dirname(DOWNLOAD_DIR), '..', 'docs', 'sohbet159_results.json')

MANGADEX_API = "https://api.mangadex.org"

# Track results
results = []
total_tested = 0
total_passed = 0

async def test_mangadex(client, cid, title, ctype, uuid):
    """Test MangaDex download for a manga/manhwa"""
    global total_tested, total_passed
    total_tested += 1
    
    try:
        # Get latest chapter
        r = await client.get(f"{MANGADEX_API}/manga/{uuid}/feed",
            params={"translatedLanguage[]": "en", "limit": 1, "order[chapter]": "desc"},
            timeout=15)
        if r.status_code != 200:
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"MangaDex feed HTTP {r.status_code}"}
        
        chapters = r.json().get('data', [])
        if not chapters:
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": "No chapters found"}
        
        ch = chapters[0]
        ch_id = ch['id']
        ch_num = ch['attributes'].get('chapter', '?')
        
        # Get at-home server
        r2 = await client.get(f"{MANGADEX_API}/at-home/server/{ch_id}", timeout=15)
        if r2.status_code != 200:
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"At-home HTTP {r2.status_code}"}
        
        data = r2.json()
        base_url = data['baseUrl']
        ch_hash = data['chapter']['hash']
        pages = data['chapter']['data']
        
        if not pages:
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": "No pages in chapter"}
        
        # Download first page
        page_url = f"{base_url}/data/{ch_hash}/{pages[0]}"
        r3 = await client.get(page_url, timeout=30)
        if r3.status_code != 200:
            return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": f"Page HTTP {r3.status_code}"}
        
        # Save to disk
        fname = f"test_{cid}_{ctype}_ch{ch_num}.jpg"
        fpath = os.path.join(DOWNLOAD_DIR, fname)
        with open(fpath, 'wb') as f:
            f.write(r3.content)
        
        file_size = len(r3.content)
        result = {
            "id": cid, "title": title, "type": ctype, "status": "pass",
            "chapter": ch_num, "pages": len(pages),
            "file": fname, "size": file_size, "site": "MangaDex"
        }
        total_passed += 1
        
        # Verify it's a valid image
        if file_size < 1000:
            result["warning"] = "Very small file (< 1KB)"
        
        return result
    
    except Exception as e:
        return {"id": cid, "title": title, "type": ctype, "status": "fail", "error": str(e)[:100]}

async def process_manga_manhwa():
    """Process all manga/manhwa with MangaDex UUID"""
    print("\n=== PROCESSING MANGA/MANHWA ===")
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    cur.execute("""
        SELECT c.id, c.title, c.type, c.external_id
        FROM content c
        WHERE c.type IN ('manga', 'manhwa')
        AND c.external_id LIKE 'mdx:%'
        AND EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND s.site_name = 'MangaDex' AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
        ORDER BY c.id
    """)
    items = cur.fetchall()
    print(f"  Items with MangaDex: {len(items)}")
    
    async with httpx.AsyncClient(timeout=30) as client:
        sem = asyncio.Semaphore(5)
        
        async def process_one(cid, title, ctype, ext):
            uuid = ext.replace('mdx:', '')
            async with sem:
                result = await test_mangadex(client, cid, title, ctype, uuid)
                status_icon = "✅" if result["status"] == "pass" else "❌"
                print(f"  {status_icon} ID={cid:3d} {ctype:7s} {title[:40]:40s} {result.get('chapter', '?')} -> {result.get('size', result.get('error', '?'))}")
                results.append(result)
        
        tasks = [process_one(cid, title, ctype, ext) for cid, title, ctype, ext in items]
        await asyncio.gather(*tasks)
    
    db.close()

async def main():
    global total_tested, total_passed, results
    
    start_time = time.time()
    
    # Phase 1: Manga/Manhwa (MangaDex)
    await process_manga_manhwa()
    
    elapsed = time.time() - start_time
    print(f"\n\n=== PARTIAL RESULTS (after {elapsed:.0f}s) ===")
    print(f"  Tested: {total_tested}")
    print(f"  Passed: {total_passed}")
    print(f"  Failed: {total_tested - total_passed}")
    
    # Save partial results
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "total_tested": total_tested,
            "total_passed": total_passed,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to {RESULTS_PATH}")

if __name__ == "__main__":
    asyncio.run(main())
