import json
import os
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")

_DEFAULTS = {
    "igdb_client_id": "",
    "igdb_client_secret": "",
    "igdb_token": "",
    "igdb_token_expires_at": 0,
    "mal_client_id": "",
    "mal_client_secret": "",
    "vapid_public_key": "",
    "vapid_private_key": "",
    "duration_anime_ep": 24,
    "duration_manga_ch": 5,
    "duration_manhwa_ch": 3,
    "duration_game_session": 60,
    "check_on_startup": True,
    "default_quality": "720p",
    "max_concurrent_downloads": 2,
    "auto_delete_after_watch": False,
    "daisy_chain_trigger_pct": 50,
    "deepl_api_key": "",
    "translation_fallback": "google",
}


def _load() -> dict:
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        # Eksik key'leri default ile doldur
        for k, v in _DEFAULTS.items():
            data.setdefault(k, v)
        return data
    return dict(_DEFAULTS)


def _save(cfg: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


@router.get("/settings")
async def get_settings():
    return _load()


@router.post("/settings")
async def update_settings(body: dict):
    cfg = _load()
    for k in _DEFAULTS:
        if k in body:
            cfg[k] = body[k]
    _save(cfg)
    return cfg


# ── Cookies yönetimi ─────────────────────────────────────────────────

_COOKIES_DIR = Path(__file__).parent.parent.parent / "cookies"


@router.post("/settings/cookies/{site_name}")
async def upload_cookies(site_name: str, file: UploadFile = File(...)):
    """Netscape format cookies.txt yükle. site_name: tranimeizle, turkanime, diziwatch, genel"""
    _COOKIES_DIR.mkdir(exist_ok=True)
    safe_name = site_name.replace("/", "").replace("\\", "").replace("..", "")
    if not safe_name:
        raise HTTPException(400, "Geçersiz site adı")
    fname = f"{safe_name}_cookies.txt" if not safe_name.startswith("cookies") else "cookies.txt"
    dest = _COOKIES_DIR / fname
    content = await file.read()
    dest.write_bytes(content)
    return {"ok": True, "file": fname, "bytes": len(content)}


@router.get("/settings/cookies")
async def list_cookies():
    """Yüklü cookies dosyalarını listele."""
    _COOKIES_DIR.mkdir(exist_ok=True)
    files = []
    for f in _COOKIES_DIR.glob("*.txt"):
        files.append({"name": f.name, "bytes": f.stat().st_size})
    return {"files": files}


@router.delete("/settings/cookies/{file_name}")
async def delete_cookies(file_name: str):
    """Cookies dosyasını sil."""
    safe = file_name.replace("/", "").replace("\\", "").replace("..", "")
    p = _COOKIES_DIR / safe
    if p.exists():
        p.unlink()
        return {"ok": True}
    raise HTTPException(404, "Dosya bulunamadı")
