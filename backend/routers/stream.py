import asyncio
import logging
import os
import re
import time
from typing import Optional
from urllib.parse import urlencode, urlparse, urlunparse, quote

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

logger = logging.getLogger("kurowatch.stream")

router = APIRouter()

_STREAM_TIMEOUT = 30.0
_MAX_REDIRECTS = 5
_CHUNK_SIZE = 256 * 1024

_REFERER_MAP = {
    "spidypro.com": "https://dizigom.love/",
    "rapidvid.net": "https://www.fullhdfilmizlesene.life/",
    "rapidvid":     "https://www.fullhdfilmizlesene.life/",
}

_PROXY_CACHE: dict[str, tuple[str, float]] = {}


def _get_referer(url: str) -> str:
    for domain, ref in _REFERER_MAP.items():
        if domain in url:
            return ref
    return ""


def _rewrite_hls_playlist(content: str, base_url: str) -> str:
    parsed_base = urlparse(base_url)
    base_origin = f"{parsed_base.scheme}://{parsed_base.netloc}"
    base_dir = base_origin + "/".join(parsed_base.path.rsplit("/", 1)[0]) + "/" if "/" in parsed_base.path else base_origin + "/"

    def _abs(url_str: str) -> str:
        if url_str.startswith("http"):
            return url_str
        if url_str.startswith("/"):
            return base_origin + url_str
        return base_dir + url_str

    lines = content.split("\n")
    out = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
        else:
            abs_url = _abs(stripped)
            proxied = f"/api/stream/proxy?url={quote(abs_url, safe='')}"
            out.append(proxied)
    return "\n".join(out)


async def _proxy_content(url: str, req_headers: dict) -> StreamingResponse:
    fetch_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    range_h = req_headers.get("range")
    if range_h:
        fetch_headers["Range"] = range_h
    referer = _get_referer(url)
    if referer:
        fetch_headers["Referer"] = referer

    async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=fetch_headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Proxy hatasi: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Proxy baglanti hatasi: {e}")

        content_type = resp.headers.get("content-type", "video/mp4")
        resp_headers = {
            "Accept-Ranges": resp.headers.get("accept-ranges", "bytes"),
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        }
        cl = resp.headers.get("content-length")
        if cl:
            resp_headers["Content-Length"] = cl

        return StreamingResponse(
            content=resp.aiter_bytes(),
            media_type=content_type,
            headers=resp_headers,
        )


@router.get("/stream/url")
async def get_stream_url(
    content_id: int = Query(...),
    episode_number: int = Query(...),
    url: str = Query(...),
):
    """find_stream_url calistir, video + subtitle URL'sini dondur."""
    from backend.downloader.stream_finder import find_stream_url
    video_url = await find_stream_url(url)
    if not video_url:
        video_url = url

    is_m3u8 = ".m3u8" in video_url.lower()
    if is_m3u8:
        proxy_url = f"/api/stream/hls?url={quote(video_url, safe='')}"
    else:
        proxy_url = f"/api/stream/proxy?url={quote(video_url, safe='')}"

    subtitle_url = None
    return {
        "ok": True,
        "video_url": video_url,
        "proxy_url": proxy_url,
        "is_hls": is_m3u8,
        "subtitle_url": subtitle_url,
    }


@router.get("/stream/proxy")
async def stream_proxy(url: str = Query(...), request: Request = None):
    headers = {}
    if request:
        headers = dict(request.headers)
    return await _proxy_content(url, headers)


@router.get("/stream/hls")
async def stream_hls_playlist(url: str = Query(...)):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    referer = _get_referer(url)
    if referer:
        headers["Referer"] = referer

    async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"HLS hatasi: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"HLS baglanti hatasi: {e}")

        base_url = str(resp.url)
        rewritten = _rewrite_hls_playlist(resp.text, base_url)

        return Response(
            content=rewritten,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )


@router.get("/stream/subtitle")
async def stream_subtitle(url: str = Query(...)):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    referer = _get_referer(url)
    if referer:
        headers["Referer"] = referer

    async with httpx.AsyncClient(timeout=_STREAM_TIMEOUT, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Subtitle hatasi: {e}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Subtitle baglanti hatasi: {e}")

        return Response(
            content=resp.content,
            media_type="text/vtt; charset=utf-8",
            headers={
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-cache",
            },
        )
