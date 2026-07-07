import asyncio
import sqlite3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx

DB = os.environ.get("KUROWATCH_DB_PATH", str(ROOT / "memory" / "kurowatch.db"))

ANILIST_QUERY = """
query($search: String, $type: MediaType) {
  Page(perPage: 1) {
    media(search: $search, type: $type, sort: SEARCH_MATCH) {
      id
      coverImage { large extraLarge }
    }
  }
}
"""


async def anilist_cover(client, title, media_type):
    variables = {"search": title, "type": media_type}
    try:
        r = await client.post(
            "https://graphql.anilist.co",
            json={"query": ANILIST_QUERY, "variables": variables},
            timeout=15,
        )
        data = r.json()
        media = data.get("data", {}).get("Page", {}).get("media", [])
        if media:
            cover = media[0].get("coverImage", {})
            return cover.get("extraLarge") or cover.get("large"), media[0].get("id")
    except Exception as e:
        print(f"  AniList error for '{title}': {e}")
    return None, None


async def steam_cover(client, title):
    try:
        r = await client.get(
            "https://store.steampowered.com/api/storesearch",
            params={"term": title, "l": "en", "cc": "us"},
            timeout=15,
        )
        items = r.json().get("items", [])
        if items:
            appid = items[0].get("id")
            cover = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
            r2 = await client.head(cover, follow_redirects=True, timeout=10)
            if r2.status_code == 200:
                return cover, appid
            cover2 = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/library_600x900.jpg"
            r3 = await client.head(cover2, follow_redirects=True, timeout=10)
            if r3.status_code == 200:
                return cover2, appid
            return None, appid
    except Exception as e:
        print(f"  Steam error for '{title}': {e}")
    return None, None


async def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    targets = [
        (679, "5 Centimeters per Second", "anime", "ANIME"),
        (680, "The Greatest Estate Developer", "manhwa", "MANGA"),
        (681, "The Archmage Returns After 4000 Years", "manhwa", "MANGA"),
        (92, "Kahramanin Donusu", "manga", "MANGA"),
        (125, "Assassin's Creed Shadows", "game", None),
    ]

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36"}
    ) as client:
        for cid, title, ctype, anilist_type in targets:
            print(f"\n--- #{cid} {title} ({ctype}) ---")
            cover_url = None
            external_id = None

            if anilist_type:
                cover_url, external_id = await anilist_cover(client, title, anilist_type)
                if cover_url:
                    print(f"  AniList: cover={cover_url[:60]}... id={external_id}")

            if not cover_url and ctype == "game":
                cover_url, external_id = await steam_cover(client, title)
                if cover_url:
                    print(f"  Steam: cover={cover_url[:60]}... appid={external_id}")

            if not cover_url:
                orig_title = con.execute(
                    "SELECT title FROM content WHERE id=?", (cid,)
                ).fetchone()[0]
                if orig_title != title:
                    print(f"  Retrying with DB title: {orig_title}")
                    if anilist_type:
                        cover_url, external_id = await anilist_cover(client, orig_title, anilist_type)
                        if cover_url:
                            print(f"  AniList: cover={cover_url[:60]}... id={external_id}")

            if cover_url:
                con.execute(
                    "UPDATE content SET cover_url=?, external_id=COALESCE(external_id,CAST(? AS TEXT)) WHERE id=?",
                    (cover_url, external_id, cid),
                )
                con.commit()
                print(f"  DB UPDATE: #{cid} cover_url set")
            else:
                print(f"  SKIP: no cover found")

    remaining = con.execute(
        "SELECT id, title, type FROM content WHERE cover_url IS NULL OR cover_url = '' ORDER BY id"
    ).fetchall()
    print(f"\n=== Remaining without cover: {len(remaining)} ===")
    for r in remaining:
        print(f"  #{r['id']} {r['title']} ({r['type']})")
    con.close()


if __name__ == "__main__":
    asyncio.run(main())
