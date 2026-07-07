"""
İndirme kuyruğu — max 2 eşzamanlı, WebSocket ilerleme push, JSON persist.
Daisy-chain: oynatma başladığında N+1 otomatik kuyruğa alınır (player.js tetikler).
"""
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
from fastapi import WebSocket

from backend.downloader.integrity import (
    remove_output_base_artifacts,
    remove_path,
    remove_video_artifacts,
    validate_manga_dir,
    validate_manga_files,
    validate_video_file,
)

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
_active_tasks: dict[int, asyncio.Task] = {}


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
        cleaned: list[dict] = []
        for job in data:
            if job.get("status") == "done":
                path = job.get("file_path")
                try:
                    if job.get("media_type") in ("anime", "series", "movie", "cartoon"):
                        job["file_size_bytes"] = validate_video_file(path)
                    elif job.get("media_type") in ("manga", "manhwa"):
                        _, total_bytes = validate_manga_dir(path)
                        job["file_size_bytes"] = total_bytes
                except Exception as exc:
                    print(f"[manager] stale done job atlandi #{job.get('id')}: {exc}")
                    continue
            cleaned.append(job)
        _done.extend(cleaned)
        if len(cleaned) != len(data):
            _save_jobs()
        if _done:
            _counter = max(j["id"] for j in _done)
    except Exception as exc:
        print(f"[manager] jobs.json yüklenemedi: {exc}")


def _normalize_path(p: str) -> str:
    """Windows C:XXX -> /mnt/c/Xxx (WSL'de calisir)."""
    p = p.replace("\\", "/")
    m = re.match(r"^([A-Za-z]):/(.*)", p)
    if m:
        return f"/mnt/{m.group(1).lower()}/{m.group(2)}"
    return p


def scan_downloaded_files():
    """Diskteki .mp4/.mkv dosyalarini tara, jobs'a ekle (eksik olanlari tamamla)."""
    global _done, _counter
    anime_root = os.path.join(_DOWNLOADS_ROOT, "anime")
    if not os.path.isdir(anime_root):
        return
    indexed = set()
    for j in _done:
        fp = j.get("file_path")
        if fp:
            indexed.add((j.get("content_id"), j.get("episode_number"),
                         _normalize_path(fp)))
    for cid_str in os.listdir(anime_root):
        cid_path = os.path.join(anime_root, cid_str)
        if not os.path.isdir(cid_path):
            continue
        try:
            content_id = int(cid_str)
        except ValueError:
            continue
        for fname in sorted(os.listdir(cid_path)):
            if not fname.endswith((".mp4", ".mkv")):
                continue
            m = re.match(r"ep(\d+)", fname)
            if not m:
                continue
            ep_num = int(m.group(1))
            file_path = os.path.join(cid_path, fname)
            try:
                file_size = validate_video_file(file_path)
            except Exception as exc:
                print(f"[manager] bozuk video atlandi: {file_path} ({exc})")
                continue
            if (content_id, ep_num, _normalize_path(file_path)) in indexed:
                continue
            _counter += 1
            job = {
                "id": _counter,
                "content_id": content_id,
                "content_title": f"Content #{content_id}",
                "media_type": "anime",
                "episode_number": ep_num,
                "url": "",
                "quality": "720p",
                "status": "done",
                "progress_pct": 100,
                "file_path": file_path,
                "error_msg": None,
                "file_size_bytes": file_size,
                "created_at": _now_iso(),
                "completed_at": _now_iso(),
            }
            _done.append(job)
    if _done:
        _save_jobs()


def _save_jobs():
    """Tamamlanan/başarısız job'ları diske kaydet."""
    try:
        os.makedirs(_DOWNLOADS_ROOT, exist_ok=True)
        with open(_JOBS_FILE, "w", encoding="utf-8") as f:
            json.dump(_done[-200:], f, ensure_ascii=False)
    except Exception as exc:
        print(f"[manager] jobs.json kaydedilemedi: {exc}")


def _job_dir(job: dict) -> str:
    if job["media_type"] in ("anime", "series", "movie", "cartoon"):
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
    return list(_queue) + list(_active.values()) + list(_done)


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
    # Aktif indirmeyi iptal et (asyncio task cancel)
    if job_id in _active_tasks:
        _active_tasks.pop(job_id).cancel()
        if job_id in _active:
            job = _active.pop(job_id)
            job["status"] = "cancelled"
            _done.append(job)
            _save_jobs()
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


def remove_done_job(job_id: int) -> bool:
    """Job'u _done listesinden kaldir (status farketmez)."""
    global _done
    job = next((j for j in _done if j["id"] == job_id), None)
    if job:
        path = job.get("file_path")
        try:
            if path and os.path.exists(path):
                if job.get("media_type") in ("anime", "series", "movie", "cartoon"):
                    remove_video_artifacts(path)
                else:
                    remove_path(path)
        except OSError:
            pass
    before = len(_done)
    _done[:] = [j for j in _done if j["id"] != job_id]
    if len(_done) < before:
        _save_jobs()
        return True
    return False


def delete_job_file(job_id: int) -> dict:
    """Indirilmis dosyayi/dizini sil ve job kaydini temizle."""
    global _done
    job = get_job(job_id)
    if not job or job["status"] != "done":
        return {"ok": False, "action": "not_done"}
    path = job.get("file_path")
    try:
        if path and os.path.exists(path):
            if job.get("media_type") in ("anime", "series", "movie", "cartoon"):
                remove_video_artifacts(path)
            else:
                remove_path(path)
            action = "file_deleted"
        else:
            action = "stale_job_removed"

        _done[:] = [j for j in _done if j["id"] != job_id]
        _save_jobs()
        return {"ok": True, "action": action}
    except OSError as exc:
        return {"ok": False, "action": "delete_failed", "error": str(exc)}


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
        task = asyncio.create_task(_run_job(job))
        _active_tasks[job["id"]] = task


async def _run_job(job: dict):
    from backend.downloader.anime import download_anime
    from backend.downloader.manga import download_manga_chapter

    job["status"] = "downloading"
    await _broadcast({"event": "started", "job": job})
    cleanup_path: str | None = None
    cleanup_base: str | None = None

    try:
        if job["media_type"] in ("anime", "series", "movie", "cartoon"):
            await _broadcast({"event": "progress", "job_id": job["id"], "pct": 0,
                              "msg": "Stream URL araştırılıyor..."})
            out_dir = _job_dir(job)
            os.makedirs(out_dir, exist_ok=True)
            out_base = os.path.join(out_dir, f"ep{job['episode_number']:03d}")
            cleanup_base = out_base

            async def _on_pct(pct: int):
                job["progress_pct"] = pct
                await _broadcast({"event": "progress", "job_id": job["id"], "pct": pct})

            file_path = await download_anime(
                job["url"], out_base, job.get("quality", "720p"),
                _on_pct, content_id=job.get("content_id"),
                media_type=job.get("media_type", "anime"))
            validate_video_file(file_path)
            job["file_path"] = file_path
            job["file_size_bytes"] = os.path.getsize(file_path)

        else:  # manga / manhwa
            out_dir = _job_dir(job)
            cleanup_path = out_dir
            total_pages: list[int] = [0]

            async def _on_page(downloaded: int, total: int):
                if total > 0:
                    total_pages[0] = total
                pct = int(downloaded / total * 100) if total > 0 else min(99, downloaded * 5)
                job["progress_pct"] = pct
                await _broadcast({"event": "progress", "job_id": job["id"], "pct": pct})

            files = await download_manga_chapter(job["url"], out_dir, _on_page)
            total_bytes = validate_manga_files(files)
            job["file_path"] = out_dir
            job["file_size_bytes"] = total_bytes
            # Otonom etiket senkronizasyonu: manga/manhwa kaynak etiketleri
            content_id = job.get("content_id")
            if content_id:
                try:
                    from backend.downloader.manga import extract_manga_chapter_tags
                    from backend.services import tag_sync
                    tags = await extract_manga_chapter_tags(job["url"])
                    if tags:
                        await tag_sync.sync_site_tags(content_id, urlparse(job["url"]).netloc, tags)
                except Exception as exc:  # noqa: BLE001
                    import logging
                    logging.getLogger(__name__).warning("Manga tag sync failed: %s", exc)

        job["status"] = "done"
        job["progress_pct"] = 100
        job["completed_at"] = _now_iso()

    except asyncio.CancelledError:
        job["status"] = "cancelled"
        if cleanup_base:
            remove_output_base_artifacts(cleanup_base)
        elif cleanup_path:
            try:
                remove_path(cleanup_path)
            except OSError:
                pass
    except Exception as exc:
        job["status"] = "failed"
        job["error_msg"] = str(exc)[:500]
        if cleanup_base:
            remove_output_base_artifacts(cleanup_base)
        elif cleanup_path:
            try:
                remove_path(cleanup_path)
            except OSError:
                pass

    finally:
        _active.pop(job["id"], None)
        _active_tasks.pop(job["id"], None)
        if job["status"] != "cancelled":
            _done.append(job)
            _save_jobs()
            await _broadcast({"event": "done", "job": job})
        _start_next()
