"""
FAZ-5: Manga çevirisi API.
GET  /system/gpu                           → GPU + translator kurulum durumu
POST /translate/{content_id}/{episode}     → chapter çevirisi başlat
GET  /translate/{content_id}/{episode}     → çeviri durumu
GET  /translate/pages/{content_id}/{episode} → çevrilmiş sayfa URL listesi
GET  /translate/page/{content_id}/{episode}/{page_index} → tek çevrilmiş sayfa
DELETE /translate/{content_id}/{episode}   → çevrilmiş dosyaları sil
WebSocket /translate/ws                   → ilerleme push
"""
import os
import shutil
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from backend.downloader.manager import _DOWNLOADS_ROOT
from backend.translator.detect_gpu import detect_gpu
from backend.translator.engine import translate_chapter, list_pages, translated_dir

router = APIRouter()

# ── Bellek içi çeviri oturumları ─────────────────────────────────────
# key: "{content_id}:{episode_number}"
_sessions: dict[str, dict] = {}
_ws_clients: set[WebSocket] = set()

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


# ── Yardımcı ─────────────────────────────────────────────────────────

def _chapter_dir(content_id: int, episode_number: int) -> str:
    return os.path.join(_DOWNLOADS_ROOT, "manga", str(content_id),
                        f"ch{episode_number:04d}")


def _session_key(content_id: int, ep: int) -> str:
    return f"{content_id}:{ep}"


async def _broadcast(msg: dict) -> None:
    dead = set()
    for ws in _ws_clients:
        try:
            import json as _json
            await ws.send_text(_json.dumps(msg))
        except Exception:
            dead.add(ws)
    _ws_clients.difference_update(dead)


async def _run_translation(content_id: int, episode_number: int, target_lang: str, translator: str) -> None:
    key = _session_key(content_id, episode_number)
    ch_dir = _chapter_dir(content_id, episode_number)

    async def _on_progress(done: int, total: int) -> None:
        _sessions[key]["pages_done"] = done
        pct = round(done / total * 100) if total > 0 else 0
        await _broadcast({
            "event": "progress",
            "key": key,
            "pages_done": done,
            "pages_total": total,
            "pct": pct,
        })

    ok, out_dir = await translate_chapter(
        ch_dir, target_lang=target_lang, translator=translator, progress_cb=_on_progress
    )

    _sessions[key]["status"]     = "done" if ok else "failed"
    _sessions[key]["pages_done"] = _sessions[key]["pages_total"] if ok else _sessions[key]["pages_done"]

    await _broadcast({
        "event": "done" if ok else "failed",
        "key": key,
        **_sessions[key],
    })


# ── Endpoint'ler ──────────────────────────────────────────────────────

@router.get("/system/gpu")
async def get_gpu_info():
    """GPU + manga-image-translator kurulum durumu (frontend caching için)."""
    return detect_gpu()


@router.post("/translate/{content_id}/{episode_number}")
async def start_translation(content_id: int, episode_number: int,
                            target_lang: str = "TRK", translator: str = "m2m100"):
    """Chapter çevirisini arka planda başlat."""
    key = _session_key(content_id, episode_number)

    if key in _sessions and _sessions[key]["status"] in ("translating", "pending"):
        return _sessions[key]

    ch_dir = _chapter_dir(content_id, episode_number)
    pages = list_pages(ch_dir)
    if not pages:
        raise HTTPException(404, f"content_id={content_id} bölüm {episode_number} için sayfa bulunamadı")

    session = {
        "key": key,
        "content_id": content_id,
        "episode_number": episode_number,
        "status": "translating",
        "pages_total": len(pages),
        "pages_done": 0,
        "target_lang": target_lang,
        "translator": translator,
    }
    _sessions[key] = session

    import asyncio
    asyncio.create_task(_run_translation(content_id, episode_number, target_lang, translator))
    return session


@router.get("/translate/{content_id}/{episode_number}")
async def get_translation_status(content_id: int, episode_number: int) -> dict:
    """Çeviri oturumu durumu."""
    key = _session_key(content_id, episode_number)
    if key not in _sessions:
        # Daha önce tamamlanmış olabilir — dizini kontrol et
        ch_dir = _chapter_dir(content_id, episode_number)
        tr_dir = translated_dir(ch_dir)
        if os.path.isdir(tr_dir):
            pages = sorted(f for f in os.listdir(tr_dir) if os.path.splitext(f)[1].lower() in _IMAGE_EXTS)
            if pages:
                return {"status": "done", "pages_total": len(pages), "pages_done": len(pages), "key": key}
        return {"status": "not_started", "key": key}
    return _sessions[key]


@router.get("/translate/pages/{content_id}/{episode_number}")
async def list_translated_pages(content_id: int, episode_number: int) -> dict:
    """Çevrilmiş sayfa URL'lerini listele."""
    ch_dir = _chapter_dir(content_id, episode_number)
    tr_dir = translated_dir(ch_dir)
    if not os.path.isdir(tr_dir):
        return {"pages": [], "count": 0}
    files = sorted(f for f in os.listdir(tr_dir) if os.path.splitext(f)[1].lower() in _IMAGE_EXTS)
    pages = [f"/api/translate/page/{content_id}/{episode_number}/{i}" for i in range(len(files))]
    return {"pages": pages, "count": len(files)}


@router.get("/translate/page/{content_id}/{episode_number}/{page_index}")
async def serve_translated_page(content_id: int, episode_number: int, page_index: int):
    """Tek çevrilmiş sayfayı sun."""
    ch_dir = _chapter_dir(content_id, episode_number)
    tr_dir = translated_dir(ch_dir)
    if not os.path.isdir(tr_dir):
        raise HTTPException(404, "Çeviri dizini bulunamadı")
    files = sorted(f for f in os.listdir(tr_dir) if os.path.splitext(f)[1].lower() in _IMAGE_EXTS)
    if page_index < 0 or page_index >= len(files):
        raise HTTPException(404, f"Sayfa {page_index} mevcut değil ({len(files)} sayfa var)")
    full_path = os.path.join(tr_dir, files[page_index])
    ext = os.path.splitext(files[page_index])[1].lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "webp": "image/webp", "avif": "image/avif"}.get(ext, "image/jpeg")
    return FileResponse(full_path, media_type=mime)


@router.delete("/translate/{content_id}/{episode_number}")
async def delete_translation(content_id: int, episode_number: int) -> dict:
    """Çevrilmiş dosyaları sil."""
    key = _session_key(content_id, episode_number)
    _sessions.pop(key, None)
    ch_dir = _chapter_dir(content_id, episode_number)
    tr_dir = translated_dir(ch_dir)
    if os.path.isdir(tr_dir):
        shutil.rmtree(tr_dir)
        return {"deleted": True}
    return {"deleted": False}


@router.websocket("/translate/ws")
async def translate_ws(ws: WebSocket):
    """İlerleme push — mevcut oturumları gönder, sonra bekle."""
    await ws.accept()
    _ws_clients.add(ws)
    try:
        import json as _json
        await ws.send_text(_json.dumps({"event": "state", "sessions": list(_sessions.values())}))
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(ws)
