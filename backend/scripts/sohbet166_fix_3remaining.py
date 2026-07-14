"""SOHBET-166 — Direct URL test for 3 remaining mangas on ragnarscans + other sites."""
import asyncio, httpx, sqlite3, os, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Referer": "https://www.google.com/"}
DB = os.path.join("memory", "kurowatch.db")

# 3 remaining mangas — try direct URL patterns
TARGETS = {
    137: ("After Ten Millennia in Hell", [
        "after-ten-millennia-in-hell",
        "after-10-millennia-in-hell",
        "after-ten-millennia",
    ]),
    152: ("Lout of Count's Family", [
        "lout-of-counts-family",
        "lout-of-the-counts-family",
        "lout-of-count-family",
    ]),
    198: ("Trash of the Count's Family", [
        "trash-of-the-counts-family",
        "trash-of-the-count-family",
        "trash-of-counts-family",
    ]),
}

SITES = [
    ("ragnarscans.net", "https://ragnarscans.net"),
    ("mangawow.org", "https://mangawow.org"),
    ("asurascans.com.tr", "https://asurascans.com.tr"),
    ("mangasehri.net", "https://mangasehri.net"),
]

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=12) as cl:
        for cid, (title, slugs) in TARGETS.items():
            print(f"\n=== c.id={cid} {title} ===")
            found = None
            
            for sname, sbase in SITES:
                if found:
                    break
                for slug in slugs:
                    # Try /manga/{slug}/
                    url = f"{sbase}/manga/{slug}/"
                    try:
                        r = await cl.get(url, timeout=10)
                        if r.status_code == 200 and len(r.text) > 20000:
                            # Check for chapter links
                            ch_links = re.findall(r'href="[^"]*/bolum-\d+/"', r.text)
                            if ch_links:
                                found = (sname, sbase, slug, url, len(ch_links))
                                print(f"  ✅ {sname}: /manga/{slug}/ | HTTP 200 | {len(ch_links)} chapters")
                                break
                    except:
                        pass
                    await asyncio.sleep(0.1)
            
            if found:
                sname, sbase, slug, series_url, ch_count = found
                
                # Mark monomanga dead
                db.execute("UPDATE site SET is_dead=1, is_primary=0 WHERE content_id=? AND site_url LIKE '%monomanga%'", (cid,))
                
                # Find or create site record
                existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE ?", (cid, f"%{sname}%")).fetchone()
                if existing:
                    db.execute("UPDATE site SET site_url=?, is_dead=0, is_primary=1 WHERE id=?", (series_url, existing[0]))
                else:
                    db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead) VALUES (?, ?, ?, 1, 1, 0)", (cid, sname, series_url))
                
                # Get max chapter number
                try:
                    r = await cl.get(series_url, timeout=12)
                    if r.status_code == 200:
                        ch_nums = re.findall(r'/bolum-(\d+)/', r.text)
                        if ch_nums:
                            max_ch = max(int(n) for n in ch_nums)
                            db.execute("UPDATE content SET total_chapters=? WHERE id=?", (max_ch, cid))
                            print(f"  total_chapters: {max_ch}")
                except:
                    pass
                
                # Update episode URLs
                cur2 = db.execute("SELECT number, id FROM episode WHERE content_id=? ORDER BY number", (cid,))
                eps = cur2.fetchall()
                for ep in eps:
                    ep_url = f"{sbase}/manga/{slug}/bolum-{ep['number']}/"
                    db.execute("UPDATE episode SET url=? WHERE id=?", (ep_url, ep["id"]))
                print(f"  Episodes updated: {len(eps)}")
                
                # If only 1 episode, create more from chapter count
                if len(eps) < 2 and ch_count > 1:
                    # Get max chapter number
                    try:
                        r = await cl.get(series_url, timeout=12)
                        ch_nums = re.findall(r'/bolum-(\d+)/', r.text)
                        if ch_nums:
                            max_ch = max(int(n) for n in ch_nums)
                            # Create missing episodes
                            for n in range(1, max_ch + 1):
                                ep_url = f"{sbase}/manga/{slug}/bolum-{n}/"
                                db.execute("INSERT OR IGNORE INTO episode (content_id, number, title, url, season) VALUES (?, ?, ?, ?, 1)",
                                    (cid, n, f"Bölüm {n}", ep_url))
                            print(f"  Created {max_ch} episodes")
                    except:
                        pass
            else:
                print(f"  ❌ NOT FOUND on any site")
        
        db.commit()
    
    # Verify
    print("\n=== VERIFY ===")
    for cid in [137, 152, 198, 680]:
        cur = db.execute("SELECT id, title, total_chapters FROM content WHERE id=?", (cid,))
        c = cur.fetchone()
        if not c:
            continue
        cur2 = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=? AND is_primary=1", (cid,))
        s = cur2.fetchone()
        cur3 = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=?", (cid,))
        ep_cnt = cur3.fetchone()["cnt"]
        print(f"  c.id={cid:4d} {c['title'][:35]:35s} | total_ch={c['total_chapters']} | eps={ep_cnt}")
        if s:
            print(f"    primary: {s['site_name']} | {s['site_url'][:60]}")
    
    db.close()
    print("\n=== DONE ===")

asyncio.run(main())
