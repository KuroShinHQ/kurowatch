import httpx

_BASE = "https://api.myanimelist.net/v2"

_ANIME_FIELDS = "id,title,main_picture,num_episodes,status,genres,mean,media_type,start_date"
_MANGA_FIELDS = "id,title,main_picture,num_chapters,status,genres,mean,media_type,start_date"

_STATUS_MAP = {
    "finished_airing":     "FINISHED",
    "currently_airing":    "RELEASING",
    "not_yet_aired":       "NOT_YET_RELEASED",
    "finished":            "FINISHED",
    "currently_publishing":"RELEASING",
    "not_yet_published":   "NOT_YET_RELEASED",
    "on_hiatus":           "HIATUS",
    "discontinued":        "CANCELLED",
}


async def search(q: str, content_type: str, client_id: str, page: int = 1) -> list[dict]:
    if not client_id or not q:
        return []
    endpoint = "anime" if content_type == "anime" else "manga"
    fields = _ANIME_FIELDS if content_type == "anime" else _MANGA_FIELDS
    offset = (page - 1) * 12
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{_BASE}/{endpoint}",
                params={"q": q, "limit": 12, "offset": offset, "fields": fields},
                headers={"X-MAL-Client-ID": client_id},
            )
            r.raise_for_status()
            data = r.json()
        return [_format(item["node"], content_type) for item in data.get("data", [])]
    except Exception:
        return []


async def get_detail(mal_id: str, content_type: str, client_id: str) -> dict | None:
    if not client_id:
        return None
    endpoint = "anime" if content_type == "anime" else "manga"
    fields = _ANIME_FIELDS if content_type == "anime" else _MANGA_FIELDS
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                f"{_BASE}/{endpoint}/{mal_id}",
                params={"fields": fields},
                headers={"X-MAL-Client-ID": client_id},
            )
            r.raise_for_status()
            data = r.json()
        return _format(data, content_type)
    except Exception:
        return None


async def get_chapter_count(mal_id: str, content_type: str, client_id: str) -> int | None:
    detail = await get_detail(mal_id, content_type, client_id)
    if not detail:
        return None
    return detail.get("total_chapters") or detail.get("total_episodes")


def _format(node: dict, content_type: str) -> dict:
    pic = node.get("main_picture") or {}
    cover_url = pic.get("large") or pic.get("medium")

    genres = [g["name"] for g in (node.get("genres") or [])]

    start_date = node.get("start_date") or ""
    year = int(start_date[:4]) if len(start_date) >= 4 else None

    mean = node.get("mean")
    # MAL 0-10 → ×10 to match AniList 0-100 scale
    score = round(mean * 10) if mean else None

    return {
        "external_id": f"mal:{node['id']}",
        "title": node.get("title") or "",
        "type": content_type,
        "cover_url": cover_url,
        "total_episodes": node.get("num_episodes"),
        "total_chapters": node.get("num_chapters"),
        "status": _STATUS_MAP.get(node.get("status", ""), ""),
        "genres": genres,
        "year": year,
        "score": score,
        "streaming_episodes": [],
        "synopsis": "",
        "next_airing_episode": None,
    }
