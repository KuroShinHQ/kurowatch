"""
Kategori bazında içerik sayısı + çalışan site dağılımı.
Hangi içeriğin hangi siteden izlenip/okunup indirilebileceğini göster.
"""
import sqlite3

WORKING_SITES = {
    # Kesin çalışıyor (direkt video/m3u8)
    "tranimaci.com":      ("anime",       "✅ MP4 direkt"),
    "anizm.net":          ("anime",       "✅ M3U8 direkt"),
    # Embed bulundu (yt-dlp test lazım)
    "hdfilmcehennemi.nl": ("dizi/film",   "🟡 embed"),
    "turkanime.tv":       ("anime",       "🟡 embed"),
    "turkanime.co":       ("anime",       "🟡 embed"),
    "dizibox.live":       ("dizi",        "🟡 embed"),
    "diziwatch.ac":       ("dizi",        "🟡 embed (CF)"),
    "tranimeizle.io":     ("anime",       "🔴 CF bot"),
    "tranimeizle.co":     ("anime",       "🔴 CF bot"),
    # Manga siteler
    "mangadex.org":       ("manga",       "✅ API"),
    # 403'ler (şimdilik çalışmıyor)
    "ruyamanga.com":      ("manga",       "🔴 403"),
    "ruyamanga.net":      ("manga",       "🔴 403"),
    "asurascans.com.tr":  ("manga",       "🔴 403"),
    "mangatr.net":        ("manga",       "🔴 bot redirect"),
    "mangaokutr.com":     ("manga",       "🔴 offline"),
}

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. Kategori dağılımı
print("=" * 70)
print("KATEGORİ DAĞILIMI")
print("=" * 70)
cur.execute("SELECT type, COUNT(*) as n FROM content GROUP BY type ORDER BY n DESC")
for r in cur.fetchall():
    print(f"  {r['type']:12} : {r['n']:4} içerik")

# 2. Her içeriğin site URL'leri
cur.execute("""
    SELECT c.id, c.title, c.type,
           GROUP_CONCAT(s.site_url, '|||') as urls,
           GROUP_CONCAT(s.site_name, '|||') as names,
           GROUP_CONCAT(s.is_dead, '|||') as deads
    FROM content c
    LEFT JOIN site s ON s.content_id = c.id
    GROUP BY c.id
""")
rows = cur.fetchall()

# 3. Her içerik için çalışan site var mı?
categories = {
    "anime":   {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "manga":   {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "manhwa":  {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "dizi":    {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "film":    {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "game":    {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
    "other":   {"total": 0, "has_working": 0, "has_broken": 0, "no_site": 0, "working_sites": {}},
}

def classify_url(url):
    """URL → çalışma durumu"""
    if not url:
        return None
    url_lower = url.lower()
    for domain, (_, status) in WORKING_SITES.items():
        if domain in url_lower:
            return status
    return "❓ bilinmiyor"

for row in rows:
    ctype = row['type'] or "other"
    cat = ctype if ctype in categories else "other"
    categories[cat]["total"] += 1

    urls = (row['urls'] or "").split("|||")
    urls = [u.strip() for u in urls if u.strip()]

    if not urls:
        categories[cat]["no_site"] += 1
        continue

    statuses = [classify_url(u) for u in urls if u]
    statuses = [s for s in statuses if s]

    has_working = any("✅" in (s or "") for s in statuses)
    has_yellow  = any("🟡" in (s or "") for s in statuses)
    has_broken  = any("🔴" in (s or "") for s in statuses)

    if has_working or has_yellow:
        categories[cat]["has_working"] += 1
        # Hangi site çalışıyor
        for u in urls:
            for domain, (_, status) in WORKING_SITES.items():
                if domain in u.lower() and ("✅" in status or "🟡" in status):
                    categories[cat]["working_sites"][domain] = categories[cat]["working_sites"].get(domain, 0) + 1
    elif has_broken:
        categories[cat]["has_broken"] += 1
    else:
        categories[cat]["no_site"] += 1

# 4. Özet rapor
print("\n" + "=" * 70)
print("COVERAGE RAPORU — Kategori bazında")
print("=" * 70)

TARGET_CATS = [("anime", "Anime"), ("dizi", "Dizi"), ("film", "Film"),
               ("manga", "Manga"), ("manhwa", "Manhwa"), ("game", "Oyun")]

for ctype, label in TARGET_CATS:
    c = categories[ctype]
    if c["total"] == 0:
        continue
    working_pct = int(100 * c["has_working"] / c["total"]) if c["total"] else 0
    broken_pct  = int(100 * c["has_broken"]  / c["total"]) if c["total"] else 0
    nosite_pct  = int(100 * c["no_site"]     / c["total"]) if c["total"] else 0

    print(f"\n  [{label}] toplam={c['total']}")
    print(f"    ✅/🟡 site var (indir?) : {c['has_working']:4}  ({working_pct}%)")
    print(f"    🔴 kırık site           : {c['has_broken']:4}  ({broken_pct}%)")
    print(f"    ❌ site yok / bilinmiyor: {c['no_site']:4}  ({nosite_pct}%)")

    if c["working_sites"]:
        top = sorted(c["working_sites"].items(), key=lambda x: -x[1])[:5]
        print(f"    Çalışan siteler: " + ", ".join(f"{d}({n})" for d,n in top))

print("\n" + "=" * 70)
print("SİTE BAZINDA İÇERİK SAYISI (tüm tipler)")
print("=" * 70)
cur.execute("""
    SELECT
        CASE
            WHEN s.site_url LIKE '%tranimaci%' THEN 'tranimaci.com'
            WHEN s.site_url LIKE '%anizm.net%' THEN 'anizm.net'
            WHEN s.site_url LIKE '%hdfilmcehennemi%' THEN 'hdfilmcehennemi.nl'
            WHEN s.site_url LIKE '%turkanime.tv%' THEN 'turkanime.tv'
            WHEN s.site_url LIKE '%turkanime.co%' THEN 'turkanime.co'
            WHEN s.site_url LIKE '%dizibox%' THEN 'dizibox.live'
            WHEN s.site_url LIKE '%diziwatch%' THEN 'diziwatch.ac'
            WHEN s.site_url LIKE '%tranimeizle.io%' THEN 'tranimeizle.io'
            WHEN s.site_url LIKE '%tranimeizle%' THEN 'tranimeizle.co'
            WHEN s.site_url LIKE '%mangadex%' THEN 'mangadex.org'
            WHEN s.site_url LIKE '%ruyamanga%' THEN 'ruyamanga.*'
            WHEN s.site_url LIKE '%asurascans%' THEN 'asurascans.com.tr'
            WHEN s.site_url LIKE '%mangatr.net%' THEN 'mangatr.net'
            WHEN s.site_url LIKE '%mangaokutr%' THEN 'mangaokutr.com'
            ELSE 'diger: ' || substr(s.site_url, 9, 25)
        END as domain,
        COUNT(DISTINCT s.content_id) as icerik_sayisi,
        c.type
    FROM site s JOIN content c ON c.id = s.content_id
    WHERE s.site_url IS NOT NULL AND s.site_url != ''
    GROUP BY domain, c.type
    ORDER BY icerik_sayisi DESC
    LIMIT 40
""")
for r in cur.fetchall():
    print(f"  {r['domain']:35} | {r['type']:8} | {r['icerik_sayisi']:4} içerik")

conn.close()
