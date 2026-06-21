"""
fetch_romaji_cache.py — 329 animenin AniList romaji bilgisini cache'e yazar.
Rate limit: 1 istek / 0.8sn → ~4dk tüm liste için.
Çıktı: scripts/ta_romaji_cache.json
"""
import asyncio
import json
import sqlite3
import time
from pathlib import Path

import httpx

ANILIST_URL = "https://graphql.anilist.co"
CACHE_PATH = Path("/mnt/c/Kuroshin/kurowatch/scripts/ta_romaji_cache.json")

_QUERY = """
query ($id: Int, $malId: Int) {
  Media(id: $id, idMal: $malId) {
    title { romaji english }
    synonyms
  }
}
"""


def get_targets():
    conn = sqlite3.connect("/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db")
    rows = conn.execute("""
        SELECT c.id, c.title, c.external_id
        FROM content c
        WHERE c.type = 'anime'
        AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%tranimeizle%')
        AND NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%turkanime%')
        ORDER BY c.id
    """).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "ext_id": r[2] or ""} for r in rows]


async def fetch_one(client: httpx.AsyncClient, item: dict) -> dict:
    ext_id = item["ext_id"]
    if not ext_id or ext_id.startswith("tmdb:"):
        return {"id": item["id"], "romaji": None, "english": None, "synonyms": []}

    variables = {}
    if ext_id.startswith("mal:"):
        try:
            variables["malId"] = int(ext_id[4:])
        except ValueError:
            return {"id": item["id"], "romaji": None, "english": None, "synonyms": []}
    else:
        try:
            variables["id"] = int(ext_id)
        except ValueError:
            return {"id": item["id"], "romaji": None, "english": None, "synonyms": []}

    for attempt in range(3):
        try:
            r = await client.post(ANILIST_URL, json={"query": _QUERY, "variables": variables}, timeout=10.0)
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", 60))
                print(f"  Rate limit — {wait}sn bekleniyor...")
                await asyncio.sleep(wait + 2)
                continue
            if r.status_code != 200:
                break
            data = r.json()
            if data.get("errors"):
                break
            media = data["data"]["Media"]
            titles = media["title"]
            syns = [s for s in (media.get("synonyms") or []) if s and any(c.isascii() and c.isalpha() for c in s)]
            return {
                "id": item["id"],
                "romaji": titles.get("romaji"),
                "english": titles.get("english"),
                "synonyms": syns[:5],
            }
        except Exception as e:
            if attempt == 2:
                print(f"  HATA [{item['id']}] {item['title'][:30]}: {e}")
    return {"id": item["id"], "romaji": None, "english": None, "synonyms": []}


async def main():
    targets = get_targets()
    print(f"Toplam: {len(targets)} anime")

    # Mevcut cache'i yükle (kısmi devam destekli)
    cache = {}
    if CACHE_PATH.exists():
        with open(CACHE_PATH) as f:
            existing = json.load(f)
        cache = {str(e["id"]): e for e in existing}
        print(f"Mevcut cache: {len(cache)} kayıt")

    remaining = [t for t in targets if str(t["id"]) not in cache]
    print(f"Çekilecek: {len(remaining)} | Atlanan (cache): {len(cache)}")

    async with httpx.AsyncClient() as client:
        for i, item in enumerate(remaining):
            result = await fetch_one(client, item)
            cache[str(item["id"])] = result
            romaji = result.get("romaji") or "-"
            print(f"  [{i+1}/{len(remaining)}] [{item['id']}] {item['title'][:35]:35} → {romaji}")
            await asyncio.sleep(0.8)  # ~75 req/dk, AniList limiti 90

            # Her 50'de bir kaydet
            if (i + 1) % 50 == 0:
                with open(CACHE_PATH, "w") as f:
                    json.dump(list(cache.values()), f, ensure_ascii=False, indent=2)
                print(f"  [KAYIT] {len(cache)} kayıt yazıldı")

    with open(CACHE_PATH, "w") as f:
        json.dump(list(cache.values()), f, ensure_ascii=False, indent=2)

    found = sum(1 for v in cache.values() if v.get("romaji"))
    print(f"\nTamamlandı: {found}/{len(targets)} romaji bulundu → {CACHE_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
