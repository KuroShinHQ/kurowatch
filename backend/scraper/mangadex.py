import httpx

BASE = "https://api.mangadex.org"

_CONTENT_RATINGS = ["safe", "suggestive", "erotica", "pornographic"]


async def search(q: str, content_type: str, page: int = 1) -> list[dict]:
    offset = (page - 1) * 12
    params: dict = {
        "title": q,
        "limit": 12,
        "offset": offset,
        "includes[]": "cover_art",
        "order[relevance]": "desc",
        "contentRating[]": _CONTENT_RATINGS,
    }
    if content_type == "manhwa":
        params["originalLanguage[]"] = "ko"
    elif content_type == "manga":
        params["originalLanguage[]"] = "ja"

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(f"{BASE}/manga", params=params)
            r.raise_for_status()
            data = r.json()
        return [_format(m) for m in data.get("data", [])]
    except Exception:
        return []


async def get_detail(mdx_id: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{BASE}/manga/{mdx_id}",
                params={"includes[]": "cover_art"},
            )
            r.raise_for_status()
            data = r.json()
        return _format(data["data"])
    except Exception:
        return None


async def get_chapter_count(mdx_id: str) -> int | None:
    """En yüksek chapter numarasını döndürür (İngilizce veya raw)."""
    for lang in (["en"], _CONTENT_RATINGS):
        try:
            params: dict = {
                "manga": mdx_id,
                "limit": 1,
                "order[chapter]": "desc",
                "contentRating[]": _CONTENT_RATINGS,
            }
            if lang != _CONTENT_RATINGS:
                params["translatedLanguage[]"] = lang
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.get(f"{BASE}/chapter", params=params)
                r.raise_for_status()
                data = r.json()
            items = data.get("data", [])
            if items:
                ch = items[0]["attributes"].get("chapter")
                if ch:
                    return int(float(ch))
        except Exception:
            pass
    return None


def _format(m: dict) -> dict:
    attrs = m.get("attributes", {})
    title_dict = attrs.get("title", {}) or {}
    title = (
        title_dict.get("en")
        or title_dict.get("ja-ro")
        or next(iter(title_dict.values()), "")
    )

    cover_url = None
    for rel in m.get("relationships", []):
        if rel["type"] == "cover_art":
            fn = (rel.get("attributes") or {}).get("fileName")
            if fn:
                cover_url = f"https://uploads.mangadex.org/covers/{m['id']}/{fn}.256.jpg"
            break

    orig_lang = attrs.get("originalLanguage", "")
    ctype = "manhwa" if orig_lang == "ko" else "manga"

    last_ch = attrs.get("lastChapter")
    total_chapters = int(float(last_ch)) if last_ch and last_ch not in ("", "0") else None

    tags = []
    for tag in attrs.get("tags", []):
        name = (tag.get("attributes") or {}).get("name", {}).get("en")
        if name:
            tags.append(name)

    status_map = {
        "ongoing": "RELEASING",
        "completed": "FINISHED",
        "hiatus": "HIATUS",
        "cancelled": "CANCELLED",
    }

    desc = (attrs.get("description") or {}).get("en") or ""

    return {
        "external_id": f"mdx:{m['id']}",
        "title": title,
        "type": ctype,
        "cover_url": cover_url,
        "total_episodes": None,
        "total_chapters": total_chapters,
        "status": status_map.get(attrs.get("status", ""), attrs.get("status", "")),
        "genres": tags,
        "year": attrs.get("year"),
        "score": None,
        "streaming_episodes": [],
        "synopsis": desc,
        "next_airing_episode": None,
    }
