"""
TMDB Zenginleştirme — AniList'in bulamadığı içerikler için TMDB API kullanır.

Hedef: cover_url=null olan anime/manhwa/manga içerikler
Özellikle: Western film/dizi (Dexter, Witcher, Titanic vb.)

Gereksinim:
  config.json → "tmdb_api_key": "YOUR_TMDB_READ_ACCESS_TOKEN"
  TMDB ücretsiz key: https://www.themoviedb.org/settings/api

Çalıştır:
  python3 scripts/enrich_tmdb.py
  python3 scripts/enrich_tmdb.py --force   (zaten cover'ı olanları da güncelle)
"""

import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "http://localhost:8099/api"
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
DELAY = 0.35
FORCE = "--force" in sys.argv

_CONFIG_PATH = "C:\\Kuroshin\\kurowatch\\backend\\config.json"
# WSL path fallback
if not __import__("os").path.exists(_CONFIG_PATH):
    _CONFIG_PATH = "/mnt/c/Kuroshin/kurowatch/backend/config.json"


def get_tmdb_key() -> str:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        key = cfg.get("tmdb_api_key", "")
        if key:
            return key
    except Exception:
        pass
    return ""


def api_get(path: str) -> list | dict:
    req = urllib.request.Request(f"{API}/{path.lstrip('/')}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def api_patch(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{API}/{path.lstrip('/')}",
        data=data,
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def tmdb_search(title: str, tmdb_key: str, media_type: str = "multi") -> dict | None:
    """
    TMDB'de arama yapar. media_type: 'multi', 'movie', 'tv'
    Returns: {'cover_url': ..., 'external_id': 'tmdb:123', 'tmdb_type': 'movie'/'tv'}
    """
    # Temizlenmiş başlık (yıl, sezon marker)
    clean = re.sub(r'\s*\([Ss]\d+\)', '', title)
    clean = re.sub(r'\s*\(\d{4}\)', '', clean)
    clean = re.sub(r'\s*\([^)]{4,30}\)$', '', clean)
    clean = clean.strip()

    for q in ([clean] if clean != title else []) + [title]:
        encoded = urllib.parse.quote(q)
        url = f"{TMDB_BASE}/search/{media_type}?query={encoded}&language=tr-TR&api_key={tmdb_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "KuroWatch/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
            results = data.get("results", [])
            if not results:
                continue
            best = results[0]
            poster = best.get("poster_path")
            if not poster:
                continue
            tmdb_id = best.get("id")
            mtype = best.get("media_type", media_type)
            return {
                "cover_url": f"{TMDB_IMG}{poster}",
                "external_id": f"tmdb:{tmdb_id}",
                "tmdb_type": mtype,
            }
        except Exception:
            pass
        time.sleep(0.2)
    return None


def main():
    tmdb_key = get_tmdb_key()
    if not tmdb_key:
        print("HATA: TMDB API key bulunamadı!")
        print("config.json'a şunu ekle: \"tmdb_api_key\": \"YOUR_BEARER_TOKEN\"")
        print("Ücretsiz key: https://www.themoviedb.org/settings/api")
        sys.exit(1)

    # Tüm içerikleri çek
    all_items = api_get("/content")
    # Oyunları çıkar (Steam kullanıyor), AniList eşleşmiş olanları çıkar
    targets = [
        c for c in all_items
        if c.get("type") in ("anime", "manga", "manhwa")
        and (not c.get("cover_url") or FORCE)
        and not (str(c.get("external_id", "")).isdigit())  # Pure AniList ID var → atla
    ]

    print(f"TMDB ile zenginleştirilecek: {len(targets)} içerik\n")

    found = skipped = failed = 0

    for c in targets:
        cid = c["id"]
        title = c["title"]
        ctype = c["type"]

        print(f"  [{ctype}] {title}", end=" → ")

        # Anime için hem movie hem tv dene
        result = tmdb_search(title, tmdb_key, "multi")
        time.sleep(DELAY)

        if not result:
            print("bulunamadı")
            skipped += 1
            continue

        patch = {"cover_url": result["cover_url"]}
        if not c.get("external_id"):
            patch["external_id"] = result["external_id"]

        try:
            api_patch(f"/content/{cid}", patch)
            print(f"✅ (TMDB:{result['external_id']}, type:{result['tmdb_type']})")
            found += 1
        except Exception as e:
            print(f"❌ PATCH hatası: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"✅ Zenginleştirildi: {found}")
    print(f"⏭️  Bulunamadı: {skipped}")
    print(f"❌ Başarısız: {failed}")
    print(f"\nSonuç: {found} yeni kapak eklendi.")


if __name__ == "__main__":
    main()
