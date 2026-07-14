"""
SOHBET-164 v2 — 113 FİLM MIGRATION: hdfilmcehennemi.nl/720pizle → hdfilmcehennemi.now
=====================================================================================

v2 improvements:
- Manual Turkish title map for known English titles
- Multi-result selection: pick best by title similarity + year match
- "Serisi" handling: pick first/oldest film of series
- Additional English title fallbacks
- Year-aware scoring (prefer exact year match)
"""
import asyncio, httpx, re, json, sqlite3, os
from urllib.parse import quote
from difflib import SequenceMatcher

DB = os.path.join("memory", "kurowatch.db")
HDFC_SEARCH = "https://www.hdfilmcehennemi.now/wp-json/wp/v2/search"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
HDRS = {"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8", "Accept": "application/json,*/*"}

_TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

def normalize(s):
    s = s.lower().strip()
    s = s.translate(_TR_MAP)
    s = re.sub(r'\(([^)]+)\)', '', s)
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def title_similarity(a, b):
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    base = SequenceMatcher(None, a, b).ratio()
    if a in b or b in a:
        base = max(base, 0.85)
    return base

def extract_year_from_url(url):
    m = re.search(r'-(\d{4})-izle', url)
    return int(m.group(1)) if m else None

# Manual Turkish title map — based on _sohbet164_test_tr.py results
TITLE_MAP = {
    # English → Turkish (or best search query)
    "3 Idiots": ["3 Aptal"],
    "A Beautiful Mind": ["Akıl Oyunları"],
    "A.R.O.G": ["A.R.O.G", "Arog"],
    "Abimm": ["Abimm"],
    "Asena ve Oniriks": ["Asteriks ve Oniriks", "Asteriks Obelix"],
    "Asteriks ve Oniriks": ["Asteriks ve Oniriks", "Asteriks Obelix"],
    "Avengers": ["Yenilmezler"],
    "Batman Serisi": ["Batman"],
    "Cem Yılmaz Fundamentals": ["CM101MMXI", "Fundamentals"],
    "Chihiro Gidişi": ["Ruhların Kaçışı", "Chihiro"],
    "Corpse Bride": ["Ölü Gelin", "Corpse Bride"],
    "Dabbe Serisi": ["Dabbe"],
    "Edge of Tomorrow": ["Yarının Sınırında"],
    "Fast & Furious": ["Hızlı Ve Öfkeli"],
    "Fight Club": ["Dövüş Kulübü"],
    "Filistin": ["Filistin"],
    "Finding Nemo": ["Kayıp Balık Nemo"],
    "Fetih 1453": ["Fetih 1453"],
    "Fury": ["Öfke"],
    "Ghost Rider": ["Hayalet Sürücü", "Ghost Rider"],
    "Gladiator": ["Gladyatör"],
    "Gladio": ["Gladio"],
    "Hababam Sınıfı (Yeni Nesil)": ["Hababam Sınıfı"],
    "Hancock": ["Hancock"],
    "Harry Potter Serisi": ["Harry Potter"],
    "Howl's Moving Castle": ["Yürüyen Şato", "Howls Moving Castle"],
    "I Am Legend": ["Ben Efsaneyim", "I Am Legend"],
    "Ice Age": ["Buz Devri"],
    "In Time": ["Zamana Karşı"],
    "Inception": ["Başlangıç"],
    "Joker (2019)": ["Joker"],
    "Kurtlar Vadisi Irak": ["Kurtlar Vadisi Irak"],
    "Lion King": ["Aslan Kral"],
    "Léon: The Professional": ["Sevginin Gücü"],
    "Matrix Serisi": ["Matrix"],
    "New York'ta Beş Minare": ["New York'ta Beş Minare"],
    "No Country for Old Men": ["İhtiyarlara Yer Yok"],
    "Pacific Rim": ["Pasifik Savaşı", "Pacific Rim"],
    "Percy Jackson Serisi": ["Percy Jackson"],
    "Pirates of the Caribbean": ["Karayip Korsanları"],
    "Planet of the Apes": ["Maymunlar Cehennemi"],
    "Real Steel": ["Çelik Yumruk", "Real Steel"],
    "Recep İvedik Üçlemesi": ["Recep İvedik"],
    "Resident Evil Serisi": ["Resident Evil", "Ölümcül Deney"],
    "Shark Tale": ["Köpek Balığı Hikayesi", "Hikaye Masalı"],
    "Sherlock Holmes Serisi": ["Sherlock Holmes"],
    "Spider-Man": ["Örümcek Adam"],
    "Spirited Away": ["Ruhların Kaçışı"],
    "Split": ["Parçalanmış", "Split"],
    "Terminator Serisi": ["Terminator"],
    "The Collector": ["Koleksiyoncu"],
    "The Godfather": ["Baba"],
    "The Green Mile": ["Yeşil Yol"],
    "The Hobbit: An Unexpected Journey": ["Hobbit"],
    "The Hunger Games": ["Açlık Oyunları"],
    "The Incredibles": ["İnanılmaz Aile"],
    "The Lord of the Rings": ["Yüzüklerin Efendisi"],
    "The Maze Runner": ["Labirent"],
    "The Mummy": ["Mumya"],
    "The Revenant": ["Diriliş"],
    "The Scorpion King Serisi": ["Akrep Kral", "Scorpion King"],
    "The Shawshank Redemption": ["Esaretin Bedeli"],
    "The Wolf of Wall Street": ["Para Avcısı"],
    "Toy Story": ["Oyuncak Hikayesi"],
    "Transformers Serisi": ["Transformers"],
    "Twilight": ["Alacakaranlık"],
    "Undisputed": ["Yenilmez"],
    "WALL-E": ["Walle", "Wall-E"],
    "World War Z": ["Dünya Savaşı Z", "World War Z"],
    "Yahşi Batı": ["Yahşi Batı"],
}

# For multi-result queries, which result to pick (index, or 'best' for auto)
# Some series should map to a specific film (e.g., first film of series)
SERIES_PICK = {
    "Avengers": "first",          # Yenilmezler 4
    "Batman Serisi": "the_batman",  # The Batman (modern)
    "Dabbe Serisi": "first",       # Dabbe (first)
    "Fast & Furious": "first",     # Hızlı ve Öfkeli 10 or first
    "Harry Potter Serisi": "first",
    "Matrix Serisi": "first",
    "Recep İvedik Üçlemesi": "first",
    "Resident Evil Serisi": "first",
    "Sherlock Holmes Serisi": "exact",   # pick "Sherlock Holmes" (no suffix)
    "Spider-Man": "first",
    "Terminator Serisi": "first",
    "The Hobbit: An Unexpected Journey": "first",
    "The Hunger Games": "first",
    "The Lord of the Rings": "first",  # Kralın Dönüşü or first
    "The Maze Runner": "exact",         # pick "Labirent" (no suffix)
    "The Mummy": "first",
    "The Revenant": "exact",            # pick "Diriliş" (no suffix, 2015)
    "Toy Story": "first",
    "Transformers Serisi": "first",
    "Twilight": "first",
    "Undisputed": "first",
    "The Collector": "exact",           # pick "Koleksiyoncu" (no suffix)
    "Lion King": "exact",               # pick "Aslan Kral" (no suffix)
    "Joker (2019)": "exact",            # pick "Joker" (no suffix)
    "The Incredibles": "exact",         # pick "İnanılmaz Aile" (no suffix)
    "Pirates of the Caribbean": "first",
    "Planet of the Apes": "first",
    "Fury": "exact",                    # might not exist; pick "Öfke" if any
    "The Godfather": "exact",           # tricky — "Baba" matches many
}

async def search_hdfc(client, query, per_page=15):
    try:
        r = await client.get(HDFC_SEARCH, params={"search": query, "per_page": per_page}, timeout=15)
        if r.status_code != 200:
            return []
        data = r.json()
        return [d for d in data if d.get("subtype") == "movies"]
    except Exception as e:
        return []

def pick_result(movie_title, movie_year, candidates, pick_strategy="best"):
    """Pick the best matching result from candidates."""
    if not candidates:
        return None
    if pick_strategy == "first":
        return candidates[0]
    if pick_strategy == "exact":
        # Find candidate whose title matches the search query (no suffix like "2", "3")
        norm_title = normalize(movie_title)
        for c in candidates:
            ct = normalize(c["title"])
            # exact match or candidate title is short (no sequel number)
            if ct == norm_title:
                return c
            # if candidate title doesn't end with a digit, prefer it
            if not re.search(r'\b\d+\b', c["title"]):
                # also check year
                url_year = extract_year_from_url(c["url"])
                if movie_year and url_year == movie_year:
                    return c
                if not movie_year:
                    return c
        # fallback to first
        return candidates[0]
    if pick_strategy == "the_batman":
        for c in candidates:
            if "the batman" in c["title"].lower():
                return c
        return candidates[0]
    # default: best by score
    scored = []
    for c in candidates:
        sim = title_similarity(movie_title, c["title"])
        year_bonus = 0
        url_year = extract_year_from_url(c["url"])
        if movie_year and url_year == movie_year:
            year_bonus = 0.15
        elif movie_year and url_year and abs(url_year - movie_year) <= 1:
            year_bonus = 0.08
        score = sim + year_bonus
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return scored[0][1] if scored else None

async def find_movie(client, movie):
    """Find a movie on hdfilmcehennemi.now. Returns (url, match_title, strategy) or None."""
    title = movie["title"]
    year = movie["release_year"]
    
    # 1. Check TITLE_MAP
    mapped_key = None
    for k in TITLE_MAP:
        if normalize(k) == normalize(title) or k.lower() == title.lower():
            mapped_key = k
            break
    # Also try matching by stripping parenthetical
    if not mapped_key:
        for k in TITLE_MAP:
            # k might be substring of title or vice versa
            if normalize(k) in normalize(title) or normalize(title) in normalize(k):
                mapped_key = k
                break
    
    queries_to_try = []
    pick_strategy = "best"
    if mapped_key:
        queries_to_try = TITLE_MAP[mapped_key]
        # Get pick strategy
        for k, v in SERIES_PICK.items():
            if normalize(k) == normalize(mapped_key):
                pick_strategy = v
                break
    
    # 2. Always add the original title as a fallback query
    if title not in queries_to_try and normalize(title) not in [normalize(q) for q in queries_to_try]:
        queries_to_try.append(title)
    
    # 3. Add English part (parenthetical) as a query
    paren = re.search(r'\(([^)]+)\)', title)
    if paren:
        eng = paren.group(1).strip()
        if len(eng) > 2 and eng not in queries_to_try:
            # Skip if it's just a year
            if not re.match(r'^\d{4}$', eng):
                queries_to_try.append(eng)
    
    # 4. Add year-suffixed query
    if year:
        yq = f"{title} {year}"
        if yq not in queries_to_try:
            queries_to_try.append(yq)
    
    # Try each query, collect all unique candidates
    all_candidates = {}
    for q in queries_to_try[:5]:  # limit to 5 queries
        results = await search_hdfc(client, q)
        for r in results:
            all_candidates[r["id"]] = r
        await asyncio.sleep(0.05)
    
    candidates = list(all_candidates.values())
    if not candidates:
        return None
    
    picked = pick_result(title, year, candidates, pick_strategy)
    if picked:
        return picked["url"], picked["title"], pick_strategy
    return None

async def main():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    
    # Get ALL movies (re-process all 113, not just unmatched — overwrite previous v1 matches)
    cur = db.execute("SELECT id, title, title_tr, release_year FROM content WHERE type='movie' ORDER BY id")
    movies = [dict(r) for r in cur.fetchall()]
    print(f"Total movies: {len(movies)}")
    
    matched = []
    unmatched = []
    
    async with httpx.AsyncClient(headers=HDRS, follow_redirects=True) as cl:
        for i, m in enumerate(movies):
            result = await find_movie(cl, m)
            if result:
                url, match_title, strategy = result
                matched.append({
                    "id": m["id"],
                    "title": m["title"],
                    "year": m["release_year"],
                    "url": url,
                    "match_title": match_title,
                    "strategy": strategy,
                })
                print(f"  [{i+1:3d}/{len(movies)}] OK  {m['title'][:35]:35s} -> {match_title[:30]:30s} | {strategy}")
            else:
                unmatched.append({
                    "id": m["id"],
                    "title": m["title"],
                    "year": m["release_year"],
                })
                print(f"  [{i+1:3d}/{len(movies)}] NO  {m['title'][:35]:35s} | (no candidates)")
    
    print(f"\n=== SUMMARY ===")
    print(f"  Matched:   {len(matched)}/{len(movies)}")
    print(f"  Unmatched: {len(unmatched)}")
    
    with open("_sohbet164_movie_matches_v2.json", "w", encoding="utf-8") as f:
        json.dump({"matched": matched, "unmatched": unmatched}, f, indent=2, ensure_ascii=False)
    
    # === DB UPDATE ===
    print(f"\n=== DB UPDATE ===")
    updated_sites = 0
    updated_eps = 0
    inserted_sites = 0
    
    for m in matched:
        cid = m["id"]
        new_url = m["url"]
        
        # 1. Mark existing dead sites as dead (hdfilmcehennemi.nl, 720pizle, hdfilmcehennemi.io)
        cur = db.execute("""
            UPDATE site SET is_dead=1, is_primary=0
            WHERE content_id=? AND (
                site_url LIKE '%hdfilmcehennemi.nl%' OR
                site_url LIKE '%720pizle%' OR
                site_url LIKE '%hdfilmcehennemi.io%' OR
                site_name LIKE '%hdfilmcehennemi.nl%' OR
                site_name LIKE '%720pizle%'
            )
        """, (cid,))
        updated_sites += cur.rowcount
        
        # 2. Upsert .now site
        existing = db.execute("SELECT id FROM site WHERE content_id=? AND site_url LIKE '%hdfilmcehennemi.now%'", (cid,)).fetchone()
        if existing:
            db.execute("UPDATE site SET site_url=?, site_name='hdfilmcehennemi.now', is_primary=1, is_dead=0 WHERE id=?", (new_url, existing[0]))
        else:
            db.execute("""
                INSERT INTO site (content_id, site_name, site_url, is_primary, latest_known_ep, is_dead)
                VALUES (?, 'hdfilmcehennemi.now', ?, 1, 1, 0)
            """, (cid, new_url))
            inserted_sites += 1
        
        # 3. Update ALL episode URLs to new .now URL
        # Movies typically have 1 episode but some have multiple (data anomaly)
        cur = db.execute("""
            UPDATE episode SET url=?
            WHERE content_id=? AND (
                url LIKE '%hdfilmcehennemi.nl%' OR
                url LIKE '%720pizle%' OR
                url LIKE '%crunchyroll%' OR
                url LIKE '%tranimaci%' OR
                url LIKE '%hdfilmcehennemi.io%' OR
                url IS NULL OR url=''
            )
        """, (new_url, cid))
        updated_eps += cur.rowcount
    
    db.commit()
    print(f"  Sites marked dead: {updated_sites}")
    print(f"  Sites inserted:    {inserted_sites}")
    print(f"  Episodes updated:  {updated_eps}")
    
    print(f"\n=== UNMATCHED (still failing) ===")
    for u in unmatched:
        print(f"  c.id={u['id']:4d} {u['title']}")
    
    db.close()
    print(f"\n=== DONE — Movie migration v2 complete ===")

if __name__ == "__main__":
    asyncio.run(main())
