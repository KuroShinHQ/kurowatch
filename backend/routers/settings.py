import asyncio
import json
import os
import time
from pathlib import Path
from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
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
    "download_quality_manual": "720p",
    "download_quality_auto": "480p",
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


# ── CAPTCHA Human-in-the-Loop ─────────────────────────────────────────

_CAPTCHA_SITE_URLS = {
    "tranimeizle": "https://tranimeizle.co",
    "turkanime":   "https://turkanime.co",
    "diziwatch":   "https://diziwatch.com",
}


def _cookies_to_netscape(cookies: list) -> str:
    lines = ["# Netscape HTTP Cookie File", "# KuroWatch CAPTCHA capture", ""]
    for c in cookies:
        domain   = c.get("domain", "")
        flag     = "TRUE" if domain.startswith(".") else "FALSE"
        path     = c.get("path", "/")
        secure   = "TRUE" if c.get("secure") else "FALSE"
        expires  = str(int(c.get("expires", 0)))
        name     = c.get("name", "")
        value    = c.get("value", "")
        lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}")
    return "\n".join(lines)


def _sse(status: str, msg: str) -> str:
    payload = json.dumps({"status": status, "msg": msg}, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.get("/settings/cookies/captcha/{site_name}")
async def captcha_browser_launch(site_name: str):
    """
    Playwright headed browser aç → Lord CAPTCHA'ya tıklar →
    cf_clearance cookie'si alınınca kaydet → SSE ile durum bildir.
    """
    site_url = _CAPTCHA_SITE_URLS.get(site_name)
    if not site_url:
        raise HTTPException(400, f"Bilinmeyen site: {site_name}")

    async def generator():
        yield _sse("starting", "Tarayıcı başlatılıyor...")
        try:
            import os as _os
            # WSLg display — X11 soketi varsa DISPLAY=:0 kullan
            if not _os.environ.get("DISPLAY"):
                _os.environ["DISPLAY"] = ":0"

            from playwright.async_api import async_playwright

            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=False,
                    args=["--window-size=1280,800", "--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/131.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                yield _sse("open", f"{site_url} açıldı. CAPTCHA checkbox'ına tıklayın...")
                try:
                    await page.goto(site_url, wait_until="domcontentloaded", timeout=30_000)
                except Exception:
                    pass  # CF challenge sayfasında timeout normaldir

                # cf_clearance cookie'yi bekle (max 5 dakika)
                deadline = time.time() + 300
                ping_at  = time.time() + 10
                found    = False

                while time.time() < deadline:
                    # Canlı tutma ping'i (her 10s)
                    if time.time() >= ping_at:
                        remaining = int(deadline - time.time())
                        yield _sse("waiting", f"Bekleniyor... ({remaining}s kaldı)")
                        ping_at = time.time() + 10

                    cookies = await context.cookies()
                    cf_cookies = [c for c in cookies if c["name"] == "cf_clearance"]

                    if cf_cookies:
                        found = True
                        yield _sse("saving", "CF clearance alındı! Cookie'ler kaydediliyor...")
                        await asyncio.sleep(1)  # Kalan cookie'lerin yerleşmesini bekle
                        cookies = await context.cookies()  # Taze liste

                        _COOKIES_DIR.mkdir(exist_ok=True)
                        fname = f"{site_name}_cookies.txt"
                        dest  = _COOKIES_DIR / fname
                        dest.write_text(_cookies_to_netscape(cookies), encoding="utf-8")

                        await browser.close()
                        yield _sse("done", f"{len(cookies)} cookie {fname} dosyasına kaydedildi. Artık indirme butonu çalışır!")
                        return

                    await asyncio.sleep(2)

                await browser.close()
                if not found:
                    yield _sse("timeout", "5 dakika beklendi ama cf_clearance alınamadı. Tekrar deneyin.")

        except Exception as exc:
            yield _sse("error", str(exc))

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
