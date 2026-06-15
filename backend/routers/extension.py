"""
FAZ-6 Browser Extension endpoint'leri.
GET  /api/extension/status   → ping (popup için)
GET  /api/extension/sites    → desteklenen site listesi
POST /api/extension/capture  → URL+title+episode → AniList ara → DB ekle/güncelle
"""
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Content
from backend.scraper import anilist

router = APIRouter()

SUPPORTED_SITES = [
    {"id": "crunchyroll", "name": "Crunchyroll", "url": "crunchyroll.com",  "type": "anime"},
    {"id": "diziwatch",   "name": "Diziwatch",   "url": "diziwatch.com",   "type": "anime"},
    {"id": "mangadex",    "name": "MangaDex",    "url": "mangadex.org",    "type": "manga"},
]


class CaptureRequest(BaseModel):
    url: str
    title: str
    episode: Optional[int] = None
    chapter: Optional[int] = None
    site: str
    type: str = "anime"


@router.get("/extension/status")
async def extension_status():
    return {"ok": True, "version": "0.1.0", "service": "kurowatch"}


@router.get("/extension/sites")
async def extension_sites():
    return {"sites": SUPPORTED_SITES}


@router.post("/extension/capture")
async def extension_capture(req: CaptureRequest, db: AsyncSession = Depends(get_db)):
    existing = await _find_existing(db, req.title, req.type)

    if existing:
        progress = req.episode or req.chapter or existing.my_progress
        if progress > existing.my_progress:
            existing.my_progress = progress
            if existing.status == "planning":
                existing.status = "watching"
            await db.commit()
        return {
            "action": "updated",
            "content_id": existing.id,
            "title": existing.title,
            "progress": existing.my_progress,
        }

    matched = await _search_anilist(req.title, req.type)

    content = Content(
        title=matched["title"] if matched else req.title,
        type=_map_type(req.type),
        status="watching",
        cover_url=matched.get("cover_url") if matched else None,
        external_id=matched.get("external_id") if matched else None,
        total_episodes=matched.get("total_episodes") if matched else None,
        total_chapters=matched.get("total_chapters") if matched else None,
        my_progress=req.episode or req.chapter or 0,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)

    return {
        "action": "created",
        "content_id": content.id,
        "title": content.title,
        "progress": content.my_progress,
        "anilist_matched": matched is not None,
    }


async def _find_existing(db: AsyncSession, title: str, content_type: str) -> Optional[Content]:
    result = await db.execute(select(Content).where(Content.type == _map_type(content_type)))
    rows = result.scalars().all()
    tl = title.lower()
    for c in rows:
        cl = c.title.lower()
        if cl in tl or tl in cl:
            return c
    return None


async def _search_anilist(title: str, content_type: str) -> Optional[dict]:
    try:
        results = await anilist.search(title, content_type=content_type)
        return results[0] if results else None
    except Exception:
        return None


def _map_type(t: str) -> str:
    return {"anime": "anime", "manga": "manga", "manhwa": "manhwa"}.get(t, "anime")
