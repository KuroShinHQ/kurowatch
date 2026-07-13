import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx
from backend.database import AsyncSessionLocal
from backend.models import Content
from sqlalchemy import select

MARTIAL_PEAK_ID = 1
MANGADEX_UUID = "b1461071-bfbb-43e7-a5b6-a7ba5904649f"

async def get_mangadex_latest_chapter(uuid: str) -> int | None:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"https://api.mangadex.org/manga/{uuid}/feed",
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
    except Exception as exc:
        print(f"MangaDex API hatasi: {exc}")
        return None

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Content).where(Content.id == MARTIAL_PEAK_ID))
        mp = r.scalar_one_or_none()
        if not mp:
            print("HATA: Martial Peak bulunamadi (id=1)")
            return

        print(f"Guncel: total_chapters={mp.total_chapters}, external_id={mp.external_id}")

        latest = await get_mangadex_latest_chapter(MANGADEX_UUID)
        if latest is None:
            print("HATA: MangaDex'ten chapter sayisi alinamadi")
            return

        print(f"MangaDex en son chapter: {latest}")
        mp.total_chapters = latest
        mp.updated_at = __import__('datetime').datetime.utcnow()
        await db.commit()
        print(f"OK: Martial Peak total_chapters = {latest} olarak guncellendi")

        r2 = await db.execute(select(Content).where(Content.id == MARTIAL_PEAK_ID))
        mp2 = r2.scalar_one()
        print(f"Dogruma: total_chapters = {mp2.total_chapters}")

if __name__ == "__main__":
    asyncio.run(main())
