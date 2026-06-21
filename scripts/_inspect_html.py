"""HTML içinden link yapısına bak."""
import httpx
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

def check(label, url, referer=None):
    h = dict(HEADERS)
    if referer:
        h["Referer"] = referer
    print(f"\n{'='*60}")
    print(f"{label} | {url}")
    try:
        with httpx.Client(timeout=15, follow_redirects=True, headers=h) as c:
            r = c.get(url)
        print(f"Status: {r.status_code} | len={len(r.text)}")
        # Tüm href'leri bul
        all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', r.text)
        # İlgili filtreleme
        interesting = [x for x in all_hrefs if any(k in x.lower() for k in ['bolum', 'episode', 'sezon', 'izle', 'watch', 'ep-', '-ep', '/ep'])]
        print(f"İlgili linkler ({len(interesting)}):")
        for l in interesting[:10]:
            print(f"  {l[:100]}")
        if not interesting:
            print("  (yok) — tüm linklerden ilk 10:")
            for l in all_hrefs[:10]:
                print(f"  {l[:100]}")
    except Exception as e:
        print(f"HATA: {e}")

check("turkanime.tv seri", "https://www.turkanime.tv/anime/ore-dake-level-up-na-ken-how-to-get-stronger", "https://www.turkanime.tv/")
check("dizibox.live seri", "https://www.dizibox.live/diziler/dungeon-meshi/", "https://www.dizibox.live/")
check("diziwatch.ac bolum1", "https://diziwatch.ac/dizi/solo-leveling/sezon-1/bolum-1", "https://diziwatch.ac/")
