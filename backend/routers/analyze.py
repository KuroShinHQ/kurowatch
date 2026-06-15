"""
FAZ-4: Chromaprint intro tespiti API.
POST /analyze/intro/{content_id}      → indirilen tüm bölümleri analiz et
GET  /analyze/intro/{content_id}      → bu içeriğin tüm intro zamanları
GET  /analyze/intro/{content_id}/{ep} → tek bölüm intro zamanı (player için)
"""
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy import select, delete

from backend.database import AsyncSessionLocal
from backend.models import IntroTimestamp
from backend.analyzer.chromaprint import fingerprint_file
from backend.analyzer.intro_detector import compare_fingerprints, consensus_intro
from backend.downloader.manager import _DOWNLOADS_ROOT

router = APIRouter()

# ── Yardımcı ─────────────────────────────────────────────────────────

def _episode_paths(content_id: int) -> list[tuple[int, str]]:
    """downloads/anime/{content_id}/ içindeki ep*.mp4 dosyalarını döner."""
    base = os.path.join(_DOWNLOADS_ROOT, "anime", str(content_id))
    if not os.path.isdir(base):
        return []
    result = []
    for fname in sorted(os.listdir(base)):
        if not fname.startswith("ep") or not fname.endswith(".mp4"):
            continue
        try:
            ep_num = int(fname[2:5])  # "ep001.mp4" → 1
        except ValueError:
            continue
        result.append((ep_num, os.path.join(base, fname)))
    return result


async def _analyze_content(content_id: int) -> list[dict]:
    """
    Tüm bölümler için fingerprint üret, çift karşılaştır, intro zamanlarını kaydet.
    Returns: per-episode intro timestamp listesi.
    """
    episodes = _episode_paths(content_id)
    if len(episodes) < 2:
        return []

    # 1) Tüm fingerprint'ları hesapla
    fps_data: list[tuple[int, dict]] = []
    for ep_num, path in episodes:
        data = await fingerprint_file(path)
        if data:
            fps_data.append((ep_num, data))

    if len(fps_data) < 2:
        return []

    # 2) Tüm çift kombinasyonlarını karşılaştır
    pair_results: list[dict] = []
    for i in range(len(fps_data)):
        for j in range(i + 1, len(fps_data)):
            ep1_num, d1 = fps_data[i]
            ep2_num, d2 = fps_data[j]
            r = compare_fingerprints(
                d1["fingerprint"], d1["fps"],
                d2["fingerprint"], d2["fps"],
            )
            if r:
                r["ep1_number"] = ep1_num
                r["ep2_number"] = ep2_num
                pair_results.append(r)

    if not pair_results:
        return []

    # 3) Her bölüm için consensus hesapla
    intros: list[dict] = []
    for ep_num, _ in fps_data:
        relevant = [r for r in pair_results if r.get("ep1_number") == ep_num or r.get("ep2_number") == ep_num]
        ts = consensus_intro(relevant, ep_num)
        if ts:
            intros.append({"episode_number": ep_num, **ts})

    # 4) DB'ye kaydet
    if intros:
        async with AsyncSessionLocal() as db:
            # Eski kayıtları temizle
            await db.execute(delete(IntroTimestamp).where(IntroTimestamp.content_id == content_id))
            for row in intros:
                db.add(IntroTimestamp(
                    content_id=content_id,
                    episode_number=row["episode_number"],
                    intro_start=row["start"],
                    intro_end=row["end"],
                    confidence=row["confidence"],
                ))
            await db.commit()

    return intros


# ── Endpoint'ler ──────────────────────────────────────────────────────

@router.post("/analyze/intro/{content_id}")
async def analyze_intro(content_id: int, background_tasks: BackgroundTasks):
    """Arka planda analiz başlat, hemen job bilgisi döner."""
    episodes = _episode_paths(content_id)
    if not episodes:
        raise HTTPException(404, f"content_id={content_id} için indirilmiş bölüm bulunamadı")
    if len(episodes) < 2:
        raise HTTPException(400, "Intro tespiti için en az 2 indirilmiş bölüm gerekli")

    background_tasks.add_task(_analyze_content, content_id)
    return {
        "status": "analyzing",
        "content_id": content_id,
        "episode_count": len(episodes),
        "message": "Analiz arka planda başladı. GET /api/analyze/intro/{id} ile sonucu kontrol edin.",
    }


@router.get("/analyze/intro/{content_id}")
async def get_all_intros(content_id: int):
    """Bu içeriğin tüm bölümlerine ait intro zamanları."""
    async with AsyncSessionLocal() as db:
        rows = (await db.execute(
            select(IntroTimestamp)
            .where(IntroTimestamp.content_id == content_id)
            .order_by(IntroTimestamp.episode_number)
        )).scalars().all()

    return {
        "content_id": content_id,
        "intros": [
            {
                "episode_number": r.episode_number,
                "start": r.intro_start,
                "end":   r.intro_end,
                "confidence": r.confidence,
            }
            for r in rows
        ],
    }


@router.get("/analyze/intro/{content_id}/{episode_number}")
async def get_episode_intro(content_id: int, episode_number: int) -> dict:
    """Tek bölüm intro zamanı — player.js tarafından kullanılır."""
    async with AsyncSessionLocal() as db:
        row = (await db.execute(
            select(IntroTimestamp).where(
                IntroTimestamp.content_id == content_id,
                IntroTimestamp.episode_number == episode_number,
            )
        )).scalar_one_or_none()

    if not row:
        return {"found": False}

    return {
        "found": True,
        "start": row.intro_start,
        "end":   row.intro_end,
        "confidence": row.confidence,
    }


@router.delete("/analyze/intro/{content_id}")
async def clear_intros(content_id: int):
    """Bu içeriğin intro verilerini sil (yeniden analiz için)."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            delete(IntroTimestamp).where(IntroTimestamp.content_id == content_id)
        )
        await db.commit()
    return {"deleted": result.rowcount}
