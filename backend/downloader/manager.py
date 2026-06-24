"""
İndirme kuyruğu — max 2 eşzamanlı, WebSocket ilerleme push, JSON persist.
Daisy-chain: oynatma başladığında N+1 otomatik kuyruğa alınır (player.js tetikler).
"""
import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import WebSocket

_MAX_CONCURRENT = 2

_DOWNLOADS_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "downloads")
)
_JOBS_FILE = os.path.join(_DOWNLOADS_ROOT, "jobs.json")

_queue:  list[dict] = []
_active: dict[int, dict] = {}
_done:   list[dict] = []
_ws_clients: set[WebSocket] = set()
_counter = 0
_lock = asyncio.Lock()


# ── Genel Yardımcı ───────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_jobs():
    """Startup: daha önce kaydedilmiş job'ları yükle (restart'ta kayıp önleme)."""
    global _done, _counter
    if not os.path.isfile(_JOBS_FILE):
        return
    try:
        with open(_JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _done.extend(data)
        if _done:
            _counter = max(j["id"] for j in _done)
    except Exception as exc:
        print(f"[manager] jobs.json yüklenemedi: {exc}")


def _save_jobs():
    """Tamamlanan/başarısız job'ları diske kaydet."""
    try:
        os.makedirs(_DOWNLOADS_ROOT, exist_ok=True)
        with open(_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(_done[-200:], f, ensure_ascii=False)
    except Exception as exc:
        print(f"[manager] jobs.json kaydedilemedi: {exc}")


def _job_dir(job: dict) -> str:
    if job["media_type"] == "anime":
        return os.path.join(_DOWNLOADS_ROOT, "anime", str(job["content_id"]))
    return os.path.join(_DOWNLOADS_ROOT, "manga", str(job["content_id"]),
                        f"ch{job['episode_number']:04d}")


# ── Dışa açık API ────────────────────────────────────────────────────

async def add_job(
    content_id: int,
    content_title: str,
    media_type: str,
    episode_number: int,
    url: str,
    quality: str = "720p",
) -> dict:
    global _counter
    async with _lock:
        # Aynı bölüm zaten kuyrukta/aktif mi?
        for j in _queue + list(_active.values()):
            if j["content_id"] == content_id and j["episode_number"] == episode_number:
                return j  # zaten var

        _counter += 1
        job: dict = {
            "id": _counter,
            "content_id": content_id,
            "content_title": content_title,
            "media_type": media_type,
            "episode_number": episode_number,
            "url": url,
            "quality": quality,
            "status": "queued",
            "progress_pct": 0,
            "file_path": None,
            "error_msg": None,
            "file_size_bytes": None,
            "created_at": _now_iso(),
            "completed_at": None,
        }
        _queue.append(job)

    await _broadcast({"event": "queued", "job": job})
    _start_next()
    return job


def get_all_jobs() -> list[dict]:
    return list(_queue) + list(_active.values()) + _done[-50:]


def get_job(job_id: int) -> Optional[dict]:
    for j in get_all_jobs():
        if j["id"] == job_id:
            return j
    return None


def cancel_job(job_id: int) -> bool:
    global _queue
    for i, j in enumerate(_queue):
        if j["id"] == job_id:
            _queue.pop(i)
            return True
    return False


def get_storage_bytes() -> int:
    total = 0
    if not os.path.isdir(_DOWNLOADS_ROOT):
        return 0
    for root, _, files in os.walk(_DOWNLOADS_ROOT):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def delete_job_file(job_id: int) -> bool:
    """İndirilmiş dosyayı/dizini sil (izle-sil için)."""
    import shutil
    job = get_job(job_id)
    if not job or job["status"] != "done":
        return False
    path = job.get("file_path")
    if not path or not os.path.exists(path):
        return False
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        job["status"] = "deleted"
        job["file_path"] = None
        return True
    except OSError:
        return False


# ── WebSocket ────────────────────────────────────────────────────────

async def register_ws(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    all_jobs = get_all_jobs()
    await ws.send_json({"event": "state", "jobs": all_jobs})


def unregister_ws(ws: WebSocket):
    _ws_clients.discard(ws)


async def _broadcast(msg: dict):
    dead: set[WebSocket] = set()
    for ws in _ws_clients:
        try:
            await ws.send_json(msg)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _ws_clients.discard(ws)


# ── Kuyruk İşlemcisi ─────────────────────────────────────────────────

def _start_next():
    while len(_active) < _MAX_CONCURRENT and _queue:
        job = _queue.pop(0)
        _active[job["id"]] = job
        asyncio.create_task(_run_job(job))


async def _run_job(job: dict):
    from backend.downloader.anime import download_anime
    from backend.downloader.manga import download_manga_chapter

    job["status"] = "downloading"
    await _broadcast({"event": "started", "job": job})

    try:
        if job["media_type"] == "anime":
            out_dir = _job_dir(job)
            os.makedirs(out_dir, exist_ok=True)
            out_base = os.path.join(out_dir, f"ep{job['episode_number']:03d}")

            async def _on_pct(pct: int):
                job["progress_pct"] = pct
                await _broadcast({"event": "progress", "job_id": job["id"], "pct": pct})

            file_path = await download_anime(job["url"], out_base, job.get("quality", "720p"), _on_pct)
            job["file_path"] = file_path
            job["file_size_bytes"] = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        else:  # manga / manhwa
            out_dir = _job_dir(job)
            total_pages: list[int] = [0]

            async def _on_page(downloaded: int, total: int):
                if total > 0:
                    total_pages[0] = total
                pct = int(downloaded / total * 100) if total > 0 else min(99, downloaded * 5)
                job["progress_pct"] = pct
                await _broadcast({"event": "progress", "job_id": job["id"], "pct": pct})

            files = await download_manga_chapter(job["url"], out_dir, _on_page)
            job["file_path"] = out_dir
            job["file_size_bytes"] = sum(
                os.path.getsize(f) for f in files if os.path.exists(f)
            )

        job["status"] = "done"
        job["progress_pct"] = 100
        job["completed_at"] = _now_iso()

    except Exception as exc:
        job["status"] = "failed"
        job["error_msg"] = str(exc)[:500]

    finally:
        _active.pop(job["id"], None)
        _done.append(job)
        _save_jobs()
        await _broadcast({"event": "done", "job": job})
        _start_next()
