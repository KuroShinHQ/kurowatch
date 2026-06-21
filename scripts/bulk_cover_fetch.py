"""
Bulk cover fetcher: AniList → Jikan (MAL) zinciri
Cover-siz tüm içerikler için cover URL çeker ve SQLite'a direkt yazar.
Backend çalışıyor olsa da olmasa da çalışır.
"""
import asyncio
import re
import sqlite3
from pathlib import Path

import aiohttp

DB_PATH = Path(__file__).parent.parent / "memory" / "kurowatch.db"
ANILIST_URL = "https://graphql.anilist.co"
JIKAN_URL   = "https://api.jikan.moe/v4"

ANILIST_QUERY = """
query($s: String!, $type: MediaType) {
  Media(search: $s, type: $type) {
    coverImage { extraLarge large }
  }
}
"""

def title_variants(title: str) -> list:
    seen = []
    def add(v):
        v = v.strip()
        if v and v not in seen and len(v) > 2:
            seen.append(v)

    add(title)
    # Parantez içini çıkar: "Attack on Titan (Shingeki)" → "Attack on Titan"
    no_paren = re.sub(r'\s*\([^)]*\)', '', title).strip()
    add(no_paren)
    # Parantez içini al: "Attack on Titan (Shingeki)" → "Shingeki"
    for p in re.findall(r'\(([^)]+)\)', title):
        add(p)
    # İki nokta öncesi: "Zom 100: Zombie ni..." → "Zom 100"
    if ':' in title:
        add(title.split(':')[0])
    # Sezon tag temizle: "Shangri-La Frontier (S2)" → "Shangri-La Frontier"
    add(re.sub(r'\s*\([Ss]\d+\)\s*', '', title))
    # Serisi kelimesini kaldır
    add(re.sub(r'\s*(Serisi|Serileri)\s*', '', title, flags=re.IGNORECASE))
    return seen


async def anilist_cover(session: aiohttp.ClientSession, title: str, ctype: str):
    media_type = "MANGA" if ctype == "manga" else "ANIME"
    for variant in title_variants(title):
        try:
            async with session.post(
                ANILIST_URL,
                json={"query": ANILIST_QUERY, "variables": {"s": variant, "type": media_type}},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                if r.status != 200:
                    continue
                data = await r.json()
                media = (data.get("data") or {}).get("Media")
                if media:
                    img = media.get("coverImage", {})
                    url = img.get("extraLarge") or img.get("large")
                    if url:
                        return url
        except Exception:
            pass
        await asyncio.sleep(0.4)
    return None


async def jikan_cover(session: aiohttp.ClientSession, title: str, ctype: str):
    endpoint = "manga" if ctype == "manga" else "anime"
    for variant in title_variants(title):
        try:
            async with session.get(
                f"{JIKAN_URL}/{endpoint}",
                params={"q": variant, "limit": 1},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                if r.status == 429:
                    await asyncio.sleep(3)
                    continue
                if r.status != 200:
                    continue
                data = await r.json()
                items = data.get("data", [])
                if items:
                    imgs = items[0].get("images", {}).get("jpg", {})
                    url = imgs.get("large_image_url") or imgs.get("image_url")
                    if url:
                        return url
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return None


def db_get_no_cover():
    con = sqlite3.connect(str(DB_PATH))
    rows = con.execute(
        "SELECT id, title, type FROM content WHERE cover_url IS NULL OR cover_url = ''"
    ).fetchall()
    con.close()
    return rows


def db_set_cover(content_id: int, url: str):
    con = sqlite3.connect(str(DB_PATH))
    con.execute(
        "UPDATE content SET cover_url = ? WHERE id = ?", (url, content_id)
    )
    con.commit()
    con.close()


async def main():
    rows = db_get_no_cover()
    total = len(rows)
    print(f"Cover-siz: {total} içerik\n")

    found = 0
    not_found = []

    async with aiohttp.ClientSession() as session:
        for i, (cid, title, ctype) in enumerate(rows, 1):
            label = title[:52] + "..." if len(title) > 52 else title
            print(f"[{i:02d}/{total}] {label:55s} ", end="", flush=True)

            # 1. AniList
            url = await anilist_cover(session, title, ctype)
            source = "AniList"

            # 2. Jikan/MAL fallback
            if not url:
                url = await jikan_cover(session, title, ctype)
                source = "Jikan "

            if url:
                db_set_cover(cid, url)
                found += 1
                print(f"✅ {source}")
            else:
                not_found.append(title)
                print("⚠️  bulunamadı")

            await asyncio.sleep(0.2)

    print(f"\n{'─'*60}")
    print(f"✅ Güncellenen : {found}/{total}")
    print(f"⚠️  Bulunamayan : {len(not_found)}")
    if not_found:
        print("\nManuel cover gereken içerikler:")
        for t in not_found:
            print(f"  • {t}")


if __name__ == "__main__":
    asyncio.run(main())
