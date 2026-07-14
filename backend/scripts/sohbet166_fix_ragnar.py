"""SOHBET-166 — Search all manga/manhwa on ragnarscans.net WP REST + update DB."""
import asyncio, httpx, sqlite3, os, json, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Referer": "https://www.google.com/"}
DB = os.path.join("memory", "kurowatch.db")

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    # 1. Get all manga/manhwa with ragnarscans.net site (currently dead)
    cur = db.execute("""
        SELECT c.id, c.title, c.type, c.external_id, c.total_chapters, s.id AS site_id, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE c.type IN ('manga', 'manhwa') AND s.site_url LIKE '%ragnarscans.net%'
        ORDER BY c.id
    """)
    ragnar_contents = [dict(r) for r in cur.fetchall()]
    print(f"Total manga/manhwa with ragnarscans.net: {len(ragnar_contents)}")
    
    # 2. For each, search ragnarscans.net WP REST to find correct slug
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=15) as cl:
        updated = 0
        for m in ragnar_contents:
            title = m["title"]
            # Search WP REST
            queries = [title[:50]]
            # Also try without parenthetical
            paren = re.search(r'\(([^)]+)\)', title)
            if paren:
                queries.append(paren.group(1).strip())
            
            found_url = None
            for q in queries[:2]:
                try:
                    r = await cl.get("https://ragnarscans.net/wp-json/wp/v2/search", 
                        params={"search": q, "per_page": 10}, timeout=12)
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list):
                            for d in data:
                                url = d.get("url", "")
                                if "/manga/" in url and url.endswith("/"):
                                    found_url = url
                                    break
                except:
                    pass
                await asyncio.sleep(0.2)
            
            if found_url:
                # Extract slug from URL: https://ragnarscans.net/manga/{slug}/
                slug = found_url.rstrip("/").split("/manga/")[-1]
                
                # Update site URL to series page
                db.execute("UPDATE site SET site_url=?, is_dead=0, is_primary=1 WHERE id=?", (found_url, m["site_id"]))
                
                # Mark other sites as non-primary
                db.execute("UPDATE site SET is_primary=0 WHERE content_id=? AND id != ?", (m["id"], m["site_id"]))
                
                # Update episode URLs to ragnarscans pattern: /manga/{slug}/bolum-{N}/
                ch_pattern = f"https://ragnarscans.net/manga/{slug}/bolum-{{}}/"
                # Get episode count
                cur2 = db.execute("SELECT number, id FROM episode WHERE content_id=? ORDER BY number", (m["id"],))
                eps = cur2.fetchall()
                for ep in eps:
                    ep_url = ch_pattern.format(ep["number"])
                    db.execute("UPDATE episode SET url=? WHERE id=?", (ep_url, ep["id"]))
                
                updated += 1
                if updated <= 10 or updated % 20 == 0:
                    print(f"  [{updated:3d}] c.id={m['id']:4d} {title[:35]:35s} | slug={slug[:30]} | eps={len(eps)}")
            else:
                # Keep as dead if not found
                pass
        
        db.commit()
        print(f"\nUpdated: {updated}/{len(ragnar_contents)}")
    
    # 3. Also update total_chapters from ragnarscans chapter count
    print("\n=== Update total_chapters from ragnarscans.net ===")
    cur = db.execute("""
        SELECT c.id, c.title, c.total_chapters, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE c.type IN ('manga', 'manhwa') AND s.site_url LIKE '%ragnarscans.net/manga/%'
        AND s.is_primary = 1
        ORDER BY c.id
    """)
    primary_ragnar = [dict(r) for r in cur.fetchall()]
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=15) as cl:
        ch_updated = 0
        for m in primary_ragnar:
            try:
                r = await cl.get(m["site_url"], timeout=12)
                if r.status_code == 200:
                    # Count chapter links: /manga/{slug}/bolum-N/
                    ch_links = re.findall(r'href="(https://ragnarscans\.net/manga/[^"]+/bolum-\d+/)"', r.text)
                    uniq = list(dict.fromkeys(ch_links))
                    if uniq:
                        real_count = len(uniq)
                        if real_count != m["total_chapters"]:
                            db.execute("UPDATE content SET total_chapters=? WHERE id=?", (real_count, m["id"]))
                            ch_updated += 1
                            if ch_updated <= 10:
                                print(f"  c.id={m['id']:4d} {m['title'][:35]:35s} | total_ch {m['total_chapters']} → {real_count}")
            except:
                pass
            await asyncio.sleep(0.2)
    
    db.commit()
    print(f"  total_chapters updated: {ch_updated}")
    
    # 4. Verify
    print("\n=== Verify (target mangas) ===")
    for cid in [152, 198, 680, 137]:
        cur = db.execute("SELECT id, title, total_chapters FROM content WHERE id=?", (cid,))
        c = cur.fetchone()
        if not c:
            continue
        cur2 = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=? ORDER BY is_primary DESC", (cid,))
        sites = cur2.fetchall()
        cur3 = db.execute("SELECT number, url FROM episode WHERE content_id=? ORDER BY number LIMIT 3", (cid,))
        eps = cur3.fetchall()
        print(f"  c.id={cid:4d} {c['title'][:35]:35s} | total_ch={c['total_chapters']}")
        for s in sites[:3]:
            print(f"    site: {s['site_name']:20s} primary={s['is_primary']} dead={s['is_dead']} | {s['site_url'][:60]}")
        for e in eps:
            print(f"    ep#{e['number']}: {e['url'][:70]}")
    
    db.close()
    print("\n=== DONE ===")

asyncio.run(main())
