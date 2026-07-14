"""Test all 113 films on hdfc.nl with multiple slug variants"""
import asyncio, httpx, re, os, json, sqlite3

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "..", "..", "memory", "kurowatch.db")
db_path = os.path.normpath(db_path)

def slugify(s):
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\sçğıöşü-]', '', s)
    s = re.sub(r'\s+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')

async def main():
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    
    cur = db.execute("SELECT id, title FROM content WHERE type='movie' ORDER BY id")
    films = [dict(r) for r in cur.fetchall()]
    
    async with httpx.AsyncClient(timeout=12, follow_redirects=True,
                                  headers={'User-Agent': 'Mozilla/5.0', 'Accept-Language': 'tr-TR,tr;q=0.9'}) as cl:
        
        matches = []
        # Known working slugs from the catalog
        known_slugs = {
            'esaretin-bedeli': '1-esaretin-bedeli-film-izle-hdf-hdf-6',
            'the-shawshank-redemption': '1-esaretin-bedeli-film-izle-hdf-hdf-6',
            'fight-club': '1-dovus-kulubu-izle-6',
            'dovus-kulubu': '1-dovus-kulubu-izle-6',
            'american-psycho': 'american-psycho-6',
            'the-godfather': 'hd-the-godfather-izle-10',
            'godfather': 'hd-the-godfather-izle-10',
            'avatar': 'avatar-fire-and-ash-51',
            'batman': 'batman-kara-sovalye-hd-film-izle-hdf-hdf-7',
            'the-dark-knight': 'batman-kara-sovalye-hd-film-izle-hdf-hdf-7',
            'kara-sovalye': 'batman-kara-sovalye-hd-film-izle-hdf-hdf-7',
            'spider-man': 'spider-man-brand-new-day',
            'pulp-fiction': 'ucuz-roman-izle-hdf-7',
            'ucuz-roman': 'ucuz-roman-izle-hdf-7',
            'cem-yilmaz-fundamentals': 'cm101mmxi-fundamentals-1',
            'the-mummy': 'lee-cronin-s-the-mummy-7',
            'mummy': 'lee-cronin-s-the-mummy-7',
            'the-lord-of-the-rings': '1-yuzuklerin-efendisi-kralin-donusu-izle-hdf-7',
            'yuzuklerin-efendisi': '1-yuzuklerin-efendisi-kralin-donusu-izle-hdf-7',
            'wall-e': 'wall-e',
            'shark-tale': 'shark-tale',
            'the-collector': 'the-collector',
            'howls-moving-castle': 'howls-moving-castle',
            'planet-of-the-apes': 'planet-of-the-apes',
        }
        
        # Use known mappings
        match_count = 0
        for film in films:
            title = film['title']
            clean = slugify(title)
            
            # Check if our clean slug matches any known mapping
            if clean in known_slugs:
                url = f"https://www.hdfilmcehennemi.nl/{known_slugs[clean]}/"
                matches.append((film['id'], title, url))
                match_count += 1
                print(f"  ✅ [{match_count}] {title[:40]:40s} -> {known_slugs[clean][:50]}")
                continue
            
            # Also check if title parts contain a known key
            found = False
            for key, val in known_slugs.items():
                if key in clean or key in title.lower():
                    url = f"https://www.hdfilmcehennemi.nl/{val}/"
                    matches.append((film['id'], title, url))
                    match_count += 1
                    print(f"  ✅ [{match_count}] {title[:40]:40s} -> {val[:50]} (via '{key}')")
                    found = True
                    break
            if found:
                continue
            
            # Try basic slug on hdfc.nl 
            url = f"https://www.hdfilmcehennemi.nl/{clean}/"
            try:
                r = await cl.get(url, timeout=8)
                if r.status_code == 200 and '<iframe' in r.text and len(r.text) > 20000:
                    matches.append((film['id'], title, url))
                    match_count += 1
                    print(f"  🔍 [{match_count}] {title[:40]:40s} -> {clean[:50]} (DIRECT HIT!)")
                    await asyncio.sleep(0.1)
                    continue
            except:
                pass
            
            # Also try extracting the English part of the title
            paren_match = re.search(r'\(([^)]+)\)', title)
            if paren_match:
                eng_title = paren_match.group(1)
                eng_clean = slugify(eng_title)
                if eng_clean != clean:
                    url = f"https://www.hdfilmcehennemi.nl/{eng_clean}/"
                    try:
                        r = await cl.get(url, timeout=8)
                        if r.status_code == 200 and '<iframe' in r.text and len(r.text) > 20000:
                            matches.append((film['id'], title, url))
                            match_count += 1
                            print(f"  🔍 [{match_count}] {title[:40]:40s} -> {eng_clean[:50]} (ENG HIT!)")
                            await asyncio.sleep(0.1)
                            continue
                    except:
                        pass
            
            print(f"  ❌ {title[:50]:50s} (no match)")
            await asyncio.sleep(0.05)
        
        print(f"\n\nTotal matched: {len(matches)}/{len(films)}")
        
        # Save and add to DB
        print("\n=== ADDING TO DATABASE ===")
        added = 0
        for content_id, title, url in matches:
            existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_name LIKE '%hdfilmcehennemi.nl%'", (content_id,)).fetchone()
            if not existing:
                db.execute("INSERT INTO site (content_id, site_name, site_url, is_primary) VALUES (?, ?, ?, ?)",
                           (content_id, "hdfilmcehennemi.nl", url, 0))
                added += 1
            if added > 0 and added % 10 == 0:
                db.commit()
        db.commit()
        print(f"Added {added} new hdfc.nl site records")
        
        # Summary
        print(f"\n=== SUMMARY ===")
        cur = db.execute("""SELECT c.type, c.id, c.title, s.site_name FROM content c
            JOIN site s ON c.id = s.content_id
            WHERE c.type='movie' AND (s.site_name LIKE '%hdfilmcehennemi%' OR s.site_name LIKE '%720pizle%')
            AND s.is_dead != 1
            ORDER BY c.id""")
        count = len(cur.fetchall())
        print(f"Total movie sites with non-dead hdfc/720pizle: {count}")
        
        # Count sitesiz films
        cur = db.execute("""SELECT c.id, c.title FROM content c WHERE c.type='movie' AND c.id NOT IN (
            SELECT content_id FROM site WHERE site_name LIKE '%hdfilmcehennemi%' OR site_name LIKE '%720pizle%'
        )""")
        sitesiz = [dict(r) for r in cur.fetchall()]
        print(f"Films with no hdfc/720pizle site: {len(sitesiz)}")
        for s in sitesiz:
            print(f"  {s['title']}")

if __name__ == "__main__":
    asyncio.run(main())
