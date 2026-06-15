"""
FAZ-7c: MAL OAuth2 PKCE Sync.
GET    /api/sync/mal/auth       → PKCE auth URL döner
GET    /api/sync/mal/callback   → code → token, config'e yaz
GET    /api/sync/mal/status     → bağlı mı? username?
POST   /api/sync/mal/import     → MAL listesi → KuroWatch DB
DELETE /api/sync/mal/disconnect → token temizle
"""
import base64, hashlib, json, os, secrets, time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from backend.config import get_config, _CONFIG_PATH
from backend.database import get_db
from backend.models import Content

router = APIRouter()

_MAL_AUTH  = "https://myanimelist.net/v1/oauth2/authorize"
_MAL_TOKEN = "https://myanimelist.net/v1/oauth2/token"
_MAL_API   = "https://api.myanimelist.net/v2"
_REDIRECT  = "http://localhost:8099/api/sync/mal/callback"

_verifier: Optional[str] = None


def _save_cfg(cfg: dict) -> None:
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


@router.get("/sync/mal/auth")
async def mal_auth():
    global _verifier
    cfg = get_config()
    client_id = cfg.get("mal_client_id", "")
    if not client_id:
        raise HTTPException(400, "MAL Client ID ayarlanmamış (Settings > API > MAL Client ID)")

    _verifier = base64.urlsafe_b64encode(secrets.token_bytes(40)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    url = (
        f"{_MAL_AUTH}?response_type=code&client_id={client_id}"
        f"&redirect_uri={_REDIRECT}&code_challenge={challenge}"
        f"&code_challenge_method=S256&state=kurowatch"
    )
    return {"auth_url": url}


@router.get("/sync/mal/callback")
async def mal_callback(code: str = Query(...)):
    global _verifier
    if not _verifier:
        return HTMLResponse("<h2>Oturum süresi doldu. KuroWatch ayarlar sayfasından tekrar deneyin.</h2>", 400)

    cfg = get_config()
    client_id = cfg.get("mal_client_id", "")
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(_MAL_TOKEN, data={
                "client_id": client_id,
                "code": code,
                "code_verifier": _verifier,
                "grant_type": "authorization_code",
                "redirect_uri": _REDIRECT,
            })
            r.raise_for_status()
            token = r.json()
    except Exception as e:
        return HTMLResponse(f"<h2>Token alınamadı: {e}</h2>", 500)

    _verifier = None
    cfg["mal_access_token"]     = token.get("access_token", "")
    cfg["mal_refresh_token"]    = token.get("refresh_token", "")
    cfg["mal_token_expires_at"] = time.time() + token.get("expires_in", 3600)
    _save_cfg(cfg)
    return HTMLResponse(
        "<script>window.opener && window.opener.postMessage('mal_connected','*'); window.close();</script>"
        "<p>MAL bağlandı! Bu pencereyi kapatabilirsiniz.</p>"
    )


@router.get("/sync/mal/status")
async def mal_status():
    cfg = get_config()
    token = cfg.get("mal_access_token", "")
    if not token:
        return {"connected": False}
    try:
        async with httpx.AsyncClient(timeout=8.0) as c:
            r = await c.get(f"{_MAL_API}/users/@me", headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 401:
            return {"connected": False, "reason": "token_expired"}
        u = r.json()
        return {"connected": True, "username": u.get("name"), "picture": u.get("picture")}
    except Exception:
        return {"connected": False}


@router.post("/sync/mal/import")
async def mal_import(db: AsyncSession = Depends(get_db)):
    cfg = get_config()
    token = cfg.get("mal_access_token", "")
    if not token:
        raise HTTPException(401, "MAL bağlı değil. Önce bağlan.")

    created = updated = 0
    _STATUS = {
        "watching": "watching", "reading": "watching",
        "completed": "completed", "on_hold": "on_hold",
        "dropped": "dropped", "plan_to_watch": "planning", "plan_to_read": "planning",
    }

    for ctype, endpoint, fields in (
        ("anime", "animelist", "id,title,main_picture,num_episodes,my_list_status"),
        ("manga", "mangalist", "id,title,main_picture,num_chapters,my_list_status"),
    ):
        offset = 0
        while True:
            try:
                async with httpx.AsyncClient(timeout=15.0) as c:
                    r = await c.get(
                        f"{_MAL_API}/users/@me/{endpoint}",
                        params={"fields": fields, "limit": 100, "offset": offset},
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    r.raise_for_status()
                    data = r.json()
            except Exception:
                break

            for item in data.get("data", []):
                node = item["node"]
                my_status = (item.get("list_status") or {}).get("status", "plan_to_watch")
                kw_status = _STATUS.get(my_status, "planning")

                pic = node.get("main_picture") or {}
                cover = pic.get("large") or pic.get("medium")
                ext_id = f"mal:{node['id']}"

                res = await db.execute(select(Content).where(Content.external_id == ext_id))
                existing = res.scalar_one_or_none()
                if existing:
                    if cover: existing.cover_url = cover
                    updated += 1
                else:
                    db.add(Content(
                        title=node.get("title", ""),
                        type=ctype,
                        status=kw_status,
                        cover_url=cover,
                        external_id=ext_id,
                        total_episodes=node.get("num_episodes"),
                        total_chapters=node.get("num_chapters"),
                        my_progress=0,
                    ))
                    created += 1

            if not data.get("paging", {}).get("next"):
                break
            offset += 100

    await db.commit()
    return {"ok": True, "created": created, "updated": updated}


@router.delete("/sync/mal/disconnect")
async def mal_disconnect():
    cfg = get_config()
    for k in ("mal_access_token", "mal_refresh_token", "mal_token_expires_at"):
        cfg.pop(k, None)
    _save_cfg(cfg)
    return {"ok": True}
