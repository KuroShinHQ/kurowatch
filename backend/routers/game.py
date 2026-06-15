"""
FAZ-7b: Oyun oturumu takibi.
POST /api/game/{id}/session/start  → oturum başlat
POST /api/game/{id}/session/stop   → oturum durdur, süreyi kaydet
GET  /api/game/{id}/sessions       → toplam süre + oturum listesi
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Content, GameSession

router = APIRouter()

# In-memory aktif oturumlar {content_id: unix_start_ts}
_active: dict[int, float] = {}


@router.post("/game/{content_id}/session/start")
async def session_start(content_id: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(Content, content_id)
    if not c or c.type != "game":
        raise HTTPException(404, "Oyun bulunamadı")
    if content_id in _active:
        return {"ok": True, "status": "already_running", "started_at": _active[content_id]}
    _active[content_id] = time.time()
    if c.status == "planning":
        c.status = "watching"
        await db.commit()
    return {"ok": True, "status": "started", "started_at": _active[content_id]}


@router.post("/game/{content_id}/session/stop")
async def session_stop(content_id: int, db: AsyncSession = Depends(get_db)):
    start = _active.pop(content_id, None)
    if start is None:
        raise HTTPException(400, "Bu oyun için aktif oturum yok")
    duration = max(1, int((time.time() - start) / 60))
    db.add(GameSession(content_id=content_id, duration_minutes=duration))
    await db.commit()
    return {"ok": True, "duration_minutes": duration}


@router.get("/game/{content_id}/sessions")
async def sessions_list(content_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(GameSession)
        .where(GameSession.content_id == content_id)
        .order_by(GameSession.started_at.desc())
        .limit(20)
    )
    sessions = result.scalars().all()
    total = sum(s.duration_minutes for s in sessions)
    hours, mins = divmod(total, 60)
    return {
        "total_minutes": total,
        "total_label": f"{hours}sa {mins}dk" if hours else f"{mins}dk",
        "active": content_id in _active,
        "active_since": _active.get(content_id),
        "sessions": [
            {"id": s.id, "duration_minutes": s.duration_minutes, "started_at": s.started_at.isoformat()}
            for s in sessions
        ],
    }
