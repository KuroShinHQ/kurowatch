from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Tag, ContentTag, Content

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    tag_type: str = "user"
    color: Optional[str] = None


@router.get("/tags")
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).order_by(Tag.name))
    return [
        {"id": t.id, "name": t.name, "tag_type": t.tag_type, "color": t.color}
        for t in result.scalars().all()
    ]


@router.post("/tags", status_code=201)
async def create_tag(body: TagCreate, db: AsyncSession = Depends(get_db)):
    if body.tag_type not in ("api", "user"):
        raise HTTPException(400, "tag_type: api veya user olmalı")
    tag = Tag(**body.model_dump())
    db.add(tag)
    try:
        await db.commit()
        await db.refresh(tag)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, f"'{body.name}' etiketi zaten var")
    return {"id": tag.id, "name": tag.name, "tag_type": tag.tag_type, "color": tag.color}


@router.post("/content/{content_id}/tags/{tag_id}", status_code=201)
async def attach_tag(content_id: int, tag_id: int, db: AsyncSession = Depends(get_db)):
    r_c = await db.execute(select(Content).where(Content.id == content_id))
    if not r_c.scalar_one_or_none():
        raise HTTPException(404, "İçerik bulunamadı")
    r_t = await db.execute(select(Tag).where(Tag.id == tag_id))
    if not r_t.scalar_one_or_none():
        raise HTTPException(404, "Etiket bulunamadı")

    ct = ContentTag(content_id=content_id, tag_id=tag_id)
    db.add(ct)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()  # zaten ekli
    return {"ok": True}


@router.delete("/content/{content_id}/tags/{tag_id}", status_code=204)
async def detach_tag(content_id: int, tag_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(ContentTag).where(
            ContentTag.content_id == content_id,
            ContentTag.tag_id == tag_id
        )
    )
    ct = r.scalar_one_or_none()
    if not ct:
        raise HTTPException(404, "Etiket bu içeriğe ekli değil")
    await db.delete(ct)
    await db.commit()
