"""SOHBET-164 — Final search for 8 still-failing series via direct URL guessing + alternatives."""
import asyncio, httpx, json, sqlite3, os, re

DB = os.path.join("memory", "kurowatch.db")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"}

_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

def slugify(s):
    s = s.lower().strip().translate(_TR_MAP)
    s = re.sub(r'\(.*?\)', '', s)
    s = re.sub(r"'", '', s)
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s

# 8 still-failing series with guess slugs
STILL_FAILING = {
    322: ("Galip Derviş", ["galip-dervis", "galip-dervis-1", "galip-dervis-2"]),
    416: ("Kurtlar Vadisi (Pusu dönemi)", ["kurtlar-vadisi-pusu", "kurtlar-vadisi", "kurtlar-vadisi-pusu-1"]),
    417: ("Kurtlar Vadisi (Pusu)", ["kurtlar-vadisi-pusu", "kurtlar-vadisi", "kurtlar-vadisi-pusu-1"]),
    522: ("Seksenler", ["seksenler", "seksenler-1", "seksenler-dizi"]),
    570: ("Teletubbies", ["teletubbies", "teletubbies-1", "teletabi"]),
    673: ("Çocuklar Duymasın", ["cocuklar-duymasin", "cocuklar-duymasin-1", "cocuklar-duymasin-dizi"]),
    674: ("Çok Güzel Hareketler Bunlar", ["cok-guzel-hareketler-bunlar", "cghb", "cok-guzel-hareketler-bunlar-1"]),
    675: ("Çok Güzel Hareketler Bunlar (1. Kuşak)", ["cok-guzel-hareketler-bunlar", "cghb", "cok-guzel-hareketler-bunlar-1"]),
}

async def test_url(client, url):
    try:
        r = await client.head(url, timeout=8)
        if r.status_code == 405:
            r = await client.get(url, timeout=8)
        return r.status_code, len(r.text) if r.status_code < 400 else 0
    except:
        return 0, 0

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    results = {}
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True) as cl:
        for cid, (title, guess_slugs) in STILL_FAILING.items():
            print(f"\n=== c.id={cid} {title} ===")
            found = None
            
            # 1. Try dizimag direct URL: https://www.dizimag.com.tr/{slug}/
            for slug in guess_slugs:
                url = f"https://www.dizimag.com.tr/{slug}/"
                status, sz = await test_url(cl, url)
                if status == 200 and sz > 30000:
                    found = ("dizimag.com.tr", slug, url)
                    print(f"  ✅ dizimag direct: {url} (HTTP {status}, bytes={sz})")
                    break
            
            # 2. Try hdfc.now tvshows search with broader queries
            if not found:
                queries_map = {
                    322: ["Galip Derviş", "Galip Dervis"],
                    416: ["Kurtlar Vadisi Pusu", "Kurtlar Vadisi"],
                    417: ["Kurtlar Vadisi Pusu", "Kurtlar Vadisi"],
                    522: ["Seksenler"],
                    570: ["Teletubbies", "Teletabi"],
                    673: ["Çocuklar Duymasın", "Cocuklar Duymasin"],
                    674: ["Çok Güzel Hareketler", "Cok Guzel Hareketler"],
                    675: ["Çok Güzel Hareketler", "Cok Guzel Hareketler"],
                }
                for q in queries_map.get(cid, [title]):
                    try:
                        r = await cl.get("https://www.hdfilmcehennemi.now/wp-json/wp/v2/search", params={"search": q, "per_page": 15}, timeout=12)
                        if r.status_code == 200:
                            data = r.json()
                            tv = [d for d in data if d.get("subtype") == "tvshows"]
                            if tv:
                                print(f"  [hdfc.now tvshows] q={q!r}: {len(tv)} results")
                                for t in tv[:3]:
                                    print(f"    {t['title'][:40]:40s} | {t['url']}")
                                if not found:
                                    found = ("hdfilmcehennemi.now", t["title"], tv[0]["url"])
                    except:
                        pass
                    await asyncio.sleep(0.1)
            
            # 3. Try dizibox HTML search
            if not found:
                queries_map2 = {
                    322: "Galip Derviş",
                    416: "Kurtlar Vadisi Pusu",
                    417: "Kurtlar Vadisi Pusu",
                    522: "Seksenler",
                    570: "Teletubbies",
                    673: "Çocuklar Duymasın",
                    674: "Çok Güzel Hareketler Bunlar",
                    675: "Çok Güzel Hareketler Bunlar",
                }
                q = queries_map2.get(cid, title)
                try:
                    r = await cl.get("https://www.dizibox.live/", params={"s": q}, timeout=12)
                    if r.status_code == 200:
                        urls = re.findall(r'href="(https?://(?:www\.)?dizibox\.live/([^"#?/]+/))"', r.text)
                        filt = [(u, s) for u, s in urls if not any(x in u for x in ['/kategori/', '/category/', '/page/', '/feed/', '/wp-', '/kunye/', '/iletisim/', '/gizlilik/', '/arama/'])]
                        uniq = list(dict.fromkeys(filt))[:5]
                        if uniq:
                            print(f"  [dizibox] q={q!r}: {len(uniq)} results")
                            for u, s in uniq:
                                print(f"    {s:30s} | {u}")
                            found = ("dizibox.live", uniq[0][1], uniq[0][0])
                except:
                    pass
            
            # 4. Try yabancidizi.life
            if not found:
                q = title.split("(")[0].strip()
                try:
                    r = await cl.get("https://yabancidizi.life/", params={"s": q}, timeout=12)
                    if r.status_code == 200:
                        urls = re.findall(r'href="(https?://(?:www\.)?yabancidizi\.life/([^"#?/]+/))"', r.text)
                        filt = [(u, s) for u, s in urls if not any(x in u for x in ['/page/', '/feed/', '/wp-', '/kategori/', '/category/'])]
                        uniq = list(dict.fromkeys(filt))[:5]
                        if uniq:
                            print(f"  [yabancidizi] q={q!r}: {len(uniq)} results")
                            for u, s in uniq:
                                print(f"    {s:30s} | {u}")
                            found = ("yabancidizi.life", uniq[0][1], uniq[0][0])
                except:
                    pass
            
            if found:
                results[cid] = {"site": found[0], "slug_or_title": found[1], "url": found[2]}
                print(f"  => FOUND: {found[0]} | {found[2]}")
            else:
                results[cid] = None
                print(f"  => NOT FOUND")
    
    # Save
    with open("_sohbet164_series_final.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # DB update
    print(f"\n=== DB UPDATE ===")
    inserted = 0
    for cid, r in results.items():
        if not r:
            continue
        site_name = r["site"]
        url = r["url"]
        
        # Mark old sites dead
        db.execute("""
            UPDATE site SET is_dead=1, is_primary=0
            WHERE content_id=? AND (
                site_url LIKE '%setfilmizle%' OR site_url LIKE '%dizipod%' OR
                site_name LIKE '%setfilmizle%' OR site_name LIKE '%dizipod%'
            )
        """, (cid,))
        
        existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE ?", (cid, f"%{site_name}%")).fetchone()
        if existing:
            db.execute("UPDATE site SET site_url=?, site_name=?, is_primary=1, is_dead=0 WHERE id=?", (url, site_name, existing[0]))
        else:
            db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead) VALUES (?, ?, ?, 1, 1, 0)", (cid, site_name, url))
            inserted += 1
        
        db.execute("UPDATE episode SET url=? WHERE content_id=? AND (url LIKE '%setfilmizle%' OR url LIKE '%dizipod%' OR url IS NULL OR url='')", (url, cid))
    
    db.commit()
    print(f"  Inserted: {inserted}")
    
    # Final count
    cur = db.execute("""
        SELECT COUNT(*) FROM content c
        WHERE c.type='series' AND EXISTS (
            SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url IS NOT NULL AND (s.is_dead=0 OR s.is_dead IS NULL)
        )
    """)
    with_site = cur.fetchone()[0]
    print(f"  Series with non-dead site: {with_site}/49")
    
    db.close()
    print(f"\n=== DONE ===")

asyncio.run(main())
