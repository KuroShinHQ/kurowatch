"""
external_id'si olan tüm içerikler için AniList averageScore çeker.
Yoksa Jikan (MAL) score dener.
Direkt SQLite'a yazar.
"""
import asyncio
import sqlite3
import aiohttp

DB_PATH = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"
ANILIST_URL = "https://graphql.anilist.co"
JIKAN_URL   = "https://api.jikan.moe/v4"

ANILIST_QUERY = """
query($id: Int!) {
  Media(idMal: $id) { averageScore }
}
"""

def get_items():
    con = sqlite3.connect(DB_PATH)
    rows = con.execute(
        "SELECT id, title, type, external_id FROM content "
        "WHERE external_id IS NOT NULL AND external_id != '' "
        "AND (external_score IS NULL OR external_score = 0)"
    ).fetchall()
    con.close()
    return rows

def set_score(cid, score):
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE content SET external_score=? WHERE id=?", (score, cid))
    con.commit()
    con.close()

async def anilist_score(session, mal_id):
    try:
        async with session.post(
            ANILIST_URL,
            json={"query": ANILIST_QUERY, "variables": {"id": int(mal_id)}},
            timeout=aiohttp.ClientTimeout(total=6),
        ) as r:
            if r.status != 200: return None
            d = await r.json()
            media = (d.get("data") or {}).get("Media")
            if media and media.get("averageScore"):
                return round(media["averageScore"] / 10, 1)
    except Exception:
        pass
    return None

async def jikan_score(session, title, ctype):
    ep = "manga" if ctype == "manga" else "anime"
    try:
        async with session.get(
            f"{JIKAN_URL}/{ep}",
            params={"q": title, "limit": 1},
            timeout=aiohttp.ClientTimeout(total=6),
        ) as r:
            if r.status != 200: return None
            d = await r.json()
            items = d.get("data", [])
            if items and items[0].get("score"):
                return round(float(items[0]["score"]), 1)
    except Exception:
        pass
    return None

async def main():
    rows = get_items()
    total = len(rows)
    print(f"external_score eksik: {total} içerik\n")

    found = 0
    async with aiohttp.ClientSession() as session:
        for i, (cid, title, ctype, ext_id) in enumerate(rows, 1):
            label = title[:50] + "..." if len(title) > 50 else title
            print(f"[{i:03d}/{total}] {label:53s} ", end="", flush=True)

            score = await anilist_score(session, ext_id)
            src = "AniList"
            if not score:
                score = await jikan_score(session, title, ctype)
                src = "Jikan "

            if score:
                set_score(cid, score)
                found += 1
                print(f"✅ {score:4.1f} ({src})")
            else:
                print("⚠️  yok")
            await asyncio.sleep(0.5)

    print(f"\n✅ {found}/{total} external_score yazıldı")

if __name__ == "__main__":
    asyncio.run(main())
