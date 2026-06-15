import asyncio
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_config
from backend.database import get_db
from backend.models import Content, Episode, Update
from backend.scraper import anilist
from backend.scraper import mangadex

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
async def sync_episodes(content_id: int, db: AsyncSession = Depends(get_db)):
    """Harici kaynaktan bölüm listesini çek, yeni olanları DB'ye kaydet."""
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")

    if not c.external_id or c.type == "game":
        raise HTTPException(400, "Bu içerik tipi için bölüm sync desteklenmiyor")

    existing_q = await db.execute(select(Episode.number).where(Episode.content_id == content_id))
    existing_numbers = set(existing_q.scalars().all())

    ext = c.external_id
    new_episodes: list[Episode] = []

    if ext.startswith("mdx:"):
        # MangaDex sync
        detail = await mangadex.get_detail(ext[4:])
        if not detail:
            raise HTTPException(502, "MangaDex'ten veri alınamadı")
        total = min(detail.get("total_chapters") or (c.total_chapters or 0), 500)
        for i in range(1, total + 1):
            if i not in existing_numbers:
                new_episodes.append(Episode(content_id=content_id, number=i, is_watched=False, is_new=False))

    elif ext.startswith("mal:"):
        raise HTTPException(400, "MAL kaynakları için bölüm sync desteklenmiyor")

    elif c.type == "anime":
        # AniList anime sync (streaming episodes veya sayısal)
        detail = await anilist.get_detail(ext)
        if not detail:
            raise HTTPException(502, "AniList'ten veri alınamadı")
        streaming = detail.get("streaming_episodes", [])
        if streaming:
            for se in streaming:
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
            total = detail.get("total_episodes") or (c.total_episodes or 0)
            for i in range(1, total + 1):
                if i not in existing_numbers:
                    new_episodes.append(Episode(content_id=content_id, number=i, is_watched=False, is_new=False))

    else:
        # AniList manga/manhwa sync
        detail = await anilist.get_detail(ext)
        if not detail:
            raise HTTPException(502, "AniList'ten veri alınamadı")
        total = min(detail.get("total_chapters") or (c.total_chapters or 0), 500)
        for i in range(1, total + 1):
            if i not in existing_numbers:
                new_episodes.append(Episode(content_id=content_id, number=i, is_watched=False, is_new=False))

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
            "content_cover_url": u.content.cover_url if u.content else None,
            "content_type": u.content.type if u.content else None,
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

    ext = content.external_id
    api_count = 0
    source = "AniList"

    if ext.startswith("mdx:"):
        # MangaDex chapter count
        count = await mangadex.get_chapter_count(ext[4:])
        api_count = count or 0
        source = "MangaDex"
    elif ext.startswith("mal:"):
        # MAL — chapter/episode count via public API
        cfg = get_config()
        mal_client_id = cfg.get("mal_client_id", "")
        if not mal_client_id:
            return 0
        from backend.scraper import mal as mal_scraper
        count = await mal_scraper.get_chapter_count(ext[4:], content.type, mal_client_id)
        api_count = count or 0
        source = "MAL"
    else:
        # AniList
        detail = await anilist.get_detail(ext)
        if not detail:
            return 0
        if content.type == "anime":
            api_count = detail.get("total_episodes") or 0
        else:
            api_count = detail.get("total_chapters") or 0
        source = "AniList"

    db_count = (content.total_episodes if content.type == "anime" else content.total_chapters) or 0

    if api_count <= db_count or api_count == 0:
        return 0

    db.add(Update(
        content_id=content.id,
        episode_number=api_count,
        site_name=source,
        detected_at=datetime.utcnow(),
        is_read=False,
    ))

    if content.type == "anime":
        content.total_episodes = api_count
    else:
        content.total_chapters = api_count
    content.updated_at = datetime.utcnow()

    return api_count - db_count


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
