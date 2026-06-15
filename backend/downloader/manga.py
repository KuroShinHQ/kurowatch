import asyncio
import os
import re
from typing import Callable, Optional

import httpx


async def download_manga_chapter(
    url: str,
    output_dir: str,
    on_progress: Optional[Callable[[int, int], None]] = None,  # (downloaded, total)
) -> list[str]:
    """Manga bölümü indir. Sayfa dosyalarının yol listesini döner."""
    os.makedirs(output_dir, exist_ok=True)

    if "mangadex.org" in url:
        return await _mangadex_chapter(url, output_dir, on_progress)
    else:
        return await _gallerydl_chapter(url, output_dir, on_progress)


async def _mangadex_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    m = re.search(r"/chapter/([a-f0-9-]{36})", url)
    if not m:
        raise ValueError(f"Geçersiz MangaDex chapter URL: {url}")
    chapter_id = m.group(1)

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"https://api.mangadex.org/at-home/server/{chapter_id}")
        r.raise_for_status()
        data = r.json()

        base_url = data["baseUrl"]
        ch_hash = data["chapter"]["hash"]
        pages = data["chapter"]["data"]
        total = len(pages)

        files: list[str] = []
        for i, page in enumerate(pages):
            img_url = f"{base_url}/data/{ch_hash}/{page}"
            ext = os.path.splitext(page)[1] or ".jpg"
            dest = os.path.join(output_dir, f"{i + 1:04d}{ext}")

            img_r = await client.get(img_url, timeout=60)
            img_r.raise_for_status()
            with open(dest, "wb") as fh:
                fh.write(img_r.content)

            files.append(dest)
            if on_progress:
                on_progress(i + 1, total)

        return files


async def _gallerydl_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    cmd = [
        "gallery-dl",
        "--directory", output_dir,
        "--filename", "{num:>04}.{extension}",
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    count = 0
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="ignore").strip()
        if line.startswith("#") or "Downloading" in line:
            count += 1
            if on_progress:
                on_progress(count, 0)

    await proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"gallery-dl çıkış kodu {proc.returncode}")

    exts = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    files = sorted(
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir)
        if os.path.splitext(f)[1].lower() in exts
    )
    if not files:
        raise RuntimeError(f"gallery-dl hiç dosya indirmedi: {output_dir}")
    return files
