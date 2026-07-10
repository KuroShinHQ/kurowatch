"""
SOHBET-139 Kanıt Raporu
- SORUN 1: mangaokutr.com → ragnarscans.net episode URL fix (1721 güncelleme)
- SORUN 2+3: Dizi/film/cartoon download butonları fix (app.js scope bug)
"""
import json, os, sys, sqlite3, datetime

DB = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet139")
os.makedirs(OUT, exist_ok=True)

def q(conn, sql, params=()):
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]

conn = sqlite3.connect(DB)
report = {"generated": datetime.datetime.now().isoformat(), "findings": {}}

# ── SORUN 1: mangaokutr.com URL fix ──
print("=== SORUN 1: mangaokutr.com → ragnarscans.net ===")
rows = q(conn, "SELECT COUNT(*) as cnt FROM episode WHERE url LIKE '%mangaokutr.com%'")
remaining = rows[0]["cnt"]
print(f"  Kalan mangaokutr.com URL: {remaining}")
report["findings"]["mangaokutr_remaining"] = remaining

rows2 = q(conn, "SELECT COUNT(*) as cnt FROM episode WHERE url LIKE '%ragnarscans.net%'")
ragnar_count = rows2[0]["cnt"]
print(f"  ragnarscans.net URL (yeni): {ragnar_count}")
report["findings"]["ragnarscans_total"] = ragnar_count

# ── SORUN 2+3: Site coverage by type ──
print("\n=== SORUN 2+3: Episode URL Coverage by Type ===")
rows = q(conn, """
    SELECT c.type,
           COUNT(e.id) as total_eps,
           COUNT(e.id) FILTER(WHERE e.url IS NOT NULL AND e.url != '') as url_eps,
           COUNT(DISTINCT c.id) as total_contents,
           COUNT(DISTINCT c.id) FILTER(
               WHERE e.url IS NULL OR e.url = ''
           ) as contents_missing_urls
    FROM episode e
    JOIN content c ON c.id = e.content_id
    GROUP BY c.type ORDER BY c.type
""")
coverage = {}
for r in rows:
    pct = round(r["url_eps"] / r["total_eps"] * 100, 1) if r["total_eps"] else 0
    coverage[r["type"]] = {
        "total_eps": r["total_eps"],
        "with_urls": r["url_eps"],
        "url_pct": pct,
        "total_contents": r["total_contents"],
        "contents_with_missing": r["contents_missing_urls"],
    }
    print(f"  {r['type']}: {r['url_eps']}/{r['total_eps']} ({pct}%) — {r['contents_missing_urls']}/{r['total_contents']} contents affected")
report["findings"]["ep_url_coverage"] = coverage

# ── Dexter: specific test case ──
print("\n=== Dexter (test case) ===")
rows = q(conn, """
    SELECT c.id, c.title, c.type
    FROM content c WHERE c.title LIKE '%Dexter%'
""")
dexter_sites = {}
for r in rows:
    sites = q(conn, "SELECT id, site_url, site_name, is_dead FROM site WHERE content_id = ?", (r["id"],))
    eps = q(conn, "SELECT COUNT(*) as cnt, COUNT(url) FILTER(WHERE url IS NOT NULL AND url != '') as url_cnt FROM episode WHERE content_id = ?", (r["id"],))
    print(f"  content#{r['id']} '{r['title']}' ({r['type']}): {eps[0]['cnt']} eps, {eps[0]['url_cnt']} with URLs")
    for s in sites:
        print(f"    site#{s['id']}: {s['site_name']} dead={s['is_dead']} url={s['site_url'][:80]}")
    dexter_sites[str(r["id"])] = {
        "title": r["title"],
        "type": r["type"],
        "total_eps": eps[0]["cnt"],
        "urls": eps[0]["url_cnt"],
        "sites": sites,
    }
report["findings"]["dexter"] = dexter_sites

# ── Frontend fix verification ──
print("\n=== Frontend Fix Verification ===")
appjs = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "app.js")
with open(appjs, "r", encoding="utf-8") as f:
    content = f.read()

# Check the fix exists
fixes = {
    "primarySite_param": "function _epHtml(e, primarySite)" in content,
    "primarySite_call": "_epHtml(e, primarySite)" in content,
    "fbSite_simplified": "const fbSite = primarySite || null" in content,
}
for k, v in fixes.items():
    print(f"  {k}: {'✔' if v else '✘'}")
report["findings"]["frontend_fix"] = fixes

# ── Summary ──
print("\n=== ÖZET ===")
print(f"  [{report['findings']['mangaokutr_remaining']}] mangaokutr.com URL kaldı → {'BAŞARILI' if report['findings']['mangaokutr_remaining'] == 0 else 'BAŞARISIZ'}")
for ctype, cv in coverage.items():
    btn_status = "var" if cv["url_pct"] < 100 else "gerekmez"
    if ctype in ("series", "movie", "cartoon"):
        print(f"  [{cv['contents_with_missing']}/{cv['total_contents']}] {ctype} → fallback butonu: {btn_status}")
print(f"  Frontend fix: {'TAMAM' if all(fixes.values()) else 'EKSİK'}")

# Save report
report_path = os.path.join(OUT, "rapor.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\nRapor kaydedildi: {report_path}")

conn.close()
