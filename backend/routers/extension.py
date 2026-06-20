"""
FAZ-6 Browser Extension endpoint'leri.
GET  /api/extension/status   → ping (popup için)
GET  /api/extension/sites    → desteklenen site listesi
POST /api/extension/capture  → URL+title+episode → AniList ara → DB ekle/güncelle
"""
import json
from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Content, Site, Episode
from backend.scraper import anilist

router = APIRouter()

SUPPORTED_SITES = [
    {"id": "crunchyroll",   "name": "Crunchyroll",   "url": "crunchyroll.com",    "type": "anime"},
    {"id": "diziwatch",     "name": "Diziwatch",     "url": "diziwatch.com",      "type": "anime"},
    {"id": "mangadex",      "name": "MangaDex",      "url": "mangadex.org",       "type": "manga"},
    {"id": "tranimeizle",   "name": "Tranimeizle",   "url": "tranimeizle.co",     "type": "anime"},
    {"id": "tranimaci",     "name": "Tranimaci",     "url": "tranimaci.com",      "type": "anime"},
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

    matched = await _search_anilist(req.title, req.type)

    if existing:
        progress = req.episode or req.chapter or existing.my_progress
        changed = False
        if progress > existing.my_progress:
            existing.my_progress = progress
            changed = True
        if existing.status == "planning":
            existing.status = "watching"
            changed = True
        # Cover yoksa AniList'ten doldur
        if not existing.cover_url and matched and matched.get("cover_url"):
            existing.cover_url = matched["cover_url"]
            changed = True
        # Genres yoksa doldur
        if not existing.genres and matched and matched.get("genres"):
            existing.genres = json.dumps(matched["genres"])
            changed = True
        # Site URL yoksa ekle
        await _ensure_site(db, existing.id, req.site, req.url)
        # Episode kaydı oluştur/güncelle
        if req.episode:
            await _ensure_episode(db, existing.id, req.episode, req.url)
        await db.commit()
        return {
            "action": "updated",
            "content_id": existing.id,
            "title": existing.title,
            "progress": existing.my_progress,
        }

    content = Content(
        title=matched["title"] if matched else req.title,
        type=_map_type(req.type),
        status="watching",
        cover_url=matched.get("cover_url") if matched else None,
        external_id=matched.get("external_id") if matched else None,
        total_episodes=matched.get("total_episodes") if matched else None,
        total_chapters=matched.get("total_chapters") if matched else None,
        genres=json.dumps(matched["genres"]) if matched and matched.get("genres") else None,
        my_progress=req.episode or req.chapter or 0,
    )
    db.add(content)
    await db.commit()
    await db.refresh(content)

    await _ensure_site(db, content.id, req.site, req.url)
    if req.episode:
        await _ensure_episode(db, content.id, req.episode, req.url)
    await db.commit()

    return {
        "action": "created",
        "content_id": content.id,
        "title": content.title,
        "progress": content.my_progress,
        "anilist_matched": matched is not None,
    }


async def _ensure_site(db: AsyncSession, content_id: int, site_name: str, url: str) -> None:
    """Site kaydı yoksa oluştur (duplicate URL/domain kontrolü ile)."""
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    result = await db.execute(select(Site).where(Site.content_id == content_id))
    existing_sites = result.scalars().all()
    if any(urlparse(s.site_url).netloc == domain for s in existing_sites):
        return
    is_primary = len(existing_sites) == 0
    db.add(Site(content_id=content_id, site_name=site_name, site_url=url, is_primary=is_primary))


async def _ensure_episode(db: AsyncSession, content_id: int, ep_num: int, url: str) -> None:
    """Episode kaydı yoksa oluştur; varsa URL'yi güncelle."""
    result = await db.execute(
        select(Episode).where(Episode.content_id == content_id, Episode.number == ep_num)
    )
    ep = result.scalar_one_or_none()
    if ep:
        if not ep.url and url:
            ep.url = url
    else:
        db.add(Episode(content_id=content_id, number=ep_num, url=url, is_watched=True, is_new=False))


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
    """Tam başlık → kısaltılmış → tek kelime sırasıyla dene."""
    import re
    try:
        results = await anilist.search(title, content_type=content_type)
        if results:
            return results[0]
        # Türkçe ek kelimelerini kırp ("2. Kısım", "2 Kisim", "Part 2", "Season 2" vb.)
        short = re.sub(
            r"\s*\d+\.?\s*(Kısım|Kisim|Sezon|Season|Part|Bölüm|Bolum|Chapter|Cour)\b.*",
            "", title, flags=re.IGNORECASE
        ).strip()
        # Türkçe sıfat eklerini kırp (" Path", " Yolu", " no", "'s" vb.) → ilk kelime(ler)
        short = re.sub(r"\s*(Path|Yolu|Yolculuğu|no|of|the|'s|'s)\b.*", "", short, flags=re.IGNORECASE).strip()
        if short and short.lower() != title.lower():
            results2 = await anilist.search(short, content_type=content_type)
            if results2:
                return results2[0]
        # Son çare: sadece ilk kelime
        first_word = title.split()[0] if title else ""
        if first_word and first_word.lower() not in (short.lower(), title.lower()):
            results3 = await anilist.search(first_word, content_type=content_type)
            if results3:
                return results3[0]
        # En son: ilk kelimenin trailing-s kırpılmış hali ("Bakis" → "Baki")
        if first_word and first_word.endswith("s") and len(first_word) > 2:
            stripped = first_word[:-1]
            results4 = await anilist.search(stripped, content_type=content_type)
            if results4:
                return results4[0]
        return None
    except Exception:
        return None


def _map_type(t: str) -> str:
    return {"anime": "anime", "manga": "manga", "manhwa": "manhwa"}.get(t, "anime")
