import json
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Content, Episode, GameSession

router = APIRouter()

TYPE_LABELS = {"anime": "Anime", "manga": "Manga", "manhwa": "Manhwa",
               "series": "Dizi", "movie": "Film", "game": "Oyun"}
TYPE_ORDER = ["anime", "manga", "manhwa", "series", "movie", "game"]


@router.get("/analytics/summary")
async def analytics_summary(db: AsyncSession = Depends(get_db)):
    # ── Toplam içerik sayıları ───────────────────────────────────────
    total = await db.scalar(select(func.count(Content.id)))
    total = total or 0

    rows = await db.execute(
        select(Content.type, func.count(Content.id).label("cnt"))
        .group_by(Content.type)
    )
    type_counts = {t: 0 for t in TYPE_ORDER}
    for row in rows:
        if row.type in type_counts:
            type_counts[row.type] = row.cnt

    # ── Tamamlanan içerik ────────────────────────────────────────────
    completed = await db.scalar(
        select(func.count(Content.id)).where(Content.status == "completed")
    )
    completed = completed or 0

    # ── Ortalama puan ─────────────────────────────────────────────────
    avg_score_row = await db.execute(
        select(func.avg(Content.my_score)).where(Content.my_score.isnot(None))
    )
    avg_score = round(float(avg_score_row.scalar() or 0), 1)

    # ── Toplam izleme süresi (dakika) ────────────────────────────────
    total_minutes = 0

    # Anime: my_progress * 24dk
    r = await db.execute(
        select(func.coalesce(func.sum(Content.my_progress), 0))
        .where(Content.type == "anime")
    )
    total_minutes += (r.scalar() or 0) * 24

    # Series: my_progress * runtime_minutes (fallback 45dk)
    r = await db.execute(
        select(func.coalesce(func.sum(
            Content.my_progress * func.coalesce(Content.runtime_minutes, 45)
        ), 0))
        .where(Content.type == "series")
    )
    total_minutes += r.scalar() or 0

    # Movie: runtime_minutes (fallback 120dk)
    r = await db.execute(
        select(func.coalesce(func.sum(
            func.coalesce(Content.runtime_minutes, 120)
        ), 0))
        .where(Content.type == "movie")
    )
    total_minutes += r.scalar() or 0

    # Manga: my_progress * 5dk
    r = await db.execute(
        select(func.coalesce(func.sum(Content.my_progress), 0))
        .where(Content.type == "manga")
    )
    total_minutes += (r.scalar() or 0) * 5

    # Manhwa: my_progress * 3dk
    r = await db.execute(
        select(func.coalesce(func.sum(Content.my_progress), 0))
        .where(Content.type == "manhwa")
    )
    total_minutes += (r.scalar() or 0) * 3

    # Game: GameSession duration_minutes
    r = await db.execute(
        select(func.coalesce(func.sum(GameSession.duration_minutes), 0))
    )
    total_minutes += r.scalar() or 0

    total_hours = round(total_minutes / 60, 1)

    # ── Tür frekansları ──────────────────────────────────────────────
    genre_rows = await db.execute(
        select(Content.genres).where(Content.genres.isnot(None))
    )
    genre_counts = {}
    for (g_str,) in genre_rows:
        try:
            glist = json.loads(g_str) if isinstance(g_str, str) else (g_str or [])
            for g in glist:
                genre_counts[g] = genre_counts.get(g, 0) + 1
        except (json.JSONDecodeError, TypeError):
            pass
    top_genres = sorted(genre_counts.items(), key=lambda x: -x[1])[:8]

    # ── Haftalık aktivite (son 7 gün) ───────────────────────────────
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=6)
    day_names_tr = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"]

    weekly_days = []
    for i in range(7):
        d = week_ago + timedelta(days=i)
        day_start = datetime(d.year, d.month, d.day)
        day_end = day_start + timedelta(days=1)

        count = await db.scalar(
            select(func.count(Episode.id))
            .where(Episode.watched_at >= day_start)
            .where(Episode.watched_at < day_end)
        )

        added = await db.scalar(
            select(func.count(Content.id))
            .where(Content.added_at >= day_start)
            .where(Content.added_at < day_end)
        )

        weekly_days.append({
            "day": day_names_tr[d.weekday() + 1] if d.weekday() < 6 else "Paz",
            "day_index": d.weekday(),
            "episodes_watched": count or 0,
            "items_added": added or 0,
            "total_actions": (count or 0) + (added or 0),
        })

    max_actions = max((wd["total_actions"] for wd in weekly_days), default=1)

    # ── Oyun toplam indirme boyutu (game_metadata JSON içinde yok, 0) ─
    game_download_gb = 0

    return {
        "total_items": total,
        "type_counts": type_counts,
        "completed_count": completed,
        "avg_score": avg_score,
        "total_hours": total_hours,
        "total_minutes": round(total_minutes),
        "top_genres": [{"name": g, "count": c} for g, c in top_genres],
        "weekly_activity": weekly_days,
        "weekly_max_actions": max_actions,
        "game_download_gb": game_download_gb,
    }
