import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.database import init_db
from backend.routers import content, episodes, sites, tags, settings, sync, download, push

_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
_CONFIG_PATH  = os.path.join(os.path.dirname(__file__), "config.json")

_DEFAULTS = {
    "check_on_startup": True,
    "igdb_client_id": "", "igdb_client_secret": "",
    "igdb_token": "", "igdb_token_expires_at": 0,
    "mal_client_id": "",
    "vapid_public_key": "", "vapid_private_key": "",
    "duration_anime_ep": 24, "duration_manga_ch": 5,
    "duration_manhwa_ch": 3, "duration_game_session": 60,
    "default_quality": "720p", "max_concurrent_downloads": 2,
    "auto_delete_after_watch": False, "daisy_chain_trigger_pct": 50,
    "deepl_api_key": "", "translation_fallback": "google",
}


def _get_config() -> dict:
    if os.path.exists(_CONFIG_PATH):
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        for k, v in _DEFAULTS.items():
            cfg.setdefault(k, v)
        return cfg
    cfg = dict(_DEFAULTS)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    cfg = _get_config()
    if cfg.get("check_on_startup"):
        try:
            from backend.routers.episodes import check_updates
            from backend.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                result = await check_updates(db=db)
                if result["new_updates"]:
                    print(f"[KuroWatch] Startup: {result['new_updates']} yeni güncelleme bulundu.")
        except Exception as e:
            print(f"[KuroWatch] Startup check-updates hatası: {e}")
    yield


app = FastAPI(title="KuroWatch API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Route'ları ÖNCE ───────────────────────────────────────────────
app.include_router(content.router,  prefix="/api", tags=["content"])
app.include_router(episodes.router, prefix="/api", tags=["episodes"])
app.include_router(sites.router,    prefix="/api", tags=["sites"])
app.include_router(tags.router,     prefix="/api", tags=["tags"])
app.include_router(settings.router, prefix="/api", tags=["settings"])
app.include_router(sync.router,     prefix="/api", tags=["sync"])
app.include_router(download.router, prefix="/api", tags=["download"])
app.include_router(push.router,     prefix="/api", tags=["push"])

# ── Static Files SONRA (catch-all) ───────────────────────────────────
if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="static")
