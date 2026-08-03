"""
SOHBET-164 — 28 DİZİ MIGRATION: setfilmizle.uk/dizipod → dizimag.com.tr + alternatifler
=====================================================================================

Strateji:
1. Tüm failing series'leri tespit et (test ederek)
2. Her biri için dizimag.com.tr'de ara (WP REST search API)
3. Bulunanlara dizimag site kaydı ekle (site_url=/{slug}/)
4. Bulunamayanlar için alternatifler:
   - dizibox.live (HTML search — WP REST 401)
   - yabancidizi.life (redirect from yabancidizi.pro)
   - hdfilmcehennemi.now (tvshows subtype)
"""
import asyncio, httpx, json, sqlite3, os, re
from urllib.parse import quote

DB = os.path.join("memory", "kurowatch.db")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Accept": "application/json,*/*"}

DIZIMAG_SEARCH = "https://www.dizimag.com.tr/wp-json/wp/v2/search"
HDFC_SEARCH = "https://www.hdfilmcehennemi.now/wp-json/wp/v2/search"
DIZIBOX_BASE = "https://www.dizibox.live"
YABANCIDIZI_BASE = "https://yabancidizi.life"

async def test_url(client, url):
    try:
        r = await client.head(url, timeout=10)
        if r.status_code == 405:
            r = await client.get(url, timeout=10)
        return r.status_code
    except:
        return 0

async def search_dizimag(client, query, per_page=10):
    """Search dizimag.com.tr — returns list of {id, title, url, subtype}."""
    try:
        r = await client.get(DIZIMAG_SEARCH, params={"search": query, "per_page": per_page}, timeout=12)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

async def search_hdfc_tvshows(client, query, per_page=10):
    """Search hdfc.now — return tvshows only."""
    try:
        r = await client.get(HDFC_SEARCH, params={"search": query, "per_page": per_page}, timeout=12)
        if r.status_code == 200:
            data = r.json()
            return [d for d in data if d.get("subtype") == "tvshows"]
    except:
        pass
    return []

async def search_dizibox_html(client, query):
    """Search dizibox.live via HTML (WP REST returns 401)."""
    try:
        r = await client.get(DIZIBOX_BASE + "/", params={"s": query}, timeout=12)
        if r.status_code == 200:
            # extract post URLs
            urls = re.findall(r'href="(' + re.escape(DIZIBOX_BASE) + r'/([^"#?/]+/))"', r.text)
            # filter out category/page/feed
            filt = [(u, s) for u, s in urls if not any(x in u for x in ['/kategori/', '/category/', '/page/', '/feed/', '/wp-', '/kunye/', '/iletisim/', '/gizlilik/'])]
            return list(dict.fromkeys(filt))[:5]
    except:
        pass
    return []

async def search_yabancidizi(client, query):
    """Search yabancidizi.life."""
    try:
        r = await client.get(YABANCIDIZI_BASE + "/", params={"s": query}, timeout=12)
        if r.status_code == 200:
            urls = re.findall(r'href="(https?://(?:www\.)?yabancidizi\.life/([^"#?/]+/))"', r.text)
            filt = [(u, s) for u, s in urls if not any(x in u for x in ['/page/', '/feed/', '/wp-', '/kategori/', '/category/'])]
            return list(dict.fromkeys(filt))[:5]
    except:
        pass
    return []

# Series name translations for search
SERIES_QUERIES = {
    # Turkish series — search with Turkish name
    201: ["1 Kadın 1 Erkek"],
    212: ["Adanalı"],
    226: ["Arka Sokaklar"],
    242: ["Behzat Ç."],
    243: ["Behzat Ç. Bir Ankara Polisiyesi", "Behzat C"],
    248: ["Black Mirror"],
    252: ["Breaking Bad"],
    273: ["Dark"],
    287: ["Dexter"],
    292: ["Doctor Who"],
    293: ["Doktorlar"],
    322: ["Galip Derviş"],
    323: ["Game of Thrones", "Taht Oyunları"],
    326: ["Geniş Aile"],
    346: ["Hannibal"],
    352: ["House M.D.", "House MD"],
    355: ["Hugo"],
    400: ["Kardeş Payı"],
    409: ["Komedi Dükkanı"],
    410: ["Komedi Dükkanı"],
    416: ["Kurtlar Vadisi Pusu"],
    417: ["Kurtlar Vadisi Pusu"],
    420: ["La Casa de Papel", "Money Heist"],
    423: ["Limitless"],
    429: ["Love Death Robots"],
    456: ["Monsters At Work", "Sevimli Canavarlar"],
    457: ["Mr. Robot"],
    459: ["Muhteşem Yüzyıl"],
    491: ["Pis Yedili"],
    505: ["Rick and Morty"],
    522: ["Seksenler"],
    523: ["Selena"],
    530: ["Sherlock"],
    548: ["Sihirli Annem"],
    559: ["Squid Game"],
    568: ["Teach You a Lesson"],
    570: ["Teletubbies"],
    604: ["The Mentalist"],
    612: ["The Walking Dead"],
    613: ["The Witcher"],
    656: ["Yahşi Cazibe"],
    657: ["Yaprak Dökümü"],
    661: ["You"],
    673: ["Çocuklar Duymasın"],
    674: ["Çok Güzel Hareketler Bunlar", "ÇGHB"],
    675: ["Çok Güzel Hareketler Bunlar"],
    677: ["Öyle Bir Geçer Zaman ki"],
}

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    # Get all series
    cur = db.execute("SELECT id, title FROM content WHERE type='series' ORDER BY id")
    all_series = [dict(r) for r in cur.fetchall()]
    print(f"Total series: {len(all_series)}")
    
    # First, test which series are currently failing
    print("\n=== Testing current series URLs ===")
    failing = []
    passing = []
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True) as cl:
        for s in all_series:
            # Get ALL urls for this series (site + episode)
            cur2 = db.execute("SELECT site_url FROM site WHERE content_id=? AND site_url IS NOT NULL", (s["id"],))
            site_urls = [r["site_url"] for r in cur2.fetchall()]
            cur3 = db.execute("SELECT DISTINCT url FROM episode WHERE content_id=? AND url IS NOT NULL AND url != ''", (s["id"],))
            ep_urls = [r["url"] for r in cur3.fetchall()]
            all_urls = list(dict.fromkeys(site_urls + ep_urls))
            
            if not all_urls:
                failing.append(s)
                print(f"  FAIL c.id={s['id']:4d} {s['title'][:40]:40s} | NO URL")
                continue
            
            # Test each URL — if ANY works, series passes
            any_ok = False
            for u in all_urls[:5]:  # test up to 5 URLs
                status = await test_url(cl, u)
                if status == 200:
                    any_ok = True
                    break
            
            if any_ok:
                passing.append(s)
            else:
                failing.append(s)
                print(f"  FAIL c.id={s['id']:4d} {s['title'][:40]:40s} | all {len(all_urls)} URLs dead")
    
    print(f"\nPassing: {len(passing)}, Failing: {len(failing)}")
    
    # Now search for failing series on dizimag + alternatives
    print(f"\n=== Searching {len(failing)} failing series on dizimag + alternatives ===")
    results = {}
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True) as cl:
        for s in failing:
            cid = s["id"]
            title = s["title"]
            queries = SERIES_QUERIES.get(cid, [title])
            print(f"\n--- c.id={cid} {title} ---")
            
            found = None
            for q in queries:
                # 1. dizimag.com.tr (WP REST)
                dizi = await search_dizimag(cl, q)
                if dizi:
                    # dizimag search returns posts — filter for actual series (not episode pages)
                    # A series page has URL like /{slug}/ (no /sezon/ or /bolum/)
                    series_results = [d for d in dizi if d.get("url") and 
                                      not any(x in d["url"] for x in ['/sezon-', '/bolum', '/bölüm', '/episode', '/kategori/', '/Kategori/'])]
                    if series_results:
                        print(f"  [dizimag] q={q!r}: {len(series_results)} series results")
                        for r in series_results[:3]:
                            print(f"    {r['title'][:40]:40s} | {r['url']}")
                        if not found:
                            found = ("dizimag.com.tr", series_results[0]["title"], series_results[0]["url"])
                
                # 2. hdfc.now tvshows
                tv = await search_hdfc_tvshows(cl, q)
                if tv:
                    print(f"  [hdfc.now tvshows] q={q!r}: {len(tv)} results")
                    for r in tv[:3]:
                        print(f"    {r['title'][:40]:40s} | {r['url']}")
                    if not found:
                        found = ("hdfilmcehennemi.now", tv[0]["title"], tv[0]["url"])
                
                # 3. dizibox.live (HTML)
                if not found:
                    db_results = await search_dizibox_html(cl, q)
                    if db_results:
                        print(f"  [dizibox.live] q={q!r}: {len(db_results)} results")
                        for u, slug in db_results[:3]:
                            print(f"    {slug:30s} | {u}")
                        if not found:
                            found = ("dizibox.live", db_results[0][1], db_results[0][0])
                
                # 4. yabancidizi.life (HTML)
                if not found:
                    yd_results = await search_yabancidizi(cl, q)
                    if yd_results:
                        print(f"  [yabancidizi.life] q={q!r}: {len(yd_results)} results")
                        for u, slug in yd_results[:3]:
                            print(f"    {slug:30s} | {u}")
                        if not found:
                            found = ("yabancidizi.life", yd_results[0][1], yd_results[0][0])
                
                await asyncio.sleep(0.2)
            
            if found:
                results[cid] = {"site": found[0], "title": found[1], "url": found[2], "original_title": title}
                print(f"  => FOUND: {found[0]} | {found[1]} | {found[2]}")
            else:
                results[cid] = None
                print(f"  => NOT FOUND")
    
    # Save results
    with open("_sohbet164_series_matches.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    found_count = sum(1 for v in results.values() if v)
    print(f"\n=== SUMMARY: {found_count}/{len(failing)} failing series found ===")
    
    # === DB UPDATE ===
    print(f"\n=== DB UPDATE ===")
    inserted = 0
    for cid, r in results.items():
        if not r:
            continue
        site_name = r["site"]
        url = r["url"]
        
        # Mark existing setfilmizle/dizipod sites as dead
        db.execute("""
            UPDATE site SET is_dead=1, is_primary=0
            WHERE content_id=? AND (
                site_url LIKE '%setfilmizle%' OR
                site_url LIKE '%dizipod%' OR
                site_name LIKE '%setfilmizle%' OR
                site_name LIKE '%dizipod%' OR
                site_url LIKE '%hdfilmcehennemi.nl%'
            )
        """, (cid,))
        
        # Check if this site already exists
        site_pattern = f"%{site_name.replace('.', '%')}%"  # fuzzy match
        existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE ?", (cid, f"%{site_name}%")).fetchone()
        if existing:
            db.execute("UPDATE site SET site_url=?, site_name=?, is_primary=1, is_dead=0 WHERE id=?", (url, site_name, existing[0]))
        else:
            db.execute("""
                INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead)
                VALUES (?, ?, ?, 1, 1, 0)
            """, (cid, site_name, url))
            inserted += 1
        
        # Update episode URLs — set them to the series page URL (all episodes point to same page)
        db.execute("""
            UPDATE episode SET url=?
            WHERE content_id=? AND (
                url LIKE '%setfilmizle%' OR
                url LIKE '%dizipod%' OR
                url IS NULL OR url=''
            )
        """, (url, cid))
    
    db.commit()
    print(f"  New site records inserted: {inserted}")
    
    # Final verification — test all series again
    print(f"\n=== FINAL VERIFICATION ===")
    ok = 0
    fail = 0
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True) as cl:
        for s in all_series:
            cur2 = db.execute("SELECT site_url FROM site WHERE content_id=? AND site_url IS NOT NULL AND (is_dead=0 OR is_dead IS NULL)", (s["id"],))
            urls = [r["site_url"] for r in cur2.fetchall()]
            if not urls:
                fail += 1
                if s["id"] in [r["id"] for r in failing]:
                    print(f"  STILL FAIL c.id={s['id']:4d} {s['title'][:40]}")
                continue
            any_ok = False
            for u in urls[:3]:
                status = await test_url(cl, u)
                if status == 200:
                    any_ok = True
                    break
            if any_ok:
                ok += 1
            else:
                fail += 1
                print(f"  STILL FAIL c.id={s['id']:4d} {s['title'][:40]}")
    
    print(f"\n  Series: {ok}/{len(all_series)} OK, {fail} FAIL")
    
    db.close()
    print(f"\n=== DONE — Series migration complete ===")

if __name__ == "__main__":
    asyncio.run(main())
