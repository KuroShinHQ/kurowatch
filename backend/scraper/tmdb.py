"""
TMDB (The Movie Database) API wrapper.
Search + metadata for movies and TV series.
"""
from typing import Optional
import httpx

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p"


async def _get(api_key: str, path: str, params: dict = None) -> Optional[dict]:
    if not api_key:
        return None
    p = {"api_key": api_key, "language": "tr-TR"}
    if params:
        p.update(params)
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            resp = await c.get(BASE_URL + path, params=p)
            if resp.status_code == 200:
                return resp.json()
    except Exception:
        return None
    return None


async def search_movie(query: str, page: int = 1, api_key: str = "") -> list[dict]:
    data = await _get(api_key, "/search/movie", {"query": query, "page": page})
    if not data or "results" not in data:
        return []
    return [_format_movie(r) for r in data["results"]]


async def search_tv(query: str, page: int = 1, api_key: str = "") -> list[dict]:
    data = await _get(api_key, "/search/tv", {"query": query, "page": page})
    if not data or "results" not in data:
        return []
    return [_format_tv(r) for r in data["results"]]


async def get_movie_details(tmdb_id: int, api_key: str = "") -> Optional[dict]:
    data = await _get(api_key, f"/movie/{tmdb_id}", {"append_to_response": "credits"})
    if not data:
        return None
    return _format_movie(data, detail=True)


async def get_tv_details(tv_id: int, api_key: str = "") -> Optional[dict]:
    data = await _get(api_key, f"/tv/{tv_id}", {"append_to_response": "credits"})
    if not data:
        return None
    return _format_tv(data, detail=True)


async def get_tv_season(tv_id: int, season_number: int, api_key: str = "") -> list[dict]:
    data = await _get(api_key, f"/tv/{tv_id}/season/{season_number}")
    if not data or "episodes" not in data:
        return []
    return [
        {
            "episode_number": ep.get("episode_number"),
            "title": ep.get("name"),
            "overview": ep.get("overview"),
            "still_path": IMAGE_BASE + "/w300" + ep["still_path"] if ep.get("still_path") else None,
            "air_date": ep.get("air_date"),
            "runtime": ep.get("runtime"),
        }
        for ep in data["episodes"]
    ]


def _poster(path: Optional[str], size: str = "w500") -> Optional[str]:
    return IMAGE_BASE + "/" + size + path if path else None


def _backdrop(path: Optional[str]) -> Optional[str]:
    return IMAGE_BASE + "/w1280" + path if path else None


def _format_movie(r: dict, detail: bool = False) -> dict:
    return {
        "id": r.get("id"),
        "title": r.get("title") or r.get("original_title", ""),
        "title_tr": r.get("title") or r.get("original_title", ""),
        "type": "movie",
        "cover_url": _poster(r.get("poster_path")),
        "backdrop_url": _backdrop(r.get("backdrop_path")),
        "external_id": f"tmdb:{r.get('id')}",
        "synopsis": r.get("overview"),
        "release_year": _year(r.get("release_date")),
        "genres": [g.get("name") for g in (r.get("genres") or []) if g.get("name")],
        "total_episodes": None,
        "total_chapters": None,
        "runtime_minutes": r.get("runtime") if detail else None,
        "external_score": round((r.get("vote_average") or 0) / 2, 1),
        "external_url": f"https://www.themoviedb.org/movie/{r.get('id')}",
        "cast": _credits(r.get("credits")) if detail else None,
    }


def _format_tv(r: dict, detail: bool = False) -> dict:
    seasons = (r.get("seasons") or []) if detail else r.get("season_count", [])
    total_eps = None
    if detail and seasons:
        total_eps = sum(s.get("episode_count", 0) for s in seasons if s.get("season_number", 0) > 0)
    return {
        "id": r.get("id"),
        "title": r.get("name") or r.get("original_name", ""),
        "title_tr": r.get("name") or r.get("original_name", ""),
        "type": "series",
        "cover_url": _poster(r.get("poster_path")),
        "backdrop_url": _backdrop(r.get("backdrop_path")),
        "external_id": f"tmdb:{r.get('id')}",
        "synopsis": r.get("overview"),
        "release_year": _year(r.get("first_air_date")),
        "genres": [g.get("name") for g in (r.get("genres") or []) if g.get("name")],
        "total_episodes": total_eps,
        "total_chapters": None,
        "runtime_minutes": r.get("episode_run_time", [None])[0] if detail else None,
        "external_score": round((r.get("vote_average") or 0) / 2, 1),
        "external_url": f"https://www.themoviedb.org/tv/{r.get('id')}",
        "seasons": [
            {
                "season_number": s.get("season_number"),
                "episode_count": s.get("episode_count"),
                "poster": _poster(s.get("poster_path"), "w200"),
                "air_date": s.get("air_date"),
            }
            for s in (r.get("seasons") or []) if s.get("season_number", 0) > 0
        ] if detail else None,
        "cast": _credits(r.get("credits")) if detail else None,
    }


def _year(date_str: Optional[str]) -> Optional[int]:
    if date_str and len(date_str) >= 4:
        try:
            return int(date_str[:4])
        except ValueError:
            return None
    return None


def _credits(credits: Optional[dict]) -> list[dict]:
    if not credits:
        return None
    cast = credits.get("cast") or []
    return [
        {
            "name": c.get("name"),
            "character": c.get("character"),
            "profile_path": _poster(c.get("profile_path"), "w185"),
            "order": c.get("order", 0),
        }
        for c in cast[:20]
    ] or None


async def search_all(query: str, type: str, page: int = 1, api_key: str = "") -> list[dict]:
    if type == "movie":
        return await search_movie(query, page, api_key)
    elif type == "series":
        return await search_tv(query, page, api_key)
    return []
