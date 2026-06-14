from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Content, Site

router = APIRouter()


class SiteCreate(BaseModel):
    site_name: str
    site_url: str
    is_primary: bool = False


@router.post("/content/{content_id}/sites", status_code=201)
async def add_site(content_id: int, body: SiteCreate, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Content).where(Content.id == content_id))
    if not r.scalar_one_or_none():
        raise HTTPException(404, "İçerik bulunamadı")

    # Yeni birincil site ekleniyorsa eskisinin birincilliğini kaldır
    if body.is_primary:
        r2 = await db.execute(
            select(Site).where(Site.content_id == content_id, Site.is_primary == True)
        )
        for s in r2.scalars().all():
            s.is_primary = False

    site = Site(content_id=content_id, **body.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return {"id": site.id, "site_name": site.site_name, "site_url": site.site_url,
            "is_primary": site.is_primary, "latest_known_ep": site.latest_known_ep}


@router.delete("/sites/{site_id}", status_code=204)
async def delete_site(site_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Site).where(Site.id == site_id))
    site = r.scalar_one_or_none()
    if not site:
        raise HTTPException(404, "Site bulunamadı")
    await db.delete(site)
    await db.commit()
