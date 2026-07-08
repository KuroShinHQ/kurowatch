import asyncio
import os
import re
import time
import json
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

_BUILD_TS = int(time.time())
_VERSIONED_HTML: str | None = None

from backend.database import init_db, seed_content_type_tags
from backend.routers import content, episodes, sites, tags, settings, sync, download, push, analyze, translate, extension, game, game_download, mal_sync, stream, analytics, system

_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
_CONFIG_PATH  = os.path.join(os.path.dirname(__file__), "config.json")
_ROOT = Path(__file__).parent.parent

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
    "tmdb_api_key": "",
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


async def _startup_check_bg():
    """check_on_startup: server hazır olduktan sonra arka planda çalışır, lifespan'i bloklamaz."""
    await asyncio.sleep(3)
    cfg = _get_config()
    if not cfg.get("check_on_startup"):
        return
    try:
        from backend.routers.episodes import check_updates
        from backend.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await check_updates(db=db)
            if result["new_updates"]:
                print(f"[KuroWatch] Startup: {result['new_updates']} yeni güncelleme bulundu.")
    except Exception as e:
        print(f"[KuroWatch] Startup check-updates hatası: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from backend.downloader.manager import load_jobs, scan_downloaded_files
    load_jobs()
    scan_downloaded_files()
    await init_db()
    await seed_content_type_tags()
    asyncio.create_task(_startup_check_bg())
    yield

app = FastAPI(title="KuroWatch API", version="0.1.0", lifespan=lifespan)


# ── Global Exception Handler (v1.0-STABLE) ─────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    print(f"[KuroWatch] UNHANDLED EXCEPTION: {request.method} {request.url.path}")
    traceback.print_exc()
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": f"Beklenmeyen sunucu hatası: {type(exc).__name__}"},
    )


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
app.include_router(analyze.router,   prefix="/api", tags=["analyze"])
app.include_router(translate.router,   prefix="/api", tags=["translate"])
app.include_router(extension.router,  prefix="/api", tags=["extension"])
app.include_router(game.router,       prefix="/api", tags=["game"])
app.include_router(game_download.router, prefix="/api", tags=["game_download"])
app.include_router(mal_sync.router,   prefix="/api", tags=["mal_sync"])
app.include_router(stream.router,     prefix="/api", tags=["stream"])
app.include_router(analytics.router,  prefix="/api", tags=["analytics"])
app.include_router(system.router,    prefix="/api", tags=["system"])

# ── Versioned SPA Index ───────────────────────────────────────────────
def _versioned_html() -> str:
    global _VERSIONED_HTML
    if _VERSIONED_HTML is None:
        raw = (Path(_FRONTEND_DIR) / "index.html").read_text(encoding="utf-8")
        _VERSIONED_HTML = re.sub(
            r'(\.(?:js|css))(\?v=\d+)?"',
            rf'\1?v={_BUILD_TS}"',
            raw,
        )
    return _VERSIONED_HTML


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def spa_index():
    return HTMLResponse(_versioned_html())


# ── Cache-Control Middleware (static assets) ──────────────────────────
_STATIC_CACHE_TYPES = {
    ".js": "public, max-age=31536000, immutable",
    ".css": "public, max-age=31536000, immutable",
    ".png": "public, max-age=86400",
    ".jpg": "public, max-age=86400",
    ".jpeg": "public, max-age=86400",
    ".webp": "public, max-age=86400",
    ".ico": "public, max-age=86400",
    ".svg": "public, max-age=86400",
    ".woff2": "public, max-age=31536000, immutable",
    ".json": "public, max-age=3600",
}


@app.middleware("http")
async def cache_control_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path.startswith("/api/"):
        return response
    _, ext = os.path.splitext(request.url.path)
    if ext in _STATIC_CACHE_TYPES:
        response.headers["Cache-Control"] = _STATIC_CACHE_TYPES[ext]
    return response


# ── Static Files SONRA (catch-all) ───────────────────────────────────
_covers_dir = _ROOT / "covers"
_covers_dir.mkdir(exist_ok=True)
app.mount("/covers", StaticFiles(directory=str(_covers_dir)), name="covers")

if os.path.isdir(_FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="static")
