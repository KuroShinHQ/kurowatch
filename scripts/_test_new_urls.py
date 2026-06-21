"""Yeni verilen URL'leri test et."""
import httpx, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}
SKIP = ("logo","favicon","banner","avatar","icon","themes","placeholder","spinner","loading","gravatar","elementor")

TESTS = [
    ("golgebahcesi.com",     "manga",  "https://golgebahcesi.com/manga/son-seviye-caylak/bolum/chapter-1"),
    ("webtoonhatti.club",    "manhwa", "https://webtoonhatti.club/webtoon/buyu-imparatoru/bolum-1/"),
    ("ruyamanga.net",        "manga",  "https://ruyamanga.net/manga/solo-leveling/bolum-0/"),
    ("uzaymanga.com",        "manga",  "https://uzaymanga.com/manga/iskeletleri-canlandirabilirim/1-bolum-oku"),
    ("ragnarscans.net",      "manga",  "https://ragnarscans.net/manga/a-dragonslayers-peerless-regression/bolum-1/"),
]

SEP = "=" * 65
print(SEP)

for domain, mtype, url in TESTS:
    # ?style=list ekle (chapter URL ise)
    is_chapter = bool(re.search(r'/(bolum|chapter|ch|blm)[^/]*/?$', url, re.IGNORECASE))
    test_url = url.rstrip("/") + "/?style=list" if is_chapter else url

    h = dict(HEADERS)
    h["Referer"] = f"https://{domain}/"

    print(f"\n[{mtype}] {domain}")
    print(f"  URL: {test_url[:75]}")

    try:
        with httpx.Client(timeout=12, follow_redirects=True, headers=h) as c:
            r = c.get(test_url)

        html = r.text
        has_reading = "reading-content" in html
        cls_imgs = len(re.findall(r'wp-manga-chapter-img', html))
        data_srcs = re.findall(r'(?:data-src|data-lazy-src|src)=["\']([^"\']*\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.IGNORECASE)
        data_srcs = [u for u in data_srcs if not any(s in u.lower() for s in SKIP)]
        page_imgs = [u for u in data_srcs if re.search(r'/(manga|chapter|upload|webtoon|content)', u, re.IGNORECASE)]

        print(f"  HTTP: {r.status_code} | len={len(html)}")
        print(f"  reading-content: {'VAR' if has_reading else 'YOK'} | wp-manga-img: {cls_imgs} | sayfa-img: {len(page_imgs)}")

        if r.status_code == 200 and (cls_imgs >= 3 or len(page_imgs) >= 3):
            print(f"  >>> ✅ ÇALIŞIYOR ({max(cls_imgs, len(page_imgs))} sayfa)")
            if page_imgs:
                print(f"  İlk img: {page_imgs[0][:80]}")
        elif r.status_code == 200 and len(data_srcs) >= 5:
            print(f"  >>> 🟡 BELİRSİZ ({len(data_srcs)} img)")
        elif r.status_code in (403, 401, 429):
            print(f"  >>> ❌ ERİŞİM REDDEDİLDİ ({r.status_code})")
        elif r.status_code == 404:
            print(f"  >>> ⚠️  404 (URL değişmiş)")
        else:
            print(f"  >>> ⚠️  {r.status_code}")
    except Exception as e:
        print(f"  >>> ❌ HATA: {e}")

print(f"\n{SEP}")
