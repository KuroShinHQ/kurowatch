"""SOHBET-157: Retry MangaDex search for still-orphan manga/manhwa with English titles"""
import asyncio, httpx, sqlite3, json, re
from datetime import datetime

DB_PATH = 'memory/kurowatch.db'
MANGADEX_API = "https://api.mangadex.org"

# Turkish-to-English title mappings for items that failed
TITLE_MAP = {
    "Eskiden Zindan Patronuydum": ["Dungeon Boss", "I Used to be a Dungeon Boss"],
    "Büyü İmparatoru": ["Magic Emperor"],
    "Bilge Okuyucunun Bakış Açısı": ["Omniscient Reader's Viewpoint", "Omniscient Reader"],
    "Dünyanın En İyi Mühendisi": ["The World's Best Engineer", "The Greatest Estate Developer"],
    "Seçkinin İkinci Yaşamı": ["The Second Life of a Gangster", "The Second Life of a Rank"],
    "Deli Mühendis": ["Crazy Engineer", "The Crazy Engineer"],
    "Kılıç Kralının Fantezi Dünyasında Hayatta Kalma Hikayesi": ["Sword King's Survival", "Survival Story of a Sword King"],
    "Kaderin Zirvesi": ["Peak of Fate", "The Peak of Fate"],
    "Soylu Ailenin İşe Yaramaz Oğlu": ["The Useless Child of the Noble Family", "The Useless Young Master"],
    "Şamanın Yolu": ["Path of the Shaman", "Shaman's Path"],
    "Kılıç Hanesinin Genç Efendisi": ["Young Lord of the Sword Family", "Swordmaster's Youngest Son"],
    "Yıldız Hocası Baek": ["Baek the Star Instructor", "Star Instructor Baek"],
    "Mağdur Sıralamacının Dönüşü": ["Return of the Victim Ranker", "Survival of a Victim Ranker"],
    "Kahraman Döndü": ["The Hero Returns", "Hero Has Returned"],
    "Regresör Kullanım Kılavuzu": ["Regressor Instruction Manual", "Regressor's Manual"],
    "O Gerçekten Bir Kahraman mı?": ["Is He Really a Hero?", "Is It a Hero?"],
    "Sonsuz Döngüde Hapsolan": ["Trapped in an Infinite Loop", "Trapped in Endless Cycle"],
    "Sokakta Hayatta Kalma Kılavuzu": ["Street Survival Guide", "How to Survive on the Street"],
    "Yetenek Yutan Sihirbaz": ["Talent-Swallowing Magician", "The Magician Who Swallows Talent"],
    "Tanrıçanın Kulu": ["Goddess's Servant", "Servant of the Goddess"],
    "Şeytani Egemenin Halefi": ["Successor of the Evil Sovereign", "Heir to the Evil Sovereign"],
    "Yıldırım Bıçağı Ustası": ["Lightning Knife Master", "Lightning Blade Master"],
    "Sémalarin Kilici": ["Sword of the Skies", "Heavenly Sword"],
    "Oyun Obu Familia Aile Senki": ["Ore no Familia", "Game Obu Familia"],
    "Martial Divine Demon": ["Martial Divine Demon"],
}

async def search_mangadex(client, title, mal_id=None):
    """Search MangaDex by title, optionally filter by MAL ID"""
    if mal_id:
        try:
            r = await client.get(f"{MANGADEX_API}/manga", params={"malId": mal_id}, timeout=15)
            if r.status_code == 200 and r.json().get("data"):
                m = r.json()["data"][0]
                return m["id"], "mal_id"
        except Exception:
            pass
    
    try:
        r = await client.get(f"{MANGADEX_API}/manga", params={"title": title, "limit": 5}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("data"):
                for m in data["data"]:
                    attrs = m.get("attributes", {})
                    title_en = attrs.get("title", {}).get("en", "").lower()
                    alt_titles = [t.get("en", "").lower() for t in attrs.get("altTitles", []) if "en" in t]
                    all_titles = set([title_en] + alt_titles)
                    search_lower = title.lower()
                    if search_lower in all_titles:
                        return m["id"], "exact_title"
                    # Check if any alt title contains the search term
                    for t in all_titles:
                        if search_lower in t or t in search_lower:
                            return m["id"], "fuzzy_title"
                return data["data"][0]["id"], "first_match"
    except Exception:
        pass
    return None, None

async def get_chapters(client, uuid):
    try:
        r = await client.get(f"{MANGADEX_API}/manga/{uuid}/aggregate", params={"translatedLanguage[]": "en"}, timeout=15)
        if r.status_code == 200:
            volumes = r.json().get("volumes", {})
            total = sum(len(v.get("chapters", {})) for v in volumes.values())
            return total
    except Exception:
        pass
    return None

async def main():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    
    # Get orphan manga/manhwa
    cur.execute("""
        SELECT c.id, c.title, c.type, c.external_id, c.total_chapters
        FROM content c WHERE c.type IN ('manga', 'manhwa')
        AND NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
        ORDER BY c.id
    """)
    items = cur.fetchall()
    print(f"Still orphan manga/manhwa: {len(items)}")
    
    found = 0
    
    async with httpx.AsyncClient(timeout=15) as client:
        for idx, (cid, title, ctype, ext, cur_ch) in enumerate(items):
            mal_id = ext.replace("mal:", "") if ext and ext.startswith("mal:") else None
            en_titles = TITLE_MAP.get(title, [title])
            
            uuid = None
            method = None
            
            for en_title in en_titles:
                uuid, method = await search_mangadex(client, en_title, mal_id)
                if uuid:
                    print(f"  [{idx+1}] ID={cid}: '{title}' -> '{en_title}' -> {uuid[:12]} ({method})")
                    break
            
            if uuid:
                ch_count = await get_chapters(client, uuid)
                cur.execute("UPDATE content SET external_id=?, total_chapters=?, updated_at=? WHERE id=?",
                           (f"mdx:{uuid}", ch_count or cur_ch, datetime.utcnow().isoformat(), cid))
                
                # Check if MangaDex site already exists
                cur.execute("SELECT id FROM site WHERE content_id=? AND site_name='MangaDex'", (cid,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead)
                        VALUES (?, 'MangaDex', ?, 1, 0)
                    """, (cid, f"https://mangadex.org/title/{uuid}"))
                
                db.commit()
                found += 1
                print(f"    -> Added MangaDex site, chapters={ch_count}")
            else:
                print(f"  [{idx+1}] ID={cid}: '{title}' -> STILL NOT FOUND")
            
            await asyncio.sleep(0.5)
    
    print(f"\n=== RETRY RESULTS ===")
    print(f"  Found: {found}/{len(items)}")
    
    # Final orphan count
    cur.execute("""
        SELECT COUNT(*) FROM content c WHERE c.type IN ('manga', 'manhwa')
        AND NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id = c.id
            AND (s.is_dead IS NULL OR s.is_dead = 0)
        )
    """)
    still_orphan = cur.fetchone()[0]
    print(f"  Still orphan manga/manhwa: {still_orphan}")
    
    cur.execute("SELECT id, title, type FROM content c WHERE c.type IN ('manga','manhwa') AND NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id = c.id AND (s.is_dead IS NULL OR s.is_dead = 0))")
    for r in cur.fetchall():
        print(f"    ID={r[0]:3d} {r[2]:10s} {r[1]}")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
