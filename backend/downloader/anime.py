import asyncio
import os
import re
from typing import Callable, Coroutine, Optional
from urllib.parse import urlparse

from backend.downloader.stream_finder import find_stream_url, get_yt_dlp_cookies_arg, get_session_header_args


async def download_anime(
    url: str,
    output_path: str,
    quality: str = "720p",
    on_progress: Optional[Callable] = None,
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

    # Playwright'ın MP4 isteğindeki header'lar (CF cookie dahil, alucard.click vb.)
    session_header_args = get_session_header_args(actual_url)

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
        *session_header_args,
        "-o", output_path + ".%(ext)s",
        actual_url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    last_pct = 0
    output_lines: list[str] = []
    # yt-dlp \r (in-place) veya \n kullanır; chunk okuyarak ikisini de yakala
    _buf = b""
    while True:
        chunk = await proc.stdout.read(4096)
        if not chunk:
            break
        _buf += chunk
        parts = re.split(b"[\r\n]+", _buf)
        _buf = parts[-1]  # son yarım satır bir sonraki chunk'a taşı
        for raw in parts[:-1]:
            line = raw.decode("utf-8", errors="ignore").strip()
            if line:
                output_lines.append(line)
            m = re.search(r"(\d+\.?\d*)%", line)
            if m and on_progress:
                pct = min(99, int(float(m.group(1))))
                if pct != last_pct:
                    last_pct = pct
                    await on_progress(pct)
    # Kalan buffer'ı işle
    if _buf:
        line = _buf.decode("utf-8", errors="ignore").strip()
        if line:
            output_lines.append(line)

    await proc.wait()
    if proc.returncode != 0:
        err_tail = " | ".join(output_lines[-3:]) if output_lines else ""
        err_lower = err_tail.lower()
        if "crunchyroll" in err_lower or "?su=" in err_tail or "vrv.co" in err_lower:
            raise RuntimeError(
                "Bu bölüm Crunchyroll'a yönlendiriyor. "
                "İndirmek için Ayarlar → Cookies bölümünden Crunchyroll cookies ekleyin."
            )
        # [generic] = embed oynatıcısı yt-dlp tarafından desteklenmiyor
        if "[generic]" in err_tail:
            domain = urlparse(url).netloc
            raise RuntimeError(
                f"{domain} sitesinde video embed bulunamadı veya desteklenmiyor. "
                "Bu site için cookies ekleyin (Ayarlar → Cookies) veya farklı bir site kullanın."
            )
        raise RuntimeError(f"yt-dlp çıkış kodu {proc.returncode}" + (f": {err_tail}" if err_tail else ""))

    # Uzantı yt-dlp tarafından eklendi — bul
    for ext in ("mp4", "mkv", "webm", "avi"):
        p = f"{output_path}.{ext}"
        if os.path.exists(p):
            if on_progress:
                await on_progress(100)
            return p

    raise RuntimeError(f"Çıktı dosyası bulunamadı: {output_path}.*")
