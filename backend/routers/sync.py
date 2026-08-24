import json
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from backend.database import get_db
from backend.models import Content, Site, Episode, Update, Tag, ContentTag

router = APIRouter()

# export/import tasinan tum scalar alanlar (tek kaynak — export ve upsert ayni listeyi kullanir)
_SCALARS = [
    "title", "title_tr", "type", "cover_url", "external_id", "status",
    "total_episodes", "total_chapters", "my_progress", "my_progress_pct",
    "my_score", "external_score", "note_text", "note_is_spoiler",
    "synopsis", "synopsis_tr", "genres", "season_number",
    "runtime_minutes", "release_year", "developer", "publisher", "game_metadata",
]


def _dt(d):
    return d.isoformat() if d else None


def _parse_dt(v):
    return datetime.fromisoformat(v) if v else None


async def _full_export(db: AsyncSession) -> dict:
    """Tum tablolari JSON'a dokum (episodes + sites + tags DAHIL — S-166 fix'i)."""
    r_c = await db.execute(select(Content).options(
        selectinload(Content.sites),
        selectinload(Content.episodes),
        selectinload(Content.updates),
        selectinload(Content.tags).selectinload(ContentTag.tag),
    ))
    contents = r_c.scalars().all()

    r_t = await db.execute(select(Tag))
    tags = r_t.scalars().all()

    by_id = {c.id: c for c in contents}
    out = []
    for c in contents:
        item = {k: getattr(c, k) for k in _SCALARS}
        item["added_at"] = _dt(c.added_at)
        item["updated_at"] = _dt(c.updated_at)
        # parent_id yerine parent_external_id (import'ta cozumlenir — id'ler kayar)
        item["parent_external_id"] = by_id[c.parent_id].external_id if c.parent_id in by_id else None
        item["sites"] = [
            {"site_name": s.site_name, "site_url": s.site_url,
             "is_primary": s.is_primary, "latest_known_ep": s.latest_known_ep,
             "is_dead": s.is_dead}
            for s in c.sites
        ]
        item["episodes"] = [
            {"season": e.season, "number": e.number, "title": e.title,
             "url": e.url, "is_watched": e.is_watched,
             "watched_at": _dt(e.watched_at), "is_new": e.is_new}
            for e in c.episodes
        ]
        item["tag_ids"] = [ct.tag_id for ct in c.tags]
        out.append(item)

    return {
        "version": 2,
        "exported_at": datetime.utcnow().isoformat(),
        "contents": out,
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


async def _apply_relations(db: AsyncSession, content: Content, item: dict):
    """sites + episodes + tag_ids restore (idempotent: once temizle sonra ekle)."""
    if "sites" in item:
        await db.execute(delete(Site).where(Site.content_id == content.id))
        for s in item["sites"] or []:
            db.add(Site(
                content_id=content.id,
                site_name=s.get("site_name", ""),
                site_url=s.get("site_url", ""),
                is_primary=bool(s.get("is_primary", False)),
                latest_known_ep=s.get("latest_known_ep"),
                is_dead=s.get("is_dead"),
            ))
    if "episodes" in item:
        await db.execute(delete(Episode).where(Episode.content_id == content.id))
        for e in item["episodes"] or []:
            db.add(Episode(
                content_id=content.id,
                season=e.get("season", 1) or 1,
                number=e.get("number", 0) or 0,
                title=e.get("title"),
                url=e.get("url"),
                is_watched=bool(e.get("is_watched", False)),
                watched_at=_parse_dt(e.get("watched_at")),
                is_new=bool(e.get("is_new", False)),
            ))
    if "tag_ids" in item:
        await db.execute(delete(ContentTag).where(ContentTag.content_id == content.id))
        for tid in item["tag_ids"] or []:
            db.add(ContentTag(content_id=content.id, tag_id=tid))


async def _upsert(item: dict, db: AsyncSession, ctx: dict):
    """Tek icerigi ekle/guncelle; ctx: {added, id_map, parent_queue}."""
    ctx["added"] += 1
    ext_id = item.get("external_id")
    existing = None
    if ext_id:
        r = await db.execute(select(Content).where(Content.external_id == ext_id))
        existing = r.scalar_one_or_none()

    if existing is not None:
        for k in _SCALARS:
            if k != "id" and k in item:
                setattr(existing, k, item[k])
        if item.get("updated_at"):
            existing.updated_at = _parse_dt(item["updated_at"]) or existing.updated_at
        content = existing
    else:
        kwargs = {k: item[k] for k in _SCALARS if k in item and k != "id"}
        kwargs.setdefault("status", "planning")
        kwargs.setdefault("my_progress", 0)
        kwargs.setdefault("note_is_spoiler", False)
        kwargs.setdefault("season_number", 1)
        kwargs["season_number"] = kwargs["season_number"] or 1
        c = Content(
            added_at=datetime.utcnow(),
            updated_at=_parse_dt(item.get("updated_at")) or datetime.utcnow(),
            **kwargs,
        )
        db.add(c)
        await db.flush()
        content = c
        if ext_id:
            ctx["id_map"][ext_id] = c.id

    # parent cozumleme: parent_external_id -> id (ikinci geciste baglanir)
    p_ext = item.get("parent_external_id")
    if p_ext:
        if p_ext in ctx["id_map"]:
            content.parent_id = ctx["id_map"][p_ext]
        else:
            ctx["parent_queue"].append((content, p_ext))

    await _apply_relations(db, content, item)


@router.post("/import/resolve")
async def resolve_import(body: ResolveBody, db: AsyncSession = Depends(get_db)):
    """Çakışma kararlarını + yeni öğeleri DB'ye uygula (episodes/sites/tags dahil)."""
    ctx = {"added": 0, "id_map": {}, "parent_queue": []}

    for dec in body.decisions:
        if dec.get("choice") == "import":
            await _upsert(dec["data"], db, ctx)

    for item in (body.new_items or []):
        await _upsert(item, db, ctx)

    # ikinci gecis: parent'lari bagla
    linked = 0
    for content, p_ext in ctx["parent_queue"]:
        if p_ext in ctx["id_map"]:
            content.parent_id = ctx["id_map"][p_ext]
            linked += 1

    await db.commit()
    return {"ok": True, "added": ctx["added"], "parents_linked": linked}
