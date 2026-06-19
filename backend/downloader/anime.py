import asyncio
import os
import re
from typing import Callable, Optional
from urllib.parse import urlparse

from backend.downloader.stream_finder import find_stream_url, get_yt_dlp_cookies_arg


async def download_anime(
    url: str,
    output_path: str,
    quality: str = "720p",
    on_progress: Optional[Callable[[int], None]] = None,
) -> str:
    """yt-dlp ile anime/video indir. stream_finder ile gerçek URL tespit edilir."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    height = quality.replace("p", "")

    # Gerçek stream URL'sini bul (embed player URL veya orijinal)
    actual_url = await find_stream_url(url)

    cookies_args = get_yt_dlp_cookies_arg(url)

    # Embed URL farklıysa orijinal sitenin domain'ini Referer olarak ekle
    referer_args: list[str] = []
    if actual_url != url:
        parsed = urlparse(url)
        referer = f"{parsed.scheme}://{parsed.netloc}/"
        referer_args = ["--add-header", f"Referer:{referer}"]

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "-f", f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best",
        "--merge-output-format", "mp4",
        "--newline",
        "--no-warnings",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", "tr,tr-TR,en",
        "--convert-subs", "vtt",
        "--sub-format", "vtt",
        *cookies_args,
        *referer_args,
        "-o", output_path + ".%(ext)s",
        actual_url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    last_pct = 0
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="ignore").strip()
        m = re.search(r"(\d+\.?\d*)%", line)
        if m and on_progress:
            pct = min(99, int(float(m.group(1))))
            if pct != last_pct:
                last_pct = pct
                on_progress(pct)

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp çıkış kodu {proc.returncode}")

    # Uzantı yt-dlp tarafından eklendi — bul
    for ext in ("mp4", "mkv", "webm", "avi"):
        p = f"{output_path}.{ext}"
        if os.path.exists(p):
            if on_progress:
                on_progress(100)
            return p

    raise RuntimeError(f"Çıktı dosyası bulunamadı: {output_path}.*")
