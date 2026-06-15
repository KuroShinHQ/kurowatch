import json
import os
from fastapi import APIRouter
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
    # Sadece bilinen key'leri güncelle (extra key reddedilmez ama saklanmaz)
    for k in _DEFAULTS:
        if k in body:
            cfg[k] = body[k]
    _save(cfg)
    return cfg
