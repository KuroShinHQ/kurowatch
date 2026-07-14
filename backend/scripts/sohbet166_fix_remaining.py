"""SOHBET-166 — Fix remaining 3 target mangas + fix total_chapters (pagination issue)."""
import asyncio, httpx, sqlite3, os, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Referer": "https://www.google.com/"}
DB = os.path.join("memory", "kurowatch.db")

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    # 1. Search ragnarscans for the 3 missing mangas
    SEARCH_MAP = {
        137: ("After Ten Millennia in Hell", ["after ten millennia", "after-ten-millennia"]),
        152: ("Lout of Count's Family", ["lout of count", "lout-of-count", "trash count"]),
        198: ("Trash of the Count's Family", ["trash of the count", "trash-of-the-count", "lout count"]),
    }
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=15) as cl:
        for cid, (title, queries) in SEARCH_MAP.items():
            print(f"\n=== c.id={cid} {title} ===")
            found_slug = None
            for q in queries:
                try:
                    r = await cl.get("https://ragnarscans.net/wp-json/wp/v2/search", 
                        params={"search": q, "per_page": 10}, timeout=12)
                    if r.status_code == 200:
                        data = r.json()
                        if isinstance(data, list):
                            for d in data:
                                url = d.get("url", "")
                                if "/manga/" in url and url.endswith("/"):
                                    found_slug = url.rstrip("/").split("/manga/")[-1]
                                    print(f"  Found: slug={found_slug} | url={url}")
                                    break
                except:
                    pass
                if found_slug:
                    break
                await asyncio.sleep(0.2)
            
            if found_slug:
                # Mark monomanga dead
                db.execute("UPDATE site SET is_dead=1, is_primary=0 WHERE content_id=? AND site_url LIKE '%monomanga%'", (cid,))
                
                # Find ragnarscans site record
                ragnar = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE '%ragnarscans%'", (cid,)).fetchone()
                series_url = f"https://ragnarscans.net/manga/{found_slug}/"
                if ragnar:
                    db.execute("UPDATE site SET site_url=?, is_dead=0, is_primary=1 WHERE id=?", (series_url, ragnar[0]))
                else:
                    db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead) VALUES (?, 'RagnarScans', ?, 1, 1, 0)", (cid, series_url))
                
                # Update episode URLs
                cur2 = db.execute("SELECT number, id FROM episode WHERE content_id=? ORDER BY number", (cid,))
                eps = cur2.fetchall()
                for ep in eps:
                    ep_url = f"https://ragnarscans.net/manga/{found_slug}/bolum-{ep['number']}/"
                    db.execute("UPDATE episode SET url=? WHERE id=?", (ep_url, ep["id"]))
                
                # Get chapter count from series page
                try:
                    r = await cl.get(series_url, timeout=12)
                    if r.status_code == 200:
                        ch_links = re.findall(r'href="https://ragnarscans\.net/manga/[^"]+/bolum-(\d+)/"', r.text)
                        if ch_links:
                            max_ch = max(int(n) for n in ch_links)
                            db.execute("UPDATE content SET total_chapters=? WHERE id=?", (max_ch, cid))
                            print(f"  Updated: total_chapters={max_ch}, eps={len(eps)}")
                except:
                    pass
            else:
                print(f"  NOT FOUND on ragnarscans")
    
    # 2. Fix total_chapters for ALL ragnarscans-primary mangas (pagination issue)
    print("\n=== Fix total_chapters (pagination) ===")
    cur = db.execute("""
        SELECT c.id, c.title, c.total_chapters, s.site_url
        FROM content c
        JOIN site s ON s.content_id = c.id
        WHERE c.type IN ('manga', 'manhwa') AND s.is_primary=1 AND s.site_url LIKE '%ragnarscans.net/manga/%'
        ORDER BY c.id
    """)
    primaries = [dict(r) for r in cur.fetchall()]
    print(f"  Total ragnarscans-primary: {len(primaries)}")
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=15) as cl:
        fixed = 0
        for m in primaries:
            try:
                r = await cl.get(m["site_url"], timeout=12)
                if r.status_code == 200:
                    # Find highest chapter number
                    ch_nums = re.findall(r'/bolum-(\d+)/', r.text)
                    if ch_nums:
                        max_ch = max(int(n) for n in ch_nums)
                        if max_ch > m["total_chapters"]:
                            db.execute("UPDATE content SET total_chapters=? WHERE id=?", (max_ch, m["id"]))
                            fixed += 1
                            if fixed <= 5:
                                print(f"  c.id={m['id']:4d} {m['title'][:35]:35s} | total_ch {m['total_chapters']} → {max_ch}")
            except:
                pass
            await asyncio.sleep(0.15)
    
    db.commit()
    print(f"  total_chapters fixed: {fixed}")
    
    # 3. Verify
    print("\n=== Final verify ===")
    for cid in [137, 152, 198, 680]:
        cur = db.execute("SELECT id, title, total_chapters FROM content WHERE id=?", (cid,))
        c = cur.fetchone()
        if not c:
            continue
        cur2 = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=? AND is_primary=1", (cid,))
        s = cur2.fetchone()
        cur3 = db.execute("SELECT number, url FROM episode WHERE content_id? ORDER BY number LIMIT 2", (cid,))
        cur3 = db.execute("SELECT number, url FROM episode WHERE content_id=? ORDER BY number LIMIT 2", (cid,))
        eps = cur3.fetchall()
        print(f"  c.id={cid:4d} {c['title'][:35]:35s} | total_ch={c['total_chapters']}")
        if s:
            print(f"    primary: {s['site_name']:15s} dead={s['is_dead']} | {s['site_url'][:60]}")
        for e in eps:
            print(f"    ep#{e['number']}: {e['url'][:70]}")
    
    db.close()
    print("\n=== DONE ===")

asyncio.run(main())
