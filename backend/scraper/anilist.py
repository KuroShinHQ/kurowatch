import httpx
import asyncio

ANILIST_URL = "https://graphql.anilist.co"

_SEARCH_QUERY = """
query ($search: String, $type: MediaType, $countryOfOrigin: CountryCode, $genre: String, $page: Int) {
  Page(page: $page, perPage: 12) {
    media(search: $search, type: $type, countryOfOrigin: $countryOfOrigin, genre: $genre, sort: SEARCH_MATCH) {
      id
      title { english romaji }
      type
      format
      episodes
      chapters
      status
      averageScore
      seasonYear
      genres
      countryOfOrigin
      coverImage { large }
    }
  }
}
"""

_DETAIL_QUERY = """
query ($id: Int) {
  Media(id: $id) {
    id
    title { english romaji }
    type
    format
    episodes
    chapters
    status
    averageScore
    seasonYear
    genres
    countryOfOrigin
    coverImage { large }
    description
    nextAiringEpisode { episode airingAt }
    streamingEpisodes { title url thumbnail }
  }
}
"""


async def _post(query: str, variables: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.post(ANILIST_URL, json={"query": query, "variables": variables})
        r.raise_for_status()
        return r.json()


def _media_type(content_type: str) -> tuple[str, str | None]:
    """content type → (AniList MediaType, countryOfOrigin)"""
    if content_type == "anime":
        return "ANIME", None
    if content_type == "manga":
        return "MANGA", "JP"
    if content_type == "manhwa":
        return "MANGA", "KR"
    return "MANGA", None


async def search(q: str | None, content_type: str, page: int = 1, genre: str | None = None) -> list[dict]:
    """AniList arama → liste döndür. q veya genre en az biri gerekli."""
    mtype, country = _media_type(content_type)
    vars_: dict = {"type": mtype, "page": page}
    if q:
        vars_["search"] = q
    if country:
        vars_["countryOfOrigin"] = country
    if genre:
        vars_["genre"] = genre
    try:
        data = await _post(_SEARCH_QUERY, vars_)
        return [_format(m) for m in data["data"]["Page"]["media"]]
    except Exception:
        return []


async def get_detail(external_id: str) -> dict | None:
    """AniList id → güncel bölüm sayısı + kapak"""
    try:
        data = await _post(_DETAIL_QUERY, {"id": int(external_id)})
        m = data["data"]["Media"]
        return _format(m)
    except Exception:
        return None


def _format(m: dict) -> dict:
    title = m["title"].get("english") or m["title"].get("romaji") or ""
    ctype = "anime" if m["type"] == "ANIME" else (
        "manhwa" if m.get("countryOfOrigin") == "KR" else "manga"
    )
    streaming = [
        {"title": se.get("title", ""), "url": se.get("url", ""), "thumbnail": se.get("thumbnail", "")}
        for se in (m.get("streamingEpisodes") or [])
    ]
    nae = m.get("nextAiringEpisode")
    return {
        "external_id": str(m["id"]),
        "title": title,
        "type": ctype,
        "cover_url": (m.get("coverImage") or {}).get("large"),
        "total_episodes": m.get("episodes"),
        "total_chapters": m.get("chapters"),
        "status": m.get("status", ""),
        "genres": m.get("genres", []),
        "year": m.get("seasonYear"),
        "score": m.get("averageScore"),
        "streaming_episodes": streaming,
        "synopsis": m.get("description") or "",
        "next_airing_episode": {"episode": nae["episode"], "airing_at": nae["airingAt"]} if nae else None,
    }
