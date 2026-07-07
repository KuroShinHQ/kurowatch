import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

_COVERS_DIR = Path(__file__).parent.parent.parent / "covers"
_COVERS_DIR.mkdir(exist_ok=True)

from backend.config import get_config
from backend.database import get_db
from backend.models import Content, ContentTag, Tag
from backend.scraper import anilist
from backend.scraper import igdb, mal

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
    genres: Optional[List[str]] = None
    runtime_minutes: Optional[int] = None
    release_year: Optional[int] = None


class ContentPatch(BaseModel):
    title: Optional[str] = None
    title_tr: Optional[str] = None
    type: Optional[str] = None
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
    genres: Optional[List[str]] = None
    runtime_minutes: Optional[int] = None
    release_year: Optional[int] = None


def _serialize(c: Content) -> dict:
    try:
        genres = json.loads(c.genres) if c.genres else []
    except Exception:
        genres = []
    return {
        "id": c.id,
        "title": c.title,
        "title_tr": c.title_tr or "",
        "type": c.type,
        "cover_url": c.cover_url,
        "external_id": c.external_id,
        "status": c.status,
        "total_episodes": c.total_episodes,
        "total_chapters": c.total_chapters,
        "my_progress": c.my_progress,
        "my_progress_pct": c.my_progress_pct,
        "my_score": c.my_score,
        "external_score": c.external_score,
        "note_text": c.note_text,
        "note_is_spoiler": c.note_is_spoiler,
        "synopsis": c.synopsis or "",
        "synopsis_tr": c.synopsis_tr or "",
        "genres": genres,
        "season_number": c.season_number if hasattr(c, 'season_number') else 1,
        "parent_id": c.parent_id if hasattr(c, 'parent_id') else None,
        "runtime_minutes": c.runtime_minutes,
        "release_year": c.release_year,
        "added_at": c.added_at.isoformat() if c.added_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        "sites": [
            {"id": s.id, "site_name": s.site_name, "site_url": s.site_url,
             "is_primary": s.is_primary, "latest_known_ep": s.latest_known_ep, "is_dead": s.is_dead}
            for s in sorted(
                c.sites or [],
                key=lambda s: (
                    1 if s.is_dead else 0,
                    -(s.latest_known_ep or -1),
                    0 if s.is_primary else 1,
                )
            )
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
    if body.type not in ("anime", "manga", "manhwa", "game", "series", "movie"):
        raise HTTPException(400, "Geçersiz içerik tipi")

    data = body.model_dump()
    genres_list = data.pop("genres", None)
    c = Content(**data)
    c.genres = json.dumps(genres_list) if genres_list else None
    c.added_at = datetime.utcnow()
    c.updated_at = datetime.utcnow()
    db.add(c)
    await db.commit()
    await db.refresh(c)
    new_id = c.id
    return await get_content(new_id, db)


@router.get("/content/{content_id}/seasons")
async def get_seasons(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    pid = getattr(c, 'parent_id', None)
    root_id = pid if pid else c.id
    stmt = select(Content).where(
        or_(Content.id == root_id, Content.parent_id == root_id)
    ).order_by(Content.season_number)
    res2 = await db.execute(stmt)
    seasons = res2.scalars().all()
    return [
        {"id": s.id, "season_number": getattr(s, 'season_number', 1) or 1,
         "title": s.title_tr or s.title, "cover_url": s.cover_url, "status": s.status}
        for s in seasons
    ]


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
        {"id": e.id, "season": getattr(e, "season", 1) or 1,
         "number": e.number, "title": e.title,
         "url": e.url, "is_watched": e.is_watched,
         "watched_at": e.watched_at.isoformat() if e.watched_at else None,
         "is_new": e.is_new}
        for e in sorted(c.episodes, key=lambda e: (getattr(e, "season", 1) or 1, e.number))
    ]
    return d


@router.patch("/content/{content_id}")
async def patch_content(content_id: int, body: ContentPatch, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")

    for field, val in body.model_dump(exclude_unset=True).items():
        if field == "genres":
            setattr(c, field, json.dumps(val))
        else:
            setattr(c, field, val)
    c.updated_at = datetime.utcnow()
    await db.commit()
    return await get_content(content_id, db)


class ProgressUpdate(BaseModel):
    progress: int


@router.post("/content/{content_id}/tags/auto-assign-type", status_code=200)
async def auto_assign_type_tag(content_id: int, db: AsyncSession = Depends(get_db)):
    """Content type'ına göre otomatik content_type_tag ata."""
    result = await db.execute(select(Content).where(Content.id == content_id).options(selectinload(Content.tags)))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    r2 = await db.execute(select(Tag).where(Tag.tag_type == "api", Tag.name == c.type))
    tag = r2.scalar_one_or_none()
    if not tag:
        raise HTTPException(404, f"'{c.type}' için sistem etiketi bulunamadı")
    already = any(ct.tag_id == tag.id for ct in (c.tags or []))
    if not already:
        db.add(ContentTag(content_id=c.id, tag_id=tag.id))
        await db.commit()
    return {"ok": True, "tag": tag.name}


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


# ── AniList Canlı Veri (synopsis + nextAiringEpisode) ────────────────

@router.get("/content/{content_id}/anilist")
async def get_content_anilist(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    if not c.external_id:
        raise HTTPException(404, "Harici ID yok")

    ext = c.external_id
    cfg = get_config()

    if ext.startswith("mdx:"):
        from backend.scraper import mangadex
        detail = await mangadex.get_detail(ext[4:])
    elif ext.startswith("mal:"):
        detail = await mal.get_detail(ext[4:], c.type, cfg.get("mal_client_id", ""))
    elif c.type == "game":
        detail = await igdb.get_detail(ext, cfg.get("igdb_client_id", ""), cfg.get("igdb_client_secret", ""))
    else:
        detail = await anilist.get_detail(ext)

    if not detail:
        raise HTTPException(503, "Harici kaynaktan veri alınamadı")

    # Lazy-save: synopsis varsa ve DB'de yoksa kaydet
    syn = (detail.get("synopsis") or "").strip()
    if syn and not c.synopsis:
        import re
        clean = re.sub(r'<[^>]+>', '', syn).strip()
        c.synopsis = clean
        c.updated_at = datetime.utcnow()
        await db.commit()

    return detail


# ── Genres Otopatch ─────────────────────────────────────────────────

@router.post("/genres/patch-all")
async def patch_all_genres(db: AsyncSession = Depends(get_db)):
    """external_id'si olan ama genres'i boş içeriklere AniList'ten genres çeker."""
    stmt = select(Content).where(
        Content.external_id.isnot(None),
        or_(Content.genres.is_(None), Content.genres == "[]", Content.genres == ""),
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    patched = 0
    failed = 0
    for c in items:
        detail = await anilist.get_detail(c.external_id)
        if detail and detail.get("genres"):
            c.genres = json.dumps(detail["genres"])
            patched += 1
        else:
            failed += 1

    await db.commit()
    return {"patched": patched, "failed": failed, "total": len(items)}


# ── Cover Zenginleştirme ─────────────────────────────────────────────

def _title_variants(title: str) -> list[str]:
    """Bir başlık için AniList'e denenmesi gereken varyantları üret."""
    variants = [title]
    # Parantez içeriği sil: "Frieren: Beyond Journey's End (Sousou no Frieren)" → "Frieren: Beyond Journey's End"
    no_paren = re.sub(r'\s*\([^)]+\)', '', title).strip()
    if no_paren and no_paren != title:
        variants.append(no_paren)
    # İki nokta üstüste'den sonrasını at: "Zom 100: Zombie ni..." → "Zom 100"
    colon_short = title.split(':')[0].strip()
    if colon_short and colon_short != title and len(colon_short) >= 4:
        variants.append(colon_short)
    # Parantezli + iki nokta kısaltma birlikte
    if no_paren:
        colon_of_clean = no_paren.split(':')[0].strip()
        if colon_of_clean and colon_of_clean not in variants and len(colon_of_clean) >= 4:
            variants.append(colon_of_clean)
    # Sezon belirteci kaldır: "(S2)", "(Season 2)"
    season_re = re.compile(r'\s*(\([Ss]\d+\)|\([Ss]eason\s*\d+\)|Part\s+\d+)$', re.IGNORECASE)
    no_season = season_re.sub('', title).strip()
    if no_season and no_season != title and no_season not in variants:
        variants.append(no_season)
    return variants


@router.post("/content/enrich-covers")
async def enrich_covers(db: AsyncSession = Depends(get_db)):
    """Cover'ı olmayan anime/manga içerikler için AniList'te agresif arama yap."""
    stmt = select(Content).where(
        Content.cover_url.is_(None),
        Content.type.in_(["anime", "manga", "manhwa", "series", "movie"]),
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    enriched = 0
    failed = []

    for c in items:
        found = None
        for variant in _title_variants(c.title):
            try:
                results = await anilist.search(variant, c.type)
                if results:
                    found = results[0]
                    break
                await asyncio.sleep(0.3)
            except Exception:
                pass

        if found and found.get("cover_url"):
            c.cover_url = found["cover_url"]
            if not c.external_id:
                c.external_id = found.get("external_id")
            if not c.genres and found.get("genres"):
                c.genres = json.dumps(found["genres"])
            if not c.total_episodes and found.get("total_episodes"):
                c.total_episodes = found["total_episodes"]
            if not c.total_chapters and found.get("total_chapters"):
                c.total_chapters = found["total_chapters"]
            c.updated_at = datetime.utcnow()
            enriched += 1
        else:
            failed.append(c.title)
        await asyncio.sleep(0.4)

    await db.commit()
    return {"enriched": enriched, "failed_count": len(failed), "failed_titles": failed[:10]}


# ── Browser Extension: Otomatik İlerleme ────────────────────────────

class AutoProgressIn(BaseModel):
    title: str
    episode: Optional[int] = None
    chapter: Optional[int] = None
    site: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None


@router.post("/progress/auto")
async def auto_progress(body: AutoProgressIn, db: AsyncSession = Depends(get_db)):
    """Browser extension: fuzzy title match → ilerleme güncelle."""
    import re

    def _norm(s: str) -> str:
        return re.sub(r"[^\w\s]", "", s.lower()).strip()

    result = await db.execute(select(Content))
    all_items = result.scalars().all()

    q = _norm(body.title)
    best: Optional[Content] = None
    best_score = 0.0

    for c in all_items:
        cn = _norm(c.title)
        if cn == q:
            best = c
            best_score = 1.0
            break
        if q in cn or cn in q:
            score = min(len(q), len(cn)) / max(len(q), len(cn), 1)
            if score > best_score:
                best, best_score = c, score

    if not best or best_score < 0.5:
        from fastapi import HTTPException as _H
        raise _H(404, f"'{body.title}' için eşleşme bulunamadı (en iyi: {best_score:.2f})")

    progress = body.episode or body.chapter or 0
    if progress > (best.my_progress or 0):
        best.my_progress = progress
        if best.status == "planning":
            best.status = "watching"
        best.updated_at = datetime.utcnow()
        await db.commit()
        return {"action": "updated", "content_id": best.id, "title": best.title,
                "progress": best.my_progress, "score": round(best_score, 2)}

    return {"action": "unchanged", "content_id": best.id, "title": best.title,
            "progress": best.my_progress, "score": round(best_score, 2)}


# ── Discover (AniList proxy) ─────────────────────────────────────────

@router.get("/discover")
async def discover(
    q: Optional[str] = Query(None),
    type: str = Query("anime"),
    genre: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
):
    # Oyun araması → IGDB
    if type == "game":
        if not q:
            raise HTTPException(400, "Oyun araması için q parametresi gerekli")
        cfg = get_config()
        return await igdb.search(q, cfg.get("igdb_client_id", ""), cfg.get("igdb_client_secret", ""), page)

    # series/movie: henüz keşif yok (manuel ekleme)
    if type in ("series", "movie"):
        return []

    if not q and not genre:
        raise HTTPException(400, "q veya genre parametresi gerekli")
    if type not in ("anime", "manga", "manhwa"):
        raise HTTPException(400, "Geçersiz tip (anime/manga/manhwa/series/movie/game)")

    results = await anilist.search(q, type, page, genre)

    # AniList 0 sonuç + q var + genre yok → MAL fallback
    if not results and q and not genre and type in ("anime", "manga"):
        cfg = get_config()
        mal_id = cfg.get("mal_client_id", "")
        if mal_id:
            results = await mal.search(q, type, mal_id, page)

    return results


@router.post("/content/{content_id}/cover")
async def upload_cover(content_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Content).where(Content.id == content_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Bulunamadı")
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    dest = _COVERS_DIR / f"{content_id}{ext}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    c.cover_url = f"/covers/{content_id}{ext}"
    c.updated_at = datetime.utcnow()
    await db.commit()
    return {"cover_url": c.cover_url}


@router.get("/discover/mangadex")
async def discover_mangadex(
    q: str = Query(..., min_length=1),
    type: str = Query("manga"),
    page: int = Query(1, ge=1),
):
    """MangaDex doğrudan arama (manga/manhwa)."""
    if type not in ("manga", "manhwa"):
        raise HTTPException(400, "Geçersiz tip (manga/manhwa)")
    from backend.scraper import mangadex
    return await mangadex.search(q, type, page)
