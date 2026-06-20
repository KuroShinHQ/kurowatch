import asyncio
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_config
from backend.database import get_db
from backend.models import Content, Episode, Site, Update
from backend.scraper import anilist
from backend.scraper import mangadex


def _extract_ep_from_url(url: str) -> int | None:
    """Site URL'inden mevcut bölüm numarasını çıkar."""
    patterns = [
        r'-(\d+)-bolum',       # anime: -24-bolum-izle
        r'bolum[/-](\d+)',     # manga: bolum-457 veya bolum/457
        r'[/-](\d+)[.-]?bolum',# manga: /457-bolum
        r'chapter[/-](\d+)',   # chapter-200
        r'[/-](\d+)/?$',       # URL sonu /24
    ]
    for pattern in patterns:
        m = re.search(pattern, url, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


def _derive_ep_url(site_url: str, current_ep: int, target_ep: int) -> str | None:
    """Mevcut bölüm numarasını URL'de hedef numarayla değiştir."""
    if not site_url or not current_ep or current_ep == target_ep:
        return site_url if current_ep == target_ep else None

    s = str(current_ep)
    t = str(target_ep)

    # Öncelikli kalıplar: bolum bağlamı
    priority_patterns = [
        (r'-' + re.escape(s) + r'-bolum', f'-{t}-bolum'),
        (r'bolum[/-]' + re.escape(s), f'bolum-{t}'),
        (r'[/-]' + re.escape(s) + r'-bolum', f'/{t}-bolum'),
        (r'chapter[/-]' + re.escape(s), f'chapter-{t}'),
    ]
    for pattern, replacement in priority_patterns:
        m = re.search(pattern, site_url, re.IGNORECASE)
        if m:
            return site_url[:m.start()] + replacement + site_url[m.end():]

    # Fallback: sayıyı word-boundary ile değiştir (tek eşleşme varsa)
    pattern = r'(?<![0-9])' + re.escape(s) + r'(?![0-9])'
    matches = list(re.finditer(pattern, site_url))
    if len(matches) == 1:
        m = matches[0]
        return site_url[:m.start()] + t + site_url[m.end():]
    if len(matches) > 1:
        # bolum/chapter bağlamındaki eşleşmeyi tercih et
        for m in matches:
            ctx = site_url[max(0, m.start()-12):m.end()+12].lower()
            if 'bolum' in ctx or 'chapter' in ctx:
                return site_url[:m.start()] + t + site_url[m.end():]
        # son eşleşme
        m = matches[-1]
        return site_url[:m.start()] + t + site_url[m.end():]

    return None

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


class EpisodeSyncBody(BaseModel):
    season: int = 1
    anilist_override_id: Optional[str] = None


@router.post("/content/{content_id}/episodes/sync")
async def sync_episodes(content_id: int, body: EpisodeSyncBody = Body(default=EpisodeSyncBody()), db: AsyncSession = Depends(get_db)):
    """Harici kaynaktan bölüm listesini çek, yeni olanları DB'ye kaydet."""
    result = await db.execute(
        select(Content)
        .options(selectinload(Content.sites))
        .where(Content.id == content_id)
    )
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")

    if c.type == "game":
        raise HTTPException(400, "Oyunlar için bölüm sync desteklenmiyor")

    # MAL prefix varsa external_id yok sayılır — site URL'den ilerle
    has_anilist_id = c.external_id and not c.external_id.startswith("mal:") and not c.external_id.startswith("mdx:")

    # Primary site URL'den bölüm URL türetme için temel bilgiler
    primary_site = next((s for s in (c.sites or []) if s.is_primary), None) or (c.sites[0] if c.sites else None)
    site_base_url = primary_site.site_url if primary_site else None
    site_current_ep = _extract_ep_from_url(site_base_url) if site_base_url else None

    season = body.season if body else 1
    existing_q = await db.execute(
        select(Episode).where(Episode.content_id == content_id, Episode.season == season)
    )
    existing_eps = {e.number: e for e in existing_q.scalars().all()}
    existing_numbers = set(existing_eps.keys())

    ext = (body.anilist_override_id if body and body.anilist_override_id else None) or c.external_id or ""
    new_episodes: list[Episode] = []
    total = 0

    if ext.startswith("mdx:"):
        chapters = await mangadex.get_chapters(ext[4:])
        if not chapters:
            raise HTTPException(502, "MangaDex'ten bölüm listesi alınamadı")
        for ch_num, ch_uuid in chapters.items():
            ep_url = f"https://mangadex.org/chapter/{ch_uuid}"
            if ch_num not in existing_numbers:
                new_episodes.append(Episode(
                    content_id=content_id, season=season, number=ch_num,
                    url=ep_url, is_watched=False, is_new=False,
                ))
                existing_numbers.add(ch_num)
            elif not existing_eps[ch_num].url:
                existing_eps[ch_num].url = ep_url
        if chapters:
            new_total = max(chapters.keys())
            c.total_chapters = new_total
            c.updated_at = datetime.utcnow()

    elif ext.startswith("mal:") or not has_anilist_id:
        # AniList ID yok → sadece site URL'den bölüm sayısını çıkar
        total = site_current_ep or (c.total_episodes if c.type == "anime" else c.total_chapters) or 0
        if not total:
            raise HTTPException(400, "Bölüm sayısı bilinmiyor — site URL'sinde bölüm numarası bulunamadı. Lütfen manuel olarak site URL'sini ekleyin.")

    elif c.type == "anime":
        detail = await anilist.get_detail(ext)
        if not detail:
            raise HTTPException(502, "AniList'ten veri alınamadı")
        # Streaming URL map — sadece URL bilgisi için, bölüm SAYISI için DEĞİL
        # AniList streamingEpisodes eksik veri içerebilir (bazı animeler için 1-2 bölüm)
        streaming_url_map: dict[int, str] = {}
        for se in (detail.get("streaming_episodes") or []):
            m_s = re.search(r'Episode\s+(\d+)', se.get("title", ""), re.IGNORECASE)
            if m_s:
                n_s = int(m_s.group(1))
                u_s = se.get("url") or (_derive_ep_url(site_base_url, site_current_ep, n_s) if site_current_ep else None)
                if u_s:
                    streaming_url_map[n_s] = u_s
        # Bölüm sayısı her zaman total_episodes'tan (streaming count DEĞİL)
        total = detail.get("total_episodes") or (c.total_episodes or 0)
        if not total and streaming_url_map:
            total = max(streaming_url_map.keys())
        # Bölümleri oluştur (URL: site türetme > streaming — kullanıcının sitesi her zaman öncelikli)
        for i in range(1, int(total) + 1):
            site_ep_url = _derive_ep_url(site_base_url, site_current_ep, i) if site_current_ep else None
            fallback_url = streaming_url_map.get(i)
            ep_url = site_ep_url or fallback_url
            if i not in existing_numbers:
                new_episodes.append(Episode(
                    content_id=content_id, season=season, number=i,
                    url=ep_url or None,
                    is_watched=False, is_new=False,
                ))
                existing_numbers.add(i)
            else:
                # Site URL varsa her zaman güncelle (streaming URL'nin üzerine yaz)
                if site_ep_url:
                    existing_eps[i].url = site_ep_url
                elif not existing_eps[i].url and fallback_url:
                    existing_eps[i].url = fallback_url
        total = 0  # alt döngünün tekrar çalışmasını önle

    else:
        # AniList manga/manhwa sync
        detail = await anilist.get_detail(ext)
        if not detail:
            raise HTTPException(502, "AniList'ten veri alınamadı")
        total = min(detail.get("total_chapters") or (c.total_chapters or 0), 500)

    # total bölümlü içerikler için bölüm listesi oluştur (URL türeterek)
    if total > 0:
        for i in range(1, int(total) + 1):
            derived_url = _derive_ep_url(site_base_url, site_current_ep, i) if site_current_ep else None
            if i not in existing_numbers:
                new_episodes.append(Episode(
                    content_id=content_id, season=season, number=i,
                    url=derived_url,
                    is_watched=False, is_new=False,
                ))
            elif derived_url and not existing_eps[i].url:
                # Mevcut URL-siz episodu güncelle
                existing_eps[i].url = derived_url

    if new_episodes:
        db.add_all(new_episodes)
    await db.commit()

    eps_q = await db.execute(
        select(Episode).where(Episode.content_id == content_id).order_by(Episode.season, Episode.number)
    )
    eps = eps_q.scalars().all()
    return {
        "synced": len(new_episodes),
        "season": season,
        "episodes": [
            {"id": e.id, "season": getattr(e, "season", 1) or 1,
             "number": e.number, "title": e.title, "url": e.url,
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
    try:
        return await asyncio.wait_for(_check_one_impl(content, db), timeout=8.0)
    except (asyncio.TimeoutError, Exception):
        return 0


async def _check_one_impl(content: Content, db: AsyncSession) -> int:
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
    """İzlenen içerikler için AniList'e sorgu at, yeni bölüm varsa Update kaydı oluştur."""
    result = await db.execute(
        select(Content)
        .where(Content.status == "watching")
        .limit(10)
    )
    items = result.scalars().all()

    found = 0
    # AniList rate limit: 90 req/dk → her istek arasına 0.7s
    for c in items:
        new = await _check_one(c, db)
        found += new
        if new:
            await asyncio.sleep(0.7)

    await db.commit()

    if found:
        try:
            from backend import push_manager
            push_manager.send_push(
                title="KuroWatch — Yeni Güncelleme",
                body=f"{found} yeni bölüm bulundu!",
                url="/#screen-updates",
            )
        except Exception:
            pass

    return {"checked": len(items), "new_updates": found}
