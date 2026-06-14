import asyncio
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Content, Episode, Update
from backend.scraper import anilist

router = APIRouter()


# ── Bölüm listesi ────────────────────────────────────────────────────

@router.get("/content/{content_id}/episodes")
async def list_episodes(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Episode)
        .where(Episode.content_id == content_id)
        .order_by(Episode.number)
    )
    eps = result.scalars().all()
    return [
        {"id": e.id, "number": e.number, "title": e.title, "url": e.url,
         "is_watched": e.is_watched,
         "watched_at": e.watched_at.isoformat() if e.watched_at else None,
         "is_new": e.is_new}
        for e in eps
    ]


@router.post("/content/{content_id}/episodes/sync")
async def sync_episodes_from_anilist(content_id: int, db: AsyncSession = Depends(get_db)):
    """AniList'ten bölüm listesini çek, yeni olanları DB'ye kaydet."""
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")

    if not c.external_id or c.type == "game":
        raise HTTPException(400, "Bu içerik tipi için AniList sync desteklenmiyor")

    # Mevcut bölüm numaraları
    existing_q = await db.execute(select(Episode.number).where(Episode.content_id == content_id))
    existing_numbers = set(existing_q.scalars().all())

    detail = await anilist.get_detail(c.external_id)
    if not detail:
        raise HTTPException(502, "AniList'ten veri alınamadı")

    new_episodes: list[Episode] = []

    if c.type == "anime":
        streaming = detail.get("streaming_episodes", [])
        if streaming:
            for se in streaming:
                # "Episode 3 - Title" → 3
                m = re.search(r'Episode\s+(\d+)', se.get("title", ""), re.IGNORECASE)
                num = int(m.group(1)) if m else None
                if num is None:
                    continue
                if num not in existing_numbers:
                    new_episodes.append(Episode(
                        content_id=content_id, number=num,
                        title=se.get("title") or None,
                        url=se.get("url") or None,
                        is_watched=False, is_new=False,
                    ))
                    existing_numbers.add(num)
        else:
            # Streaming yok, sayısal oluştur
            total = detail.get("total_episodes") or (c.total_episodes or 0)
            for i in range(1, total + 1):
                if i not in existing_numbers:
                    new_episodes.append(Episode(
                        content_id=content_id, number=i,
                        is_watched=False, is_new=False,
                    ))
    else:
        # manga / manhwa: chapter numaraları oluştur (max 500)
        total = min(detail.get("total_chapters") or (c.total_chapters or 0), 500)
        for i in range(1, total + 1):
            if i not in existing_numbers:
                new_episodes.append(Episode(
                    content_id=content_id, number=i,
                    is_watched=False, is_new=False,
                ))

    if new_episodes:
        db.add_all(new_episodes)
        await db.commit()

    eps_q = await db.execute(
        select(Episode).where(Episode.content_id == content_id).order_by(Episode.number)
    )
    eps = eps_q.scalars().all()
    return {
        "synced": len(new_episodes),
        "episodes": [
            {"id": e.id, "number": e.number, "title": e.title, "url": e.url,
             "is_watched": e.is_watched, "is_new": e.is_new,
             "watched_at": e.watched_at.isoformat() if e.watched_at else None}
            for e in eps
        ],
    }


@router.patch("/episodes/{episode_id}/watch")
async def mark_watched(episode_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Episode).where(Episode.id == episode_id))
    ep = result.scalar_one_or_none()
    if not ep:
        raise HTTPException(404, "Bulunamadı")
    ep.is_watched = True
    ep.is_new = False
    ep.watched_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}


# ── Güncellemeler ────────────────────────────────────────────────────

@router.get("/updates")
async def list_updates(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Update)
        .options(selectinload(Update.content))
        .order_by(Update.detected_at.desc())
    )
    if unread_only:
        stmt = stmt.where(Update.is_read == False)
    result = await db.execute(stmt)
    updates = result.scalars().all()
    return [
        {
            "id": u.id,
            "content_id": u.content_id,
            "content_title": u.content.title if u.content else "Bilinmiyor",
            "episode_number": u.episode_number,
            "site_name": u.site_name,
            "detected_at": u.detected_at.isoformat(),
            "is_read": u.is_read,
        }
        for u in updates
    ]


@router.patch("/updates/{update_id}/read")
async def mark_update_read(update_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Update).where(Update.id == update_id))
    u = result.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Bulunamadı")
    u.is_read = True
    await db.commit()
    return {"ok": True}


# ── Güncelleme Kontrolü ───────────────────────────────────────────────

async def _check_one(content: Content, db: AsyncSession) -> int:
    """Tek içerik için güncelleme kontrolü. Yeni bölüm sayısını döndürür."""
    if not content.external_id or content.type == "game":
        return 0

    detail = await anilist.get_detail(content.external_id)
    if not detail:
        return 0

    # Anime: episodes, Manga/Manhwa: chapters
    if content.type == "anime":
        api_count = detail.get("total_episodes") or 0
        db_count = content.total_episodes or 0
    else:
        api_count = detail.get("total_chapters") or 0
        db_count = content.total_chapters or 0

    if api_count <= db_count or api_count == 0:
        return 0

    new_count = api_count - db_count
    # Update kaydı oluştur
    u = Update(
        content_id=content.id,
        episode_number=api_count,
        site_name="AniList",
        detected_at=datetime.utcnow(),
        is_read=False,
    )
    db.add(u)

    # Content'i güncelle
    if content.type == "anime":
        content.total_episodes = api_count
    else:
        content.total_chapters = api_count
    content.updated_at = datetime.utcnow()

    return new_count


@router.post("/check-updates")
async def check_updates(db: AsyncSession = Depends(get_db)):
    """Tüm içerikler için AniList'e sorgu at, yeni bölüm varsa Update kaydı oluştur."""
    result = await db.execute(select(Content))
    items = result.scalars().all()

    found = 0
    # AniList rate limit: 90 req/dk → her istek arasına 0.7s
    for c in items:
        new = await _check_one(c, db)
        found += new
        if new:
            await asyncio.sleep(0.7)

    await db.commit()
    return {"checked": len(items), "new_updates": found}
