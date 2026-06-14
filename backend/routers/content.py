from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Content, ContentTag, Tag
from backend.scraper import anilist

router = APIRouter()


# ── Pydantic Şemaları ────────────────────────────────────────────────

class ContentCreate(BaseModel):
    title: str
    type: str
    status: str = "planning"
    cover_url: Optional[str] = None
    external_id: Optional[str] = None
    total_episodes: Optional[int] = None
    total_chapters: Optional[int] = None
    my_progress: int = 0
    my_progress_pct: Optional[int] = None
    my_score: Optional[float] = None
    note_text: Optional[str] = None
    note_is_spoiler: bool = False


class ContentPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    cover_url: Optional[str] = None
    external_id: Optional[str] = None
    my_progress: Optional[int] = None
    my_progress_pct: Optional[int] = None
    my_score: Optional[float] = None
    note_text: Optional[str] = None
    note_is_spoiler: Optional[bool] = None
    total_episodes: Optional[int] = None
    total_chapters: Optional[int] = None


def _serialize(c: Content) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "type": c.type,
        "cover_url": c.cover_url,
        "external_id": c.external_id,
        "status": c.status,
        "total_episodes": c.total_episodes,
        "total_chapters": c.total_chapters,
        "my_progress": c.my_progress,
        "my_progress_pct": c.my_progress_pct,
        "my_score": c.my_score,
        "note_text": c.note_text,
        "note_is_spoiler": c.note_is_spoiler,
        "added_at": c.added_at.isoformat() if c.added_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "sites": [
            {"id": s.id, "site_name": s.site_name, "site_url": s.site_url,
             "is_primary": s.is_primary, "latest_known_ep": s.latest_known_ep}
            for s in (c.sites or [])
        ],
        "tags": [
            {"id": ct.tag.id, "name": ct.tag.name, "tag_type": ct.tag.tag_type, "color": ct.tag.color}
            for ct in (c.tags or []) if ct.tag
        ],
    }


# ── Endpoints ────────────────────────────────────────────────────────

@router.get("/content")
async def list_content(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Content).options(
        selectinload(Content.sites),
        selectinload(Content.tags).selectinload(ContentTag.tag),
    ).order_by(Content.updated_at.desc())

    if type:
        stmt = stmt.where(Content.type == type)
    if status:
        stmt = stmt.where(Content.status == status)
    if q:
        stmt = stmt.where(Content.title.ilike(f"%{q}%"))

    result = await db.execute(stmt)
    items = result.scalars().all()
    return [_serialize(c) for c in items]


@router.post("/content", status_code=201)
async def create_content(body: ContentCreate, db: AsyncSession = Depends(get_db)):
    if body.type not in ("anime", "manga", "manhwa", "game"):
        raise HTTPException(400, "Geçersiz içerik tipi")

    c = Content(**body.model_dump())
    c.added_at = datetime.utcnow()
    c.updated_at = datetime.utcnow()
    db.add(c)
    await db.commit()
    await db.refresh(c)
    new_id = c.id
    # İlişkileri yüklemek için yeniden sorgula
    return await get_content(new_id, db)


@router.get("/content/{content_id}")
async def get_content(content_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Content).where(Content.id == content_id).options(
        selectinload(Content.sites),
        selectinload(Content.episodes),
        selectinload(Content.tags).selectinload(ContentTag.tag),
    )
    result = await db.execute(stmt)
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    d = _serialize(c)
    d["episodes"] = [
        {"id": e.id, "number": e.number, "title": e.title,
         "url": e.url, "is_watched": e.is_watched,
         "watched_at": e.watched_at.isoformat() if e.watched_at else None,
         "is_new": e.is_new}
        for e in sorted(c.episodes, key=lambda e: e.number)
    ]
    return d


@router.patch("/content/{content_id}")
async def patch_content(content_id: int, body: ContentPatch, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(c, field, val)
    c.updated_at = datetime.utcnow()
    await db.commit()
    return await get_content(content_id, db)


class ProgressUpdate(BaseModel):
    progress: int


@router.post("/content/{content_id}/progress", status_code=200)
async def update_progress(content_id: int, body: ProgressUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id).options(selectinload(Content.sites), selectinload(Content.tags)))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    c.my_progress = body.progress
    c.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(c)
    return _serialize(c)


@router.delete("/content/{content_id}", status_code=204)
async def delete_content(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    await db.delete(c)
    await db.commit()


# ── Discover (AniList proxy) ─────────────────────────────────────────

@router.get("/discover")
async def discover(
    q: str = Query(..., min_length=1),
    type: str = Query("anime"),
    page: int = Query(1, ge=1),
):
    if type not in ("anime", "manga", "manhwa"):
        raise HTTPException(400, "Geçersiz tip (anime/manga/manhwa)")
    results = await anilist.search(q, type, page)
    return results
