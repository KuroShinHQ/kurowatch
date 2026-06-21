"""
Tüm manga/manhwa sitelerini tek seferde test et.
DB'deki gerçek chapter URL'lerini kullan, yoksa manuel URL dene.
Madara: ?style=list + reading-content/img kontrol
"""
import sqlite3
import httpx
import re
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

SKIP_WORDS = ("logo", "favicon", "banner", "avatar", "icon", "themes",
              "placeholder", "spinner", "loading", "gravatar", "elementor")

# DB'den site bazında 1 chapter URL çek
conn = sqlite3.connect('/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT s.site_url, s.site_name, c.type,
           (SELECT e2.url FROM episode e2 WHERE e2.content_id = c.id
            ORDER BY e2.number ASC LIMIT 1) as ep_url
    FROM site s JOIN content c ON c.id = s.content_id
    WHERE (c.type = 'manga' OR c.type = 'manhwa')
      AND s.site_url IS NOT NULL AND s.site_url != ''
    GROUP BY substr(s.site_url, 1, 40)
    ORDER BY s.site_url
""")
db_sites = cur.fetchall()
conn.close()

# Manuel eklemeler (DB'de yok ama test etmek istediğimiz)
MANUAL_SITES = [
    ("mangawow.com",     "manga", "https://mangawow.com/manga/the-hunter/bolum-1/"),
    ("mangakeyf.com",    "manga", "https://mangakeyf.com/manga/"),
    ("mangahost.net",    "manga", "https://mangahost.net/"),
    ("okumangatr.com",   "manga", "https://okumangatr.com/"),
    ("mangadenizi.com",  "manga", "https://mangadenizi.com/"),
    ("turkmanga.net",    "manga", "https://turkmanga.net/"),
    ("mangaturk.org",    "manga", "https://mangaturk.org/"),
    ("turkmanga.com.tr", "manga", "https://turkmanga.com.tr/manga/above-all-gods/bolum-1/"),
]

# Site bazında birleştir (duplikasyon kaldır)
tested_domains = set()
all_tests = []

for row in db_sites:
    site_url = row['site_url']
    ep_url = row['ep_url'] or site_url
    # Domain çıkar
    m = re.search(r'https?://(?:www\.)?([^/]+)', site_url)
    domain = m.group(1) if m else site_url[:30]
    if domain in tested_domains:
        continue
    tested_domains.add(domain)
    all_tests.append({
        "domain": domain,
        "type": row['type'],
        "site_url": site_url,
        "ep_url": ep_url,
        "name": row['site_name'],
    })

for domain, mtype, ep_url in MANUAL_SITES:
    if domain not in tested_domains:
        tested_domains.add(domain)
        all_tests.append({
            "domain": domain,
            "type": mtype,
            "site_url": ep_url,
            "ep_url": ep_url,
            "name": domain,
        })

SEP = "=" * 65

results = []

def test_manga_url(domain, ep_url):
    """chapter URL → ?style=list → sayfa img kontrol."""
    # Chapter URL mu series URL mu?
    # Chapter URL: /bolum-N/ veya /chapter-N/ içerir
    is_chapter = bool(re.search(r'/(bolum|chapter|ch|blm)[^/]*/?$', ep_url, re.IGNORECASE))
    if is_chapter:
        list_url = ep_url.rstrip("/") + "/?style=list"
    else:
        list_url = ep_url

    referer = f"https://{domain}/"
    h = dict(HEADERS)
    h["Referer"] = referer

    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers=h) as c:
            r = c.get(list_url)

        status = r.status_code
        html = r.text

        has_reading = "reading-content" in html
        cls_imgs = re.findall(r'wp-manga-chapter-img', html)
        data_srcs = re.findall(
            r'(?:data-src|data-lazy-src|src)=["\']([^"\']*\.(?:jpg|jpeg|png|webp)[^"\']*)["\']',
            html, re.IGNORECASE
        )
        data_srcs = [u for u in data_srcs if not any(s in u.lower() for s in SKIP_WORDS)]
        # URL sayfa gibi görünüyor mu? (genellikle /manga/ veya /upload/ içerir)
        page_imgs = [u for u in data_srcs if re.search(r'/(manga|chapter|upload|chapter-images|wp-content/uploads)', u, re.IGNORECASE)]

        if status == 200 and (len(cls_imgs) >= 3 or len(page_imgs) >= 3):
            verdict = "✅ ÇALIŞIYOR"
        elif status == 200 and has_reading and len(data_srcs) >= 2:
            verdict = "✅ ÇALIŞIYOR"
        elif status == 200 and len(data_srcs) >= 5:
            verdict = "🟡 BELİRSİZ (img var)"
        elif status in (403, 401, 429):
            verdict = f"❌ ERİŞİM REDDEDİLDİ ({status})"
        elif status == 404:
            verdict = "⚠️  404 (URL eski)"
        elif status == 0:
            verdict = "❌ BAĞLANTI HATASI"
        else:
            verdict = f"⚠️  {status} (reading={has_reading}, img={len(data_srcs)})"

        return verdict, status, len(cls_imgs), len(page_imgs), list_url

    except Exception as e:
        return f"❌ HATA: {str(e)[:60]}", 0, 0, 0, list_url


print(SEP)
print("MANGA/MANHWA SİTE TAM TESTİ")
print(f"Toplam: {len(all_tests)} site")
print(SEP)

for t in sorted(all_tests, key=lambda x: x['domain']):
    domain = t['domain']
    ep_url = t['ep_url']
    mtype = t['type']

    verdict, status, cls_imgs, page_imgs, test_url = test_manga_url(domain, ep_url)
    results.append((domain, mtype, verdict, status, cls_imgs, page_imgs, test_url))

    print(f"\n[{mtype:6}] {domain}")
    print(f"  URL    : {test_url[:75]}")
    print(f"  SONUÇ  : {verdict}")
    if cls_imgs or page_imgs:
        print(f"  img    : wp-manga={cls_imgs}, page={page_imgs}")


# ── Özet ──
print(f"\n{SEP}")
print("ÖZET")
print(SEP)

working   = [(d,t,v) for d,t,v,*_ in results if "✅" in v]
uncertain = [(d,t,v) for d,t,v,*_ in results if "🟡" in v]
broken    = [(d,t,v) for d,t,v,*_ in results if "❌" in v or "⚠️" in v]

print(f"\n✅ ÇALIŞIYOR ({len(working)}):")
for d, t, v in working:
    print(f"   {d:35} [{t}]")

print(f"\n🟡 BELİRSİZ ({len(uncertain)}):")
for d, t, v in uncertain:
    print(f"   {d:35} [{t}]")

print(f"\n❌ ÇALIŞMIYOR ({len(broken)}):")
for d, t, v in broken:
    print(f"   {d:35} {v}")
