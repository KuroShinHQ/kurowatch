"""ESLESMEYEN.md oluştur — bulunamayan anime/manga/manhwa raporu."""
import json, re, sqlite3
from pathlib import Path

DB = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
TA_INDEX = Path("/mnt/c/Kuroshin/kurowatch/scripts/ta_index.json")
CATALOGS = Path("/mnt/c/Kuroshin/kurowatch/scripts/site_catalogs.json")

# Turkanime'de kesinlikle olmayacak içerik işaretleri
NON_ANIME_KEYWORDS = [
    "Arka Sokaklar","Behzat","Kurtlar Vadisi","Sihirli Annem","Çocuklar Duymasın",
    "Seksenler","Doktorlar","Diriliş","Muhteşem Yüzyıl","Kardeş Payı","Geniş Aile",
    "Hababam","Yaprak","Pis Yedili","Maskeli","Kolpaçino","Recep İvedik","Yahşi",
    "Özgürlük","Galip","G.O.R.A","Selena","Abimm","Adanalı","1 Kadın",
    "Breaking Bad","Game of Thrones","Dark ","Dexter","Doctor Who","Mr. Robot",
    "The Walking Dead","The Witcher","Sherlock","Hannibal","Rick and Morty",
    "La Casa","Black Mirror","Squid Game","You ","The Mentalist",
    "Matrix","Harry Potter","Gladiator","Titanic","Fight Club","Inception",
    "Lotr","Lord of the Rings","Hobbit","Hunger Games","Percy Jackson",
    "Spider-Man","Batman","Avengers","Thor","Captain America","Doctor Strange",
    "Deadpool","Green Lantern","Justice League","Venom","Joker (2019)",
    "Captain America", "Iron Man",
    "Cars","Ice Age","Shrek","Toy Story","Finding Nemo","Monsters","Up ","WALL-E",
    "Lion King","Maleficent","Kung Fu Panda","Madagaskar","Shark Tale",
    "Corpse Bride","Spirited Away",
    "Adventure Time","Ben 10","Scooby","Looney","Mickey","Powerpuff",
    "Dexter's Laboratory","Phineas","Regular Show","We Bare Bears",
    "Steven Universe","Gravity Falls","Over the Garden","Uncle Grandpa",
    "Teen Titans Go","Total Drama","Gumball","Ed Edd","Clarence","Generator Rex",
    "Kim Possible","My Little Pony","Ninjago","DreamWorks Dragons",
    "Teletubbies","Yogi Bear","Winnie the Pooh","Johnny Bravo",
    "Max Steel","Megas XLR","Transformers","Sonic","Space Goofs",
    "American Dragon","Alvin","Bakugan","Tom and Jerry",
    "Howl's Moving Castle","My Neighbor Totoro","5 Centimeters",
    "Fast & Furious","3 Idiots","Dabbe","Fetih","Düğün","Esaretin",
    "Para Avcısı","Taşıyıcı","Tetik","Sevginin Gücü","Léon",
    "300 ","300 S","Hancock","In Time","Edge of Tomorrow","Real Steel",
    "Terminator","Resident Evil","Pacific Rim","Split","World War Z",
    "John Wick","V for Vendetta","Hugo","Fury","Ölüm Yarışı",
    "Revenant","Godfather","Scorpion","Mummy","Green Mile","Maze Runner",
    "Shawshank","Wolf of Wall Street","American Psycho",
    "Disney Broken Karaoke","Broken Karaoke",
    "Filistin","New York'ta","Direniş","A Beautiful Mind","Akıl Oyunları",
]

def is_non_anime(title):
    t = title.lower()
    for kw in NON_ANIME_KEYWORDS:
        if kw.lower() in t:
            return True
    return False

def to_slug(s):
    _TR_MAP = str.maketrans("üöşçğıİÜÖŞÇĞ", "uoscgiuoscgg")
    s = s.lower().strip().translate(_TR_MAP)
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"[\s\-]+", "-", s).strip("-")
    return s

def find_in_index(index_slugs, title):
    """Title → turkanime index'te öneri bul."""
    slug = to_slug(title)
    parts = slug.split("-")
    candidates = []
    # Full match
    if slug in index_slugs:
        return [slug]
    # 2-3 kelime prefix
    for n in range(2, min(len(parts), 4)):
        prefix = "-".join(parts[:n])
        if len(prefix) >= 6:
            hits = [s for s in index_slugs if s.startswith(prefix)]
            candidates.extend(hits[:2])
    return list(dict.fromkeys(candidates))[:3]

def main():
    conn = sqlite3.connect(DB)
    working = ['turkanime', 'anizm', 'tranimaci', 'mangawow', 'ragnarscans', 'hayalistic']
    cond = ' OR '.join([f"s.site_url LIKE '%{k}%'" for k in working])

    # Unmatched anime
    anime_rows = conn.execute(f'''
        SELECT c.id, c.title FROM content c
        WHERE c.type = 'anime'
        AND NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond}))
        ORDER BY c.title
    ''').fetchall()

    # Unmatched manga/manhwa
    manga_rows = conn.execute(f'''
        SELECT c.id, c.type, c.title FROM content c
        WHERE c.type IN ('manga','manhwa')
        AND NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond}))
        ORDER BY c.type, c.title
    ''').fetchall()
    conn.close()

    ta_index = set(json.loads(TA_INDEX.read_text()).keys())
    catalogs = json.loads(CATALOGS.read_text())
    rg_slugs = set(catalogs.get("ragnarscans", {}).keys())
    hy_slugs = set(catalogs.get("hayalistic", {}).keys())

    # Anime bölümü
    real_anime = [(cid, t) for cid, t in anime_rows if not is_non_anime(t)]
    non_anime = [(cid, t) for cid, t in anime_rows if is_non_anime(t)]

    lines = ["# ESLESMEYEN İçerikler — Manuel URL Gerekli\n"]
    lines.append(f"> Otomatik eşleştirme yapılamayan içerikler. URL bulunca `[ ]` → `[x]` yap ve ID'yi bildir.\n")

    lines.append(f"\n## 🎌 Anime — turkanime'de bulunamadı ({len(real_anime)} adet)\n")
    lines.append("turkanime.tv/video/SLUG-1-bolum formatında URL gir.\n")
    for cid, title in real_anime:
        suggestions = find_in_index(ta_index, title)
        sug_str = ""
        if suggestions:
            sug_str = f" ← öneri: {', '.join(suggestions[:2])}"
        lines.append(f"- [ ] [{cid}] **{title}**{sug_str}")

    lines.append(f"\n## 📚 Manga ({len([r for r in manga_rows if r[1]=='manga'])} adet)\n")
    for cid, ctype, title in manga_rows:
        if ctype != 'manga':
            continue
        # ragnarscans öneri
        slug = to_slug(title)
        rg_sug = [s for s in rg_slugs if s.startswith(slug[:6]) or slug[:8] in s][:1]
        hy_sug = [s for s in hy_slugs if s.startswith(slug[:6]) or slug[:8] in s][:1]
        sug = ""
        if rg_sug: sug += f" ← RG: ragnarscans.net/manga/{rg_sug[0]}/"
        if hy_sug: sug += f" ← HY: hayalistic.blog/manga/{hy_sug[0]}/"
        lines.append(f"- [ ] [{cid}] **{title}**{sug}")

    lines.append(f"\n## 🗂️ Manhwa ({len([r for r in manga_rows if r[1]=='manhwa'])} adet)\n")
    for cid, ctype, title in manga_rows:
        if ctype != 'manhwa':
            continue
        slug = to_slug(title)
        rg_sug = [s for s in rg_slugs if s.startswith(slug[:6]) or slug[:8] in s][:1]
        hy_sug = [s for s in hy_slugs if s.startswith(slug[:6]) or slug[:8] in s][:1]
        sug = ""
        if rg_sug: sug += f" ← RG: ragnarscans.net/manga/{rg_sug[0]}/"
        if hy_sug: sug += f" ← HY: hayalistic.blog/manga/{hy_sug[0]}/"
        lines.append(f"- [ ] [{cid}] **{title}**{sug}")

    lines.append(f"\n## 🚫 Turkanime'de olmayacak içerikler ({len(non_anime)} adet)")
    lines.append("(Türk dizisi / Batı filmi / cartoon — manuel site URL ekle veya atla)\n")
    for cid, title in non_anime:
        lines.append(f"- [ ] [{cid}] {title}")

    lines.append("\n---")
    lines.append(f"\n**Özet:** Anime {len(real_anime)} | Manga {len([r for r in manga_rows if r[1]=='manga'])} | Manhwa {len([r for r in manga_rows if r[1]=='manhwa'])} | Turkanime-dışı {len(non_anime)}")

    out = "\n".join(lines)
    Path("/mnt/c/Kuroshin/kurowatch/docs/ESLESMEYEN.md").write_text(out, encoding="utf-8")
    print(f"Yazıldı: ESLESMEYEN.md")
    print(f"Anime(gerçek): {len(real_anime)} | Manga: {len([r for r in manga_rows if r[1]=='manga'])} | Manhwa: {len([r for r in manga_rows if r[1]=='manhwa'])} | Batı/Türk: {len(non_anime)}")

main()
