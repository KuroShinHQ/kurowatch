import sqlite3, re

conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')

# Site kayitlari
rows = conn.execute(
    "SELECT s.id, s.content_id, s.site_url, c.title "
    "FROM site s JOIN content c ON c.id = s.content_id "
    "WHERE s.site_url LIKE '%tranimeizle%'"
).fetchall()

ok_sites = [r for r in rows if re.search(r'-\d+-bolum', r[2] or '')]
bozuk_sites = [r for r in rows if not re.search(r'-\d+-bolum', r[2] or '')]

print(f"=== SITE KAYITLARI ===")
print(f"TOPLAM: {len(rows)}  OK: {len(ok_sites)}  BOZUK: {len(bozuk_sites)}")
for r in bozuk_sites:
    print(f"  BOZUK content={r[1]} | {r[2]} | {r[3][:40]}")

# OK sitelerin episode URL'lerini kontrol et (orneklem)
print(f"\n=== EPISODE URL ORNEKLEMI (ilk 5 OK site) ===")
for r in ok_sites[:5]:
    cid = r[1]
    eps = conn.execute(
        "SELECT number, url FROM episode WHERE content_id=? AND season=1 ORDER BY number LIMIT 5",
        (cid,)
    ).fetchall()
    print(f"\n{r[3][:40]} (content={cid})")
    print(f"  Site URL: {r[2]}")
    for ep in eps:
        tag = "OK" if ep[1] and 'tranimeizle' in (ep[1] or '') else "BOZUK/YOK"
        print(f"  Ep{ep[0]}: [{tag}] {(ep[1] or 'None')[:70]}")

# Bozuk episode URL'leri sayisi
total_eps = conn.execute(
    "SELECT COUNT(*) FROM episode e "
    "JOIN site s ON s.content_id = e.content_id "
    "WHERE s.site_url LIKE '%tranimeizle%'"
).fetchone()[0]

bad_eps = conn.execute(
    "SELECT COUNT(*) FROM episode e "
    "JOIN site s ON s.content_id = e.content_id "
    "WHERE s.site_url LIKE '%tranimeizle%' AND (e.url IS NULL OR e.url NOT LIKE '%tranimeizle%')"
).fetchone()[0]

print(f"\n=== EPISODE OZET ===")
print(f"Tranimeizle iceriklerin toplam bolumu: {total_eps}")
print(f"Tranimeizle URL'si olmayan bolumler: {bad_eps}")

conn.close()
