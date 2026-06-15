import time
from datetime import datetime, timezone

import httpx

_TOKEN_URL = "https://id.twitch.tv/oauth2/token"
_IGDB_URL  = "https://api.igdb.com/v4"

_cached_token: str = ""
_token_expires: float = 0.0


async def _get_token(client_id: str, client_secret: str) -> str:
    global _cached_token, _token_expires
    if _cached_token and time.time() < _token_expires - 60:
        return _cached_token
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(
            _TOKEN_URL,
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
        )
        r.raise_for_status()
        data = r.json()
    _cached_token = data["access_token"]
    _token_expires = time.time() + data.get("expires_in", 3600)
    return _cached_token


async def _igdb_post(endpoint: str, body: str, client_id: str, token: str) -> list:
    async with httpx.AsyncClient(timeout=12.0) as client:
        r = await client.post(
            f"{_IGDB_URL}/{endpoint}",
            content=body,
            headers={
                "Client-ID": client_id,
                "Authorization": f"Bearer {token}",
                "Content-Type": "text/plain",
            },
        )
        r.raise_for_status()
        return r.json()


async def search(q: str, client_id: str, client_secret: str, page: int = 1) -> list[dict]:
    if not client_id or not client_secret:
        return []
    try:
        token = await _get_token(client_id, client_secret)
        offset = (page - 1) * 12
        body = (
            f'search "{q}"; '
            f'fields id,name,cover.image_id,genres.name,first_release_date,'
            f'total_rating,total_rating_count,summary,platforms.abbreviation,status; '
            f'where version_parent = null; '
            f'limit 12; offset {offset};'
        )
        games = await _igdb_post("games", body, client_id, token)
        return [_format(g) for g in games]
    except Exception:
        return []


async def get_detail(game_id: str, client_id: str, client_secret: str) -> dict | None:
    if not client_id or not client_secret:
        return None
    try:
        token = await _get_token(client_id, client_secret)
        body = (
            f'where id = {game_id}; '
            f'fields id,name,cover.image_id,genres.name,first_release_date,'
            f'total_rating,total_rating_count,summary,platforms.abbreviation,status,dlcs.name; '
            f'limit 1;'
        )
        games = await _igdb_post("games", body, client_id, token)
        return _format(games[0]) if games else None
    except Exception:
        return None


def _format(g: dict) -> dict:
    image_id = (g.get("cover") or {}).get("image_id") or ""
    cover_url = (
        f"https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg"
        if image_id else None
    )

    genres = [genre["name"] for genre in (g.get("genres") or []) if "name" in genre]
    platforms = [p.get("abbreviation", "") for p in (g.get("platforms") or [])]

    release_ts = g.get("first_release_date")
    year = datetime.fromtimestamp(release_ts, tz=timezone.utc).year if release_ts else None

    # IGDB status: 0=released, 2=alpha, 3=beta, 4=early_access, 6=cancelled, 7=rumored
    status_map = {0: "FINISHED", 2: "RELEASING", 3: "RELEASING", 4: "RELEASING", 6: "CANCELLED"}
    igdb_status = g.get("status", 0)

    raw_rating = g.get("total_rating")
    score = round(raw_rating) if raw_rating else None  # IGDB 0-100 → keep as-is

    return {
        "external_id": str(g["id"]),
        "title": g.get("name", ""),
        "type": "game",
        "cover_url": cover_url,
        "total_episodes": None,
        "total_chapters": None,
        "status": status_map.get(igdb_status, "FINISHED"),
        "genres": genres,
        "year": year,
        "score": score,
        "streaming_episodes": [],
        "synopsis": g.get("summary") or "",
        "next_airing_episode": None,
        "platforms": platforms,
    }
