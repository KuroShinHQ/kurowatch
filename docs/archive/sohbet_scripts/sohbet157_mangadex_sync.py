"""SOHBET-157: MangaDex UUID sync for all manga/manhwa content.
Search by MAL ID first, fallback to title search.
Update external_id = mdx:{uuid} and total_chapters.
"""
import asyncio, httpx, sqlite3, json, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'
MANGADEX_API = "https://api.mangadex.org"

async def search_by_mal_id(client, mal_id, title_fallback):
    """Search MangaDex by MAL ID or title."""
    # Try MAL ID first
    try:
        r = await client.get(f"{MANGADEX_API}/manga", params={"malId": mal_id}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("result") == "ok" and data.get("data") and len(data["data"]) > 0:
                return data["data"][0]["id"], "mal_id"
    except Exception:
        pass
    
    # Fallback to title search
    try:
        r = await client.get(f"{MANGADEX_API}/manga", params={"title": title_fallback, "limit": 5}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("result") == "ok" and data.get("data") and len(data["data"]) > 0:
                # Try exact title match first
                for m in data["data"]:
                    attrs = m.get("attributes", {})
                    title_en = attrs.get("title", {}).get("en", "").lower()
                    alt_titles = [t.get("en", "").lower() for t in attrs.get("altTitles", []) if "en" in t]
                    all_titles = [title_en] + alt_titles
                    search_lower = title_fallback.lower()
                    if search_lower in all_titles or any(search_lower == t for t in all_titles):
                        return m["id"], "exact_title"
                # Return first result if no exact match
                return data["data"][0]["id"], "fuzzy_title"
    except Exception:
        pass
    return None, None

async def get_chapter_count(client, uuid):
    """Get total chapter count for a manga."""
    try:
        r = await client.get(f"{MANGADEX_API}/manga/{uuid}/aggregate", params={"translatedLanguage[]": "en"}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("result") == "ok":
                volumes = data.get("volumes", {})
                total = 0
                for v_id, v_data in volumes.items():
                    chapters = v_data.get("chapters", {})
                    total += len(chapters)
                return total
    except Exception:
        pass
    return None

async def main():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    # Get all manga and manhwa content (excluding those with existing mdx: external_id)
    cur.execute("""
        SELECT c.id, c.title, c.type, c.external_id, c.total_chapters
        FROM content c
        WHERE c.type IN ('manga', 'manhwa')
        ORDER BY c.id
    """)
    all_items = cur.fetchall()
    print(f"Total manga/manhwa: {len(all_items)}")
    
    # Split by external_id coverage
    with_mal = []
    no_mal = []
    already_mdx = []
    for item in all_items:
        ext = item[3] or ""
        if ext.startswith("mdx:"):
            already_mdx.append(item)
        elif ext.startswith("mal:"):
            with_mal.append(item)
        else:
            no_mal.append(item)
    
    print(f"  With mal: {len(with_mal)}")
    print(f"  No external_id: {len(no_mal)}")
    print(f"  Already mdx: {len(already_mdx)}")
    
    # Process in batches to avoid rate limiting
    results = []
    
    async with httpx.AsyncClient(timeout=15) as client:
        # Phase 1: Search by MAL ID
        for idx, item in enumerate(with_mal):
            cid, title, ctype, ext, cur_ch = item
            mal_id = ext.replace("mal:", "")
            
            uuid, method = await search_by_mal_id(client, mal_id, title)
            if uuid:
                ch_count = await get_chapter_count(client, uuid)
                results.append((cid, title, ctype, uuid, method, ch_count, mal_id))
                print(f"  [{idx+1}/{len(with_mal)}] ID={cid} '{title}' -> {uuid[:12]}... ({method}) chapters={ch_count}")
            else:
                print(f"  [{idx+1}/{len(with_mal)}] ID={cid} '{title}' -> NOT FOUND (mal={mal_id})")
            
            if (idx + 1) % 5 == 0:
                await asyncio.sleep(1)
        
        # Phase 2: Title search for items without MAL
        for idx, item in enumerate(no_mal):
            cid, title, ctype, ext, cur_ch = item
            
            uuid, method = await search_by_mal_id(client, None, title)
            if uuid:
                ch_count = await get_chapter_count(client, uuid)
                results.append((cid, title, ctype, uuid, method, ch_count, None))
                print(f"  [no-mal {idx+1}/{len(no_mal)}] ID={cid} '{title}' -> {uuid[:12]}... ({method}) chapters={ch_count}")
            else:
                print(f"  [no-mal {idx+1}/{len(no_mal)}] ID={cid} '{title}' -> NOT FOUND")
            
            if (idx + 1) % 5 == 0:
                await asyncio.sleep(1)
    
    print(f"\n=== RESULTS SUMMARY ===")
    print(f"  Found: {len(results)}/{len(with_mal) + len(no_mal)}")
    with_chapters = sum(1 for r in results if r[5] is not None)
    print(f"  With chapter count: {with_chapters}")
    
    # Phase 3: Update DB
    print(f"\n=== UPDATING DB ===")
    
    # Check which already have alive sites (we won't overwrite primary for these)
    has_primary = set()
    if results:
        ids_str = ','.join(str(r[0]) for r in results)
        cur.execute(f"""
            SELECT s.content_id FROM site s
            WHERE s.content_id IN ({ids_str})
            AND (s.is_dead IS NULL OR s.is_dead = 0)
            AND s.is_primary = 1
        """)
        has_primary = set(r[0] for r in cur.fetchall())
    print(f"  Already have primary alive site: {len(has_primary)} items")
    
    updated = 0
    sites_added = 0
    for r in results:
        cid, title, ctype, uuid, method, ch_count, mal_id = r
        
        # Update external_id and total_chapters
        if ch_count is not None:
            cur.execute("UPDATE content SET external_id=?, total_chapters=?, updated_at=? WHERE id=?", 
                       (f"mdx:{uuid}", ch_count, datetime.utcnow().isoformat(), cid))
        else:
            cur.execute("UPDATE content SET external_id=?, updated_at=? WHERE id=?", 
                       (f"mdx:{uuid}", datetime.utcnow().isoformat(), cid))
        updated += 1
        
        # Add MangaDex site record if no primary alive site exists
        if cid not in has_primary:
            # Check if MangaDex site already exists for this content
            cur.execute("SELECT id FROM site WHERE content_id=? AND site_name='MangaDex'", (cid,))
            if not cur.fetchone():
                site_url = f"https://mangadex.org/title/{uuid}"
                cur.execute("""
                    INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
                    VALUES (?, 'MangaDex', ?, 1, 0)
                """, (cid, site_url))
                sites_added += 1
    
    db.commit()
    print(f"\n  external_id updated: {updated}")
    print(f"  MangaDex sites added: {sites_added}")
    
    # Summary by type
    manga_found = sum(1 for r in results if r[2] == 'manga')
    manhwa_found = sum(1 for r in results if r[2] == 'manhwa')
    print(f"\n  Manga found: {manga_found}/66")
    print(f"  Manhwa found: {manhwa_found}/96")
    
    # Save results to JSON for report
    results_json = []
    for r in results:
        results_json.append({
            "content_id": r[0],
            "title": r[1],
            "type": r[2],
            "uuid": r[3],
            "method": r[4],
            "total_chapters": r[5],
            "mal_id": r[6]
        })
    
    with open('docs/sohbet157_mangadex_results.json', 'w', encoding='utf-8') as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)
    print(f"\n  Results saved to docs/sohbet157_mangadex_results.json")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
