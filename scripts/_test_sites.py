"""
_test_sites.py — Her site için 1 gerçek URL ile indirme testi.
Manga: httpx sync GET + reading-content/img kontrolü
Anime: stream_finder (Playwright) ile embed URL arama
"""
import asyncio
import sys
import re
import httpx
import time

sys.path.insert(0, '/mnt/c/Kuroshin/kurowatch')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

MANGA_TESTS = [
    ("ruyamanga.com",    "manga", "https://www.ruyamanga.com/manga/world-s-apocalypse-online/bolum-165/"),
    ("ruyamanga.net",    "manga", "https://ruyamanga.net/manga/i-am-the-fated-villain/bolum-122/"),
    ("asurascans.com.tr","manga", "https://asurascans.com.tr/manga/bilge-okuyucunun-bakis-acisi/bolum-239/"),
]

ANIME_TESTS = [
    ("tranimaci.com",       "anime", "https://tranimaci.com/video/long-zu-dragon-raja-16-bolum"),
    ("hdfilmcehennemi.nl",  "dizi",  "https://www.hdfilmcehennemi.nl/dizi/dexter-izle-91/sezon-8/bolum-7-hd19/"),
]

NO_URL_SITES = [
    ("turkanime.co",  "anime", "DB'de URL yok"),
    ("diziwatch.com", "dizi",  "DB'de URL yok"),
    ("anizm.net",     "anime", "DB'de URL yok"),
    ("dizibox.live",  "dizi",  "DB'de URL yok"),
    ("mangadex.org",  "manga", "DB'de URL yok"),
]

SEP = "=" * 80


def test_manga_sync(domain, media_type, url):
    list_url = url.rstrip("/") + "/?style=list"
    print(f"\n{SEP}")
    print(f"[MANGA] {domain} | {url[:70]}")
    t0 = time.time()
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            r = client.get(list_url)
        elapsed = time.time() - t0
        print(f"  HTTP status : {r.status_code}  ({elapsed:.1f}s)")
        html = r.text

        has_reading = "reading-content" in html
        imgs_class = re.findall(r'wp-manga-chapter-img', html)
        data_srcs = re.findall(r'(?:data-src|data-lazy-src|src)=["\']([^"\']*\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.IGNORECASE)
        # Temizle (logo/ikon filtrele)
        SKIP = ("logo", "favicon", "banner", "avatar", "icon", "themes", "placeholder")
        data_srcs = [u for u in data_srcs if not any(s in u.lower() for s in SKIP)]

        print(f"  reading-content : {'VAR ✅' if has_reading else 'YOK ❌'}")
        print(f"  wp-manga-img    : {len(imgs_class)}")
        print(f"  görsel URL sayısı: {len(data_srcs)}")
        if data_srcs:
            print(f"  İlk görsel      : {data_srcs[0][:80]}")

        if r.status_code == 200 and (has_reading or len(data_srcs) >= 3):
            print(f"  >>> SONUÇ: ✅ İNDİRİLEBİLİR (~{len(data_srcs)} sayfa)")
        elif r.status_code in (403, 401, 429):
            print(f"  >>> SONUÇ: ❌ ERİŞİM REDDEDİLDİ ({r.status_code})")
        elif r.status_code == 404:
            print(f"  >>> SONUÇ: ❌ SAYFA YOK (404) — URL eski olabilir")
        else:
            print(f"  >>> SONUÇ: ⚠️  BELİRSİZ (status={r.status_code}, reading={has_reading}, img={len(data_srcs)})")
    except Exception as e:
        print(f"  >>> SONUÇ: ❌ HATA — {e}")


async def test_anime_async(domain, media_type, url):
    from backend.downloader.stream_finder import find_stream_url
    print(f"\n{SEP}")
    print(f"[ANİME] {domain} | {url[:70]}")
    t0 = time.time()
    try:
        result = await find_stream_url(url)
        elapsed = time.time() - t0
        print(f"  Süre: {elapsed:.1f}s")
        if result == url:
            print(f"  >>> SONUÇ: ❌ Embed BULUNAMADI (orijinal URL döndü)")
            print(f"  URL: {result[:80]}")
        elif any(x in result for x in ('.m3u8', '.mp4', 'manifest.mpd')):
            print(f"  >>> SONUÇ: ✅ DOĞRUDAN VİDEO BULUNDU")
            print(f"  URL: {result[:80]}")
        else:
            print(f"  >>> SONUÇ: ✅ EMBED/PLAYER BULUNDU (yt-dlp ile indirilebilir)")
            print(f"  Embed: {result[:80]}")
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  >>> SONUÇ: ❌ HATA ({elapsed:.1f}s) — {e}")


async def main():
    print(SEP)
    print("KuroWatch Site Test — Gerçek İndirme Testi")
    print(SEP)

    print("\n--- MANGA SİTELERİ (httpx sync) ---")
    for domain, mt, url in MANGA_TESTS:
        test_manga_sync(domain, mt, url)

    print(f"\n\n--- ANİME/DİZİ SİTELERİ (Playwright stream_finder) ---")
    for domain, mt, url in ANIME_TESTS:
        await test_anime_async(domain, mt, url)

    print(f"\n\n{SEP}")
    print("DB'DE URL OLMAYAN SİTELER (test edilemedi):")
    for domain, mt, reason in NO_URL_SITES:
        print(f"  ❓ {domain:25} | {mt:6} | {reason}")

    print(f"\n{SEP}")
    print("TEST TAMAMLANDI")


if __name__ == "__main__":
    asyncio.run(main())
