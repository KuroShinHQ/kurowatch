import asyncio
import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.downloader import manager
from backend.downloader.integrity import DownloadIntegrityError, validate_manga_dir, validate_video_file
from backend.config import get_config
from backend.services.download_client import create_client

router = APIRouter()


# ── Modeller ─────────────────────────────────────────────────────────

class StartDownloadReq(BaseModel):
    content_id: int
    content_title: str
    media_type: str       # "anime" / "manga" / "manhwa"
    episode_number: int
    url: str
    quality: Optional[str] = "720p"


class TorrentAddReq(BaseModel):
    magnet: str
    save_path: Optional[str] = None


class TorrentActionReq(BaseModel):
    hash: str


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
        result = manager.delete_job_file(job_id)
        if not result.get("ok"):
            raise HTTPException(500, result.get("error") or result.get("action") or "Silme başarısız")
        return result
    if job["status"] in ("failed", "cancelled", "deleted"):
        if not manager.remove_done_job(job_id):
            raise HTTPException(404, "Job kaydı temizlenemedi")
        return {"ok": True, "action": "removed"}
    removed = manager.cancel_job(job_id)
    if not removed:
        raise HTTPException(400, "Aktif indirme iptal edilemez")
    return {"ok": True, "action": "cancelled"}


@router.get("/download/storage")
async def get_storage():
    total = manager.get_storage_bytes()
    return {"bytes": total, "mb": round(total / 1024 / 1024, 1)}


# ── Dosya Sunumu ─────────────────────────────────────────────────────

def _resolve_path(p: str) -> str:
    """Windows C:XXX -> /mnt/c/Xxx (WSL'de calisir)."""
    p = p.replace("\\", "/")
    import re as _re
    m = _re.match(r"^([A-Za-z]):/(.*)", p)
    if m:
        return f"/mnt/{m.group(1).lower()}/{m.group(2)}"
    return p


@router.get("/download/serve/{job_id}")
async def serve_video(job_id: int):
    """Tamamlanmış video dosyasını stream et (range request destekli)."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Dosya hazır değil")
    path = _resolve_path(job.get("file_path", ""))
    if not path or not os.path.isfile(path):
        # Dosya yoksa job'u temizle (eski kayit)
        manager.remove_done_job(job_id)
        raise HTTPException(404, "Dosya bulunamadı (kayıt temizlendi)")
    try:
        validate_video_file(path)
    except DownloadIntegrityError as exc:
        manager.delete_job_file(job_id)
        raise HTTPException(409, f"Video dosyası bozuk; kayıt temizlendi: {exc}")
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
    try:
        files_abs, _ = validate_manga_dir(dir_path)
    except DownloadIntegrityError as exc:
        manager.delete_job_file(job_id)
        raise HTTPException(409, f"Manga bölümü bozuk; kayıt temizlendi: {exc}")
    files = [os.path.basename(f) for f in files_abs]
    pages = [f"/api/download/page/{job_id}/{i}" for i in range(len(files))]
    return {"pages": pages, "count": len(files)}


@router.get("/download/page/{job_id}/{page_index}")
async def serve_manga_page(job_id: int, page_index: int):
    """Tek manga sayfasını sun."""
    job = manager.get_job(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(404, "Bölüm hazır değil")
    dir_path = job.get("file_path")
    try:
        files_abs, _ = validate_manga_dir(dir_path)
    except DownloadIntegrityError as exc:
        manager.delete_job_file(job_id)
        raise HTTPException(409, f"Manga bölümü bozuk; kayıt temizlendi: {exc}")
    files = [os.path.basename(f) for f in files_abs]
    if page_index < 0 or page_index >= len(files):
        raise HTTPException(404, f"Sayfa {page_index} mevcut değil ({len(files)} sayfa var)")

    full_path = os.path.join(dir_path, files[page_index])
    ext = os.path.splitext(files[page_index])[1].lower()
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "avif": "image/avif"}.get(ext.lstrip("."), "image/jpeg")
    return FileResponse(full_path, media_type=mime)


# ── Torrent Client Endpoints ─────────────────────────────────────────

@router.post("/download/add")
async def torrent_add(body: TorrentAddReq):
    """Add magnet to configured download client (qBittorrent/Aria2)."""
    cfg = get_config()
    client = create_client(cfg)
    if not client:
        raise HTTPException(400, "Hiçbir indirme istemcisi yapılandırılmamış (Ayarlar → İndirme İstemcisi)")
    result = await client.add_torrent(body.magnet, body.save_path)
    if not result:
        raise HTTPException(502, "Torrent eklenemedi — istemci bağlantısını kontrol et")
    return {"ok": True, "id": result}


@router.get("/download/torrent/status")
async def torrent_status():
    """Get all torrents from configured client."""
    cfg = get_config()
    client = create_client(cfg)
    if not client:
        return {"torrents": []}
    try:
        torrents = await client.get_status()
        return {"torrents": [t.to_dict() for t in torrents]}
    except Exception as e:
        return {"torrents": [], "error": str(e)}


@router.post("/download/torrent/pause")
async def torrent_pause(body: TorrentActionReq):
    cfg = get_config()
    client = create_client(cfg)
    if not client:
        raise HTTPException(400, "İstemci yapılandırılmamış")
    ok = await client.pause(body.hash)
    return {"ok": ok}


@router.post("/download/torrent/resume")
async def torrent_resume(body: TorrentActionReq):
    cfg = get_config()
    client = create_client(cfg)
    if not client:
        raise HTTPException(400, "İstemci yapılandırılmamış")
    ok = await client.resume(body.hash)
    return {"ok": ok}


@router.post("/download/torrent/remove")
async def torrent_remove(body: TorrentActionReq):
    cfg = get_config()
    client = create_client(cfg)
    if not client:
        raise HTTPException(400, "İstemci yapılandırılmamış")
    ok = await client.remove(body.hash)
    return {"ok": ok}


# ── SSE Live Stream ──────────────────────────────────────────────────

@router.get("/download/stream")
async def download_stream():
    """SSE endpoint: streams torrent status every second."""
    async def event_generator():
        while True:
            try:
                cfg = get_config()
                client = create_client(cfg)
                torrents = []
                if client:
                    t_list = await client.get_status()
                    torrents = [t.to_dict() for t in t_list]
                payload = json.dumps({"torrents": torrents}, ensure_ascii=False)
                yield f"data: {payload}\n\n"
            except Exception:
                yield "data: {\"torrents\":[]}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── WebSocket ────────────────────────────────────────────────────────

@router.websocket("/download/ws")
async def download_ws(ws: WebSocket):
    await manager.register_ws(ws)
    try:
        while True:
            await ws.receive_text()   # ping-pong: bağlantıyı canlı tut
    except WebSocketDisconnect:
        manager.unregister_ws(ws)
