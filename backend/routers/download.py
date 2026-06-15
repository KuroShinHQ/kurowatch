import os
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.downloader import manager

router = APIRouter()


# ── Modeller ─────────────────────────────────────────────────────────

class StartDownloadReq(BaseModel):
    content_id: int
    content_title: str
    media_type: str       # "anime" / "manga" / "manhwa"
    episode_number: int
    url: str
    quality: Optional[str] = "720p"


# ── Endpoint'ler ─────────────────────────────────────────────────────

@router.post("/download/start")
async def start_download(req: StartDownloadReq):
    job = await manager.add_job(
        content_id=req.content_id,
        content_title=req.content_title,
        media_type=req.media_type,
        episode_number=req.episode_number,
        url=req.url,
        quality=req.quality or "720p",
    )
    return job


@router.get("/download/queue")
async def get_queue():
    return {"jobs": manager.get_all_jobs()}


@router.delete("/download/{job_id}")
async def cancel_or_delete(job_id: int):
    job = manager.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job bulunamadı")
    if job["status"] == "done":
        manager.delete_job_file(job_id)
        return {"ok": True, "action": "file_deleted"}
    removed = manager.cancel_job(job_id)
    if not removed:
        raise HTTPException(400, "Aktif indirme iptal edilemez")
    return {"ok": True, "action": "cancelled"}


@router.get("/download/storage")
async def get_storage():
    total = manager.get_storage_bytes()
    return {"bytes": total, "mb": round(total / 1024 / 1024, 1)}


# ── Dosya Sunumu ─────────────────────────────────────────────────────

@router.get("/download/serve/{job_id}")
async def serve_video(job_id: int):
    """Tamamlanmış video dosyasını stream et (range request destekli)."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Dosya hazır değil")
    path = job.get("file_path")
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "Dosya bulunamadı")
    return FileResponse(path, media_type="video/mp4", headers={"Accept-Ranges": "bytes"})


@router.get("/download/subtitles/{job_id}")
async def serve_subtitles(job_id: int):
    """Video ile aynı dizindeki .vtt altyazı dosyasını sun (varsa)."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Bölüm hazır değil")
    path = job.get("file_path", "")
    base = os.path.splitext(path)[0]
    for candidate in (base + ".tr.vtt", base + ".vtt", base + ".tr.srt", base + ".srt"):
        if os.path.isfile(candidate):
            mime = "text/vtt" if candidate.endswith(".vtt") else "text/plain"
            return FileResponse(candidate, media_type=mime)
    raise HTTPException(404, "Altyazı bulunamadı")


@router.get("/download/pages/{job_id}")
async def list_manga_pages(job_id: int):
    """Manga bölümündeki sayfa URL'lerini listele."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done" or job["media_type"] not in ("manga", "manhwa"):
        raise HTTPException(404, "Manga bölümü hazır değil")
    dir_path = job.get("file_path")
    if not dir_path or not os.path.isdir(dir_path):
        raise HTTPException(404, "Dizin bulunamadı")

    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    files = sorted(f for f in os.listdir(dir_path) if os.path.splitext(f)[1].lower() in exts)
    pages = [f"/api/download/page/{job_id}/{i}" for i in range(len(files))]
    return {"pages": pages, "count": len(files)}


@router.get("/download/page/{job_id}/{page_index}")
async def serve_manga_page(job_id: int, page_index: int):
    """Tek manga sayfasını sun."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Bölüm hazır değil")
    dir_path = job.get("file_path")
    if not dir_path or not os.path.isdir(dir_path):
        raise HTTPException(404, "Dizin bulunamadı")

    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    files = sorted(f for f in os.listdir(dir_path) if os.path.splitext(f)[1].lower() in exts)
    if page_index < 0 or page_index >= len(files):
        raise HTTPException(404, f"Sayfa {page_index} mevcut değil ({len(files)} sayfa var)")

    full_path = os.path.join(dir_path, files[page_index])
    ext = os.path.splitext(files[page_index])[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "avif": "image/avif"}.get(ext.lstrip("."), "image/jpeg")
    return FileResponse(full_path, media_type=mime)


# ── WebSocket ────────────────────────────────────────────────────────

@router.websocket("/download/ws")
async def download_ws(ws: WebSocket):
    await manager.register_ws(ws)
    try:
        while True:
            await ws.receive_text()   # ping-pong: bağlantıyı canlı tut
    except WebSocketDisconnect:
        manager.unregister_ws(ws)
