"""
FAZ-7c: Oyun indirme kaynagi yonetimi — FitGirl Repack entegrasyonu.
GET  /api/game/{id}/fitgirl/search  → FitGirl'de oyun ara
POST /api/game/{id}/fitgirl/link    → bulunan linki game_metadata.downloads'a ekle
GET  /api/game/{id}/downloads       → kaydedilmis download linklerini listele
DELETE /api/game/{id}/downloads/{idx} → link sil
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.database import get_db
from backend.models import Content
from backend.scraper import fitgirl

logger = logging.getLogger(__name__)

router = APIRouter()


class FitGirlLinkIn(BaseModel):
    title: str
    repack_size: Optional[str] = None
    magnet: Optional[str] = None
    torrent_url: Optional[str] = None
    page_url: Optional[str] = None


async def _get_game(content_id: int, db: AsyncSession) -> Content:
    r = await db.execute(select(Content).where(Content.id == content_id))
    c = r.scalar_one_or_none()
    if not c or c.type != "game":
        raise HTTPException(404, "Oyun bulunamadi")
    return c


def _get_downloads(c: Content) -> list[dict]:
    try:
        meta = json.loads(c.game_metadata) if c.game_metadata else {}
        return meta.get("downloads", [])
    except (json.JSONDecodeError, TypeError, AttributeError):
        return []


def _set_downloads(c: Content, downloads: list[dict]):
    try:
        meta = json.loads(c.game_metadata) if c.game_metadata else {}
    except (json.JSONDecodeError, TypeError):
        meta = {}
    meta["downloads"] = downloads
    c.game_metadata = json.dumps(meta, ensure_ascii=False)


# ── FitGirl Search ────────────────────────────────────────────────────

@router.get("/game/{content_id}/fitgirl/search")
async def fitgirl_search(content_id: int, q: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """FitGirl'de oyun ara. q verilmezse content.title kullanilir."""
    c = await _get_game(content_id, db)
    query = (q or c.title).strip()
    if not query:
        raise HTTPException(400, "Arama sorgusu gerekli")

    results = await fitgirl.search(query)
    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


# ── FitGirl Detail (magnet/torrent) ───────────────────────────────────

class FitGirlDetailIn(BaseModel):
    url: str


@router.post("/game/{content_id}/fitgirl/detail")
async def fitgirl_detail(content_id: int, body: FitGirlDetailIn, db: AsyncSession = Depends(get_db)):
    """FitGirl post sayfasindan magnet/torrent linklerini cek."""
    await _get_game(content_id, db)  # just validate
    detail = await fitgirl.get_detail(body.url)
    return detail


# ── Save / List / Delete Download Links ───────────────────────────────

@router.post("/game/{content_id}/fitgirl/link")
async def fitgirl_add_link(content_id: int, body: FitGirlLinkIn, db: AsyncSession = Depends(get_db)):
    """Bulunan download linkini content'e kalici olarak ekle."""
    c = await _get_game(content_id, db)
    downloads = _get_downloads(c)
    # Avoid duplicates by page_url or magnet
    for d in downloads:
        if (d.get("page_url") and d["page_url"] == body.page_url) or \
           (d.get("magnet") and body.magnet and d["magnet"] == body.magnet):
            raise HTTPException(409, "Bu link zaten kayitli")
    entry = body.model_dump(exclude_none=True)
    entry.setdefault("source", "fitgirl")
    downloads.append(entry)
    _set_downloads(c, downloads)
    await db.commit()
    return {"ok": True, "downloads": downloads, "count": len(downloads)}


@router.get("/game/{content_id}/downloads")
async def list_downloads(content_id: int, db: AsyncSession = Depends(get_db)):
    """Kaydedilmis tum download linklerini getir."""
    c = await _get_game(content_id, db)
    downloads = _get_downloads(c)
    return {"downloads": downloads, "count": len(downloads)}


@router.delete("/game/{content_id}/downloads/{idx}")
async def delete_download(content_id: int, idx: int, db: AsyncSession = Depends(get_db)):
    """Belirtilen download linkini sil."""
    c = await _get_game(content_id, db)
    downloads = _get_downloads(c)
    if idx < 0 or idx >= len(downloads):
        raise HTTPException(404, "Link bulunamadi")
    removed = downloads.pop(idx)
    _set_downloads(c, downloads)
    await db.commit()
    return {"ok": True, "removed": removed, "count": len(downloads)}
