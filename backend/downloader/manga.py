import asyncio
import os
import re
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx

_MADARA_DOMAINS = [
    "mangawow.com", "manga-sehri.net", "mangakeyf.com", "mangahost.net",
    "okumangatr.com", "mangadenizi.com", "turkmanga.net", "mangaturk.org",
]

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}


def _is_madara(url: str) -> bool:
    host = urlparse(url).netloc.lstrip("www.")
    return any(host.endswith(d) for d in _MADARA_DOMAINS)


async def download_manga_chapter(
    url: str,
    output_dir: str,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> list[str]:
    """Manga bölümü indir. Sayfa dosyalarının yol listesini döner."""
    os.makedirs(output_dir, exist_ok=True)

    if "mangadex.org" in url:
        return await _mangadex_chapter(url, output_dir, on_progress)
    elif _is_madara(url):
        return await _madara_chapter(url, output_dir, on_progress)
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


async def _madara_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    """Madara WordPress tema sitelerinden manga bölümü indir (?style=list ile)."""
    list_url = url.rstrip("/") + "/?style=list"

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=_HEADERS) as client:
        r = await client.get(list_url)
        r.raise_for_status()
        html = r.text

    if "reading-content" not in html:
        raise RuntimeError(f"Madara: reading-content bulunamadı — {url}")

    # Önce wp-manga-chapter-img class'lı img'leri dene (Madara standart)
    # src= değerleri bazen " https://..." şeklinde boşlukla başlar — strip() zorunlu
    seen: set[str] = set()
    img_urls: list[str] = []

    chapter_imgs: list[str] = []
    for m in re.finditer(r'<img[^>]+class=["\'][^"\']*wp-manga-chapter-img[^"\']*["\'][^>]*>', html, re.IGNORECASE):
        tag = m.group(0)
        for attr in ("data-src", "data-lazy-src", "src"):
            am = re.search(rf'{attr}=["\']([^"\']*)["\']', tag, re.IGNORECASE)
            if am:
                src = am.group(1).strip()
                if src and src not in seen:
                    seen.add(src)
                    chapter_imgs.append(src)
                break

    if not chapter_imgs:
        # Fallback: tüm HTML'de src/data-src ara (boşluklu URL desteğiyle)
        _SKIP = ("logo", "favicon", "banner", "avatar", "icon", "wp-content/themes",
                 "elementor", "gravatar", "placeholder", "spinner", "loading")
        for m in re.finditer(r'(?:data-src|data-lazy-src|src)=["\']([^"\']*\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.IGNORECASE):
            src = m.group(1).strip()
            if not src or any(s in src.lower() for s in _SKIP):
                continue
            if src not in seen:
                seen.add(src)
                img_urls.append(src)

        chapter_imgs = [u for u in img_urls if re.search(r'/\d{1,4}\.(?:jpg|jpeg|png|webp)', u, re.IGNORECASE)]
        if not chapter_imgs:
            chapter_imgs = [u for u in img_urls if "/manga/" in u.lower() or "/chapter/" in u.lower()]
        if not chapter_imgs:
            chapter_imgs = img_urls

    # URL'leri sırala (001, 002, ... sırasını koru)
    chapter_imgs.sort(key=lambda u: re.search(r'(\d+)\.(?:jpg|jpeg|png|webp)', u).group(1)
                      if re.search(r'(\d+)\.(?:jpg|jpeg|png|webp)', u) else u)

    if not chapter_imgs:
        raise RuntimeError(f"Madara: hiç sayfa görseli bulunamadı — {list_url}")

    total = len(chapter_imgs)
    files: list[str] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        for i, img_url in enumerate(chapter_imgs):
            ext = re.search(r'\.(jpg|jpeg|png|webp)', img_url, re.IGNORECASE)
            ext_str = "." + (ext.group(1).lower() if ext else "jpg")
            dest = os.path.join(output_dir, f"{i + 1:04d}{ext_str}")
            img_r = await client.get(img_url)
            img_r.raise_for_status()
            with open(dest, "wb") as fh:
                fh.write(img_r.content)
            files.append(dest)
            if on_progress:
                on_progress(i + 1, total)

    if not files:
        raise RuntimeError(f"Madara: hiç sayfa indirilemedi — {url}")
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
