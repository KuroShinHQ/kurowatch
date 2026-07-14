"""SOHBET-166 — Fix episode count for 198 + MangaDex fallback for 137/152 + search more."""
import asyncio, httpx, sqlite3, os, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Referer": "https://www.google.com/"}
DB = os.path.join("memory", "kurowatch.db")

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    # 1. Fix 198 episodes — check what happened
    print("=== c.id=198 episode check ===")
    cur = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=198")
    cnt = cur.fetchone()["cnt"]
    print(f"  Episodes: {cnt}")
    
    if cnt < 10:
        # Recreate episodes
        cur2 = db.execute("SELECT total_chapters FROM content WHERE id=198")
        total = cur2.fetchone()["total_chapters"]
        print(f"  total_chapters: {total}")
        # Delete existing
        db.execute("DELETE FROM episode WHERE content_id=198")
        # Insert new
        for n in range(1, total + 1):
            db.execute("INSERT INTO episode (content_id, number, title, url, season, is_watched, is_new, watched_at) VALUES (?, ?, ?, ?, 1, 0, 0, NULL)",
                (198, n, f"Bölüm {n}", f"https://mangawow.org/manga/trash-of-the-counts-family/bolum-{n}/"))
        db.commit()
        cur3 = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=198")
        cnt2 = cur3.fetchone()["cnt"]
        print(f"  After fix: {cnt2} episodes")
    
    # 2. Search mangawow + asurascans for 137 and 152
    print("\n=== Search 137 + 152 on mangawow + asurascans ===")
    SEARCH = {
        137: ["after ten millennia", "after-ten-millennia", "on bin yil", "10000 yil"],
        152: ["lout of count", "lout-of-count", "baekjakga", "mangnani"],
    }
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True, timeout=12) as cl:
        for cid, queries in SEARCH.items():
            print(f"\n  c.id={cid}:")
            for sname, sbase in [("mangawow.org", "https://mangawow.org"), ("asurascans.com.tr", "https://asurascans.com.tr")]:
                for q in queries:
                    try:
                        r = await cl.get(sbase + "/wp-json/wp/v2/search", params={"search": q, "per_page": 10}, timeout=10)
                        if r.status_code == 200:
                            data = r.json()
                            if isinstance(data, list) and data:
                                print(f"    [{sname}] q={q!r}: {len(data)} results")
                                for d in data[:3]:
                                    print(f"      {d.get('title','?')[:40]:40s} | {d.get('url','-')}")
                    except:
                        pass
                    await asyncio.sleep(0.1)
                    
                    # Also try direct URL
                    for slug in queries:
                        url = f"{sbase}/manga/{slug}/"
                        try:
                            r = await cl.get(url, timeout=8)
                            if r.status_code == 200 and len(r.text) > 20000:
                                ch_links = re.findall(r'/bolum-\d+/', r.text)
                                if ch_links:
                                    print(f"    ✅ {sname} direct: /manga/{slug}/ | {len(ch_links)} chapters")
                        except:
                            pass
                        await asyncio.sleep(0.05)
    
    # 3. For 137 and 152 — if no Turkish source, use MangaDex as primary (English but at least works)
    print("\n=== Fallback: MangaDex primary for 137/152 ===")
    for cid in [137, 152]:
        # Mark monomanga dead
        db.execute("UPDATE site SET is_dead=1, is_primary=0 WHERE content_id=? AND site_url LIKE '%monomanga%'", (cid,))
        # Make MangaDex primary
        md = db.execute("SELECT id, site_url FROM site WHERE content_id=? AND site_url LIKE '%mangadex%'", (cid,)).fetchone()
        if md:
            db.execute("UPDATE site SET is_primary=1, is_dead=0 WHERE id=?", (md[0],))
            print(f"  c.id={cid}: MangaDex primary | {md['site_url']}")
        
        # Get chapter count from MangaDex
        cur = db.execute("SELECT external_id FROM content WHERE id=?", (cid,))
        ext = cur.fetchone()["external_id"]
        uuid = ext.replace("mdx:", "")
        
        async with httpx.AsyncClient(headers={"User-Agent": "MangaDexApi/1.0"}, timeout=20) as cl:
            try:
                r = await cl.get(f"https://api.mangadex.org/manga/{uuid}", timeout=15)
                if r.status_code == 200:
                    attrs = r.json().get("data", {}).get("attributes", {})
                    last_ch = attrs.get("lastChapter", "0")
                    try:
                        total = int(float(last_ch))
                    except:
                        total = 0
                    if total > 0:
                        db.execute("UPDATE content SET total_chapters=? WHERE id=?", (total, cid))
                        print(f"  total_chapters: {total}")
                        
                        # Create episodes if < 2
                        cur2 = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=?", (cid,))
                        ep_cnt = cur2.fetchone()["cnt"]
                        if ep_cnt < 2:
                            db.execute("DELETE FROM episode WHERE content_id=?", (cid,))
                            for n in range(1, min(total + 1, 200)):  # max 200 episodes
                                db.execute("INSERT INTO episode (content_id, number, title, url, season, is_watched, is_new, watched_at) VALUES (?, ?, ?, ?, 1, 0, 0, NULL)",
                                    (cid, n, f"Bölüm {n}", md["site_url"]))
                            print(f"  Created {min(total, 200)} episodes (MangaDex URL)")
            except Exception as e:
                print(f"  MangaDex API error: {e}")
    
    db.commit()
    
    # 4. Also create episodes for 680 (The Greatest Estate Developer) if needed
    cur = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=680")
    cnt680 = cur.fetchone()["cnt"]
    if cnt680 < 10:
        cur2 = db.execute("SELECT total_chapters FROM content WHERE id=680")
        total680 = cur2.fetchone()["total_chapters"]
        db.execute("DELETE FROM episode WHERE content_id=680")
        for n in range(1, total680 + 1):
            db.execute("INSERT INTO episode (content_id, number, title, url, season, is_watched, is_new, watched_at) VALUES (?, ?, ?, ?, 1, 0, 0, NULL)",
                (680, n, f"Bölüm {n}", f"https://ragnarscans.net/manga/the-greatest-estate-developer/bolum-{n}/"))
        db.commit()
        print(f"\n  c.id=680: Created {total680} episodes (ragnarscans)")
    
    # 5. Final verify
    print("\n=== FINAL VERIFY ===")
    for cid in [137, 152, 198, 680]:
        cur = db.execute("SELECT id, title, total_chapters FROM content WHERE id=?", (cid,))
        c = cur.fetchone()
        if not c:
            continue
        cur2 = db.execute("SELECT site_name, site_url, is_primary, is_dead FROM site WHERE content_id=? AND is_primary=1", (cid,))
        s = cur2.fetchone()
        cur3 = db.execute("SELECT COUNT(*) as cnt FROM episode WHERE content_id=?", (cid,))
        ep_cnt = cur3.fetchone()["cnt"]
        print(f"  c.id={cid:4d} {c['title'][:35]:35s} | total_ch={c['total_chapters']:4d} | eps={ep_cnt:4d}")
        if s:
            print(f"    primary: {s['site_name']:15s} | {s['site_url'][:60]}")
    
    db.close()
    print("\n=== DONE ===")

asyncio.run(main())
