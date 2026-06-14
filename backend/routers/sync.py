import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Content, Site, Episode, Update, Tag, ContentTag

router = APIRouter()


async def _full_export(db: AsyncSession) -> dict:
    """Tüm tabloları JSON'a döküm"""
    r_c = await db.execute(select(Content).options(
        selectinload(Content.sites),
        selectinload(Content.episodes),
        selectinload(Content.updates),
        selectinload(Content.tags).selectinload(ContentTag.tag),
    ))
    contents = r_c.scalars().all()

    r_t = await db.execute(select(Tag))
    tags = r_t.scalars().all()

    def dt(d):
        return d.isoformat() if d else None

    return {
        "version": 1,
        "exported_at": datetime.utcnow().isoformat(),
        "contents": [
            {
                "id": c.id, "title": c.title, "type": c.type,
                "cover_url": c.cover_url, "external_id": c.external_id,
                "status": c.status, "total_episodes": c.total_episodes,
                "total_chapters": c.total_chapters, "my_progress": c.my_progress,
                "my_progress_pct": c.my_progress_pct, "my_score": c.my_score,
                "note_text": c.note_text, "note_is_spoiler": c.note_is_spoiler,
                "added_at": dt(c.added_at), "updated_at": dt(c.updated_at),
                "sites": [
                    {"site_name": s.site_name, "site_url": s.site_url,
                     "is_primary": s.is_primary, "latest_known_ep": s.latest_known_ep}
                    for s in c.sites
                ],
                "tag_ids": [ct.tag_id for ct in c.tags],
            }
            for c in contents
        ],
        "tags": [
            {"id": t.id, "name": t.name, "tag_type": t.tag_type, "color": t.color}
            for t in tags
        ],
    }


@router.get("/export")
async def export_data(db: AsyncSession = Depends(get_db)):
    data = await _full_export(db)
    return JSONResponse(content=data, headers={
        "Content-Disposition": 'attachment; filename="kurowatch_export.json"'
    })


class ImportBody(BaseModel):
    contents: List[dict]
    tags: Optional[List[dict]] = []


@router.post("/import")
async def import_data(body: ImportBody, db: AsyncSession = Depends(get_db)):
    """
    JSON'daki her içeriği mevcut DB ile karşılaştır.
    Aynı external_id varsa updated_at'e göre çakışma listele.
    """
    conflicts = []
    new_items = []

    for item in body.contents:
        ext_id = item.get("external_id")
        if ext_id:
            r = await db.execute(
                select(Content).where(Content.external_id == ext_id)
            )
            existing = r.scalar_one_or_none()
            if existing:
                import_at = datetime.fromisoformat(item.get("updated_at", "2000-01-01"))
                db_at = existing.updated_at or datetime.min
                if import_at > db_at:
                    conflicts.append({
                        "import": item,
                        "existing": {"id": existing.id, "title": existing.title,
                                     "updated_at": db_at.isoformat()},
                    })
                continue
        new_items.append(item)

    return {"conflicts": conflicts, "new_count": len(new_items), "new_items": new_items}


class ResolveBody(BaseModel):
    decisions: List[dict]  # [{external_id, choice: "mine"|"import", data: {...}}]
    new_items: Optional[List[dict]] = []


@router.post("/import/resolve")
async def resolve_import(body: ResolveBody, db: AsyncSession = Depends(get_db)):
    """Çakışma kararlarını + yeni öğeleri DB'ye uygula"""
    added = 0

    async def _upsert(item: dict):
        nonlocal added
        ext_id = item.get("external_id")
        if ext_id:
            r = await db.execute(select(Content).where(Content.external_id == ext_id))
            existing = r.scalar_one_or_none()
            if existing:
                for k, v in item.items():
                    if k in ("id", "sites", "tag_ids", "added_at"):
                        continue
                    if k == "updated_at":
                        setattr(existing, k, datetime.fromisoformat(v) if v else None)
                    elif hasattr(existing, k):
                        setattr(existing, k, v)
                return
        # Yeni kayıt
        c = Content(
            title=item.get("title", ""),
            type=item.get("type", "anime"),
            cover_url=item.get("cover_url"),
            external_id=item.get("external_id"),
            status=item.get("status", "planning"),
            total_episodes=item.get("total_episodes"),
            total_chapters=item.get("total_chapters"),
            my_progress=item.get("my_progress", 0),
            my_progress_pct=item.get("my_progress_pct"),
            my_score=item.get("my_score"),
            note_text=item.get("note_text"),
            note_is_spoiler=item.get("note_is_spoiler", False),
            added_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(c)
        added += 1

    for dec in body.decisions:
        if dec.get("choice") == "import":
            await _upsert(dec["data"])

    for item in (body.new_items or []):
        await _upsert(item)

    await db.commit()
    return {"ok": True, "added": added}
