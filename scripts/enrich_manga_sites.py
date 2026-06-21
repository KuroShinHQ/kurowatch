"""
enrich_manga_sites.py — ragnarscans.net + hayalistic.blog için manga/manhwa eşleştir.
Bulunanları DB'ye ekle, bulunamayanları ESLESMEYEN listesi için döndür.
"""
import json, re, sqlite3
from pathlib import Path

DB = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
CATALOGS = Path("/mnt/c/Kuroshin/kurowatch/scripts/site_catalogs.json")

_TR_MAP = str.maketrans("üöşçğıİÜÖŞÇĞ", "uoscgiuoscgg")

def to_slug(s):
    s = s.lower().strip().translate(_TR_MAP)
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"[\s\-]+", "-", s).strip("-")
    return s

def slug_variants(title):
    full = to_slug(title)
    parts = full.split("-")
    variants = [full]
    # Prefix varyantları (min 8 char, 2+ kelime)
    for n in range(2, min(len(parts), 6)):
        c = "-".join(parts[:n])
        if len(c) >= 8 and c not in variants:
            variants.append(c)
    # Parantez içini çıkar: "Title (Alt Başlık)" → "title"
    no_paren = re.sub(r'\s*\([^)]*\)', '', title).strip()
    if no_paren != title:
        variants.append(to_slug(no_paren))
    return variants

def lookup(index_slugs, variants):
    """Exact match önce, sonra prefix."""
    for v in variants:
        if v in index_slugs:
            return v
    for v in variants:
        if len(v) < 8:
            continue
        matches = [s for s in index_slugs if s.startswith(v + "-") or s == v]
        if matches:
            return min(matches, key=len)
    return None

def add_to_db(content_id, site_name, url):
    conn = sqlite3.connect(DB)
    exists = conn.execute(
        "SELECT 1 FROM site WHERE content_id=? AND site_url=?", (content_id, url)
    ).fetchone()
    if not exists:
        conn.execute(
            "INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead) VALUES (?,?,?,0,0)",
            (content_id, site_name, url)
        )
        conn.commit()
    conn.close()

def get_unmatched():
    conn = sqlite3.connect(DB)
    working = ['turkanime', 'anizm', 'tranimaci', 'mangawow', 'ragnarscans', 'hayalistic']
    cond = ' OR '.join([f"s.site_url LIKE '%{k}%'" for k in working])
    rows = conn.execute(f'''
        SELECT c.id, c.type, c.title
        FROM content c
        WHERE c.type IN ('manga', 'manhwa')
        AND NOT EXISTS (
            SELECT 1 FROM site s WHERE s.content_id=c.id AND ({cond})
        )
        ORDER BY c.type, c.title
    ''').fetchall()
    conn.close()
    return [{"id": r[0], "type": r[1], "title": r[2]} for r in rows]

def main():
    catalogs = json.loads(CATALOGS.read_text())
    rg = catalogs.get("ragnarscans", {})
    hy = catalogs.get("hayalistic", {})
    rg_slugs = set(rg.keys())
    hy_slugs = set(hy.keys())

    targets = get_unmatched()
    print(f"Eşleştirilecek manga/manhwa: {len(targets)}")

    found_rg = found_hy = not_found = 0
    not_found_list = []

    for item in targets:
        cid, ctype, title = item["id"], item["type"], item["title"]
        variants = slug_variants(title)

        # ragnarscans.net dene
        match = lookup(rg_slugs, variants)
        if match:
            url = rg[match]
            add_to_db(cid, "ragnarscans.net", url)
            print(f"  ✅ RG [{cid}] {title[:40]:40} → {match}")
            found_rg += 1
            continue

        # hayalistic.blog dene
        match = lookup(hy_slugs, variants)
        if match:
            url = hy[match]
            add_to_db(cid, "hayalistic.blog", url)
            print(f"  ✅ HY [{cid}] {title[:40]:40} → {match}")
            found_hy += 1
            continue

        not_found_list.append(item)
        not_found += 1

    print(f"\nragnarscans: +{found_rg} | hayalistic: +{found_hy} | bulunamadı: {not_found}")
    return not_found_list

if __name__ == "__main__":
    not_found = main()
    # Bulunamayanları JSON'a yaz (rapor script'i için)
    Path("/mnt/c/Kuroshin/kurowatch/scripts/manga_not_found.json").write_text(
        json.dumps(not_found, ensure_ascii=False, indent=2)
    )
