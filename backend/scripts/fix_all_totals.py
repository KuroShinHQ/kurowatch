#!/usr/bin/env python3
"""SOHBET-153 Madde 5: Tüm içeriklerin total_episodes/total_chapters'ını API'den çek."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
from datetime import datetime
from backend.database import AsyncSessionLocal
from backend.models import Content
from sqlalchemy import select

ANILIST_URL = "https://graphql.anilist.co"
MANGADEX_BASE = "https://api.mangadex.org"

# AniList queries
DETAIL_QUERY = """
query ($id: Int) {
  Media(id: $id) {
    id episodes chapters type countryOfOrigin
  }
}
"""
BY_MAL_QUERY = """
query ($idMal: Int, $type: MediaType) {
  Media(idMal: $idMal, type: $type) {
    id episodes chapters type countryOfOrigin
  }
}
"""

async def anilist_query(query: str, variables: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(ANILIST_URL, json={"query": query, "variables": variables})
            r.raise_for_status()
            return r.json()
    except Exception:
        return None

async def mangadex_latest_chapter(uuid: str) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{MANGADEX_BASE}/manga/{uuid}/feed",
                params={
                    "limit": 1,
                    "order[chapter]": "desc",
                    "contentRating[]": ["safe","suggestive","erotica","pornographic"],
                }
            )
            r.raise_for_status()
            data = r.json()
            items = data.get("data", [])
            if items:
                ch = items[0]["attributes"]["chapter"]
                return int(float(ch))
            return None
    except Exception:
        return None

async def process_content(c: Content, stats: dict) -> None:
    ext = c.external_id
    if not ext:
        stats["skipped_no_ext"] += 1
        return

    if c.type == "game":
        stats["skipped_game"] += 1
        return

    old_val = c.total_episodes if c.type in ("anime", "series", "movie", "cartoon") else c.total_chapters

    if ext.startswith("mdx:"):
        uuid = ext[4:]
        latest = await mangadex_latest_chapter(uuid)
        if latest and latest > (c.total_chapters or 0):
            c.total_chapters = latest
            c.updated_at = datetime.utcnow()
            stats["updated"] += 1
            print(f"  [MDX] {c.title}: total_chapters {old_val} -> {latest}")
        else:
            stats["no_change"] += 1

    elif ext.startswith("mal:"):
        mal_id = ext[4:]
        anilist_type = "ANIME" if c.type in ("anime", "series", "movie", "cartoon") else "MANGA"
        data = await anilist_query(BY_MAL_QUERY, {"idMal": int(mal_id), "type": anilist_type})
        if data and data.get("data", {}).get("Media"):
            m = data["data"]["Media"]
            if c.type in ("anime", "series", "movie", "cartoon"):
                api_val = m.get("episodes")
                if api_val and api_val > (c.total_episodes or 0):
                    c.total_episodes = api_val
                    c.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                    print(f"  [MAL->AL] {c.title}: total_episodes {old_val} -> {api_val}")
                else:
                    stats["no_change"] += 1
            else:
                api_val = m.get("chapters")
                if api_val and api_val > (c.total_chapters or 0):
                    c.total_chapters = api_val
                    c.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                    print(f"  [MAL->AL] {c.title}: total_chapters {old_val} -> {api_val}")
                else:
                    stats["no_change"] += 1
        else:
            stats["no_data"] += 1
            print(f"  [MAL->AL] {c.title}: API'den veri alinamadi")

    elif ":" not in ext:
        # Pure numeric = AniList ID
        data = await anilist_query(DETAIL_QUERY, {"id": int(ext)})
        if data and data.get("data", {}).get("Media"):
            m = data["data"]["Media"]
            if c.type in ("anime", "series", "movie", "cartoon"):
                api_val = m.get("episodes")
                if api_val and api_val > (c.total_episodes or 0):
                    c.total_episodes = api_val
                    c.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                    print(f"  [AL] {c.title}: total_episodes {old_val} -> {api_val}")
                else:
                    stats["no_change"] += 1
            else:
                api_val = m.get("chapters")
                if api_val and api_val > (c.total_chapters or 0):
                    c.total_chapters = api_val
                    c.updated_at = datetime.utcnow()
                    stats["updated"] += 1
                    print(f"  [AL] {c.title}: total_chapters {old_val} -> {api_val}")
                else:
                    stats["no_change"] += 1
        else:
            stats["no_data"] += 1
            print(f"  [AL] {c.title}: API'den veri alinamadi (ext={ext})")
    else:
        stats["skipped_other"] += 1

    await asyncio.sleep(0.3)  # rate limit

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Content).order_by(Content.id))
        all_items = r.scalars().all()
        print(f"Toplam {len(all_items)} icerik taranacak...")

        stats = {"updated": 0, "no_change": 0, "no_data": 0,
                 "skipped_no_ext": 0, "skipped_game": 0, "skipped_other": 0}

        for i, c in enumerate(all_items):
            if i % 20 == 0 and i > 0:
                print(f"--- {i}/{len(all_items)} islendi ---")
            await process_content(c, stats)

        await db.commit()

        print("\n=== ISTATISTIKLER ===")
        print(f"Guncellenen: {stats['updated']}")
        print(f"Degismeyen: {stats['no_change']}")
        print(f"Veri alinamayan: {stats['no_data']}")
        print(f"External ID'siz atlanan: {stats['skipped_no_ext']}")
        print(f"Oyun atlanan: {stats['skipped_game']}")
        print(f"Diger atlanan: {stats['skipped_other']}")
        print(f"Toplam: {sum(stats.values())}")

if __name__ == "__main__":
    asyncio.run(main())
