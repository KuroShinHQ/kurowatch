import asyncio
import os
import re
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx

_MADARA_DOMAINS = [
    # 22 Haz 2026 — gerçek chapter testi ile onaylanan siteler
    "mangawow.com", "mangawow.org",
    "hayalistic.com.tr",
    "ragnarscans.com", "ragnarscans.net",
    "merlintoon.com",
    "mangadenizi.com",
    # Eski (şimdilik 403/offline — fallback için kodda kalır)
    "manga-sehri.net", "mangakeyf.com", "mangahost.net",
    "okumangatr.com", "turkmanga.net", "mangaturk.org",
    "ruyamanga.com", "ruyamanga.net", "asurascans.com.tr",
]

# CF turnstile veya kalıcı blok olan siteler — gallery-dl da geçemez
_CF_BLOCKED = {"mangasehri.net", "mangasehri.com"}

# uzaymanga.com eski URL pattern: /manga/{num}/{slug}/{manga_id}/{ch}-bolum
_UZAY_OLD_RE = re.compile(r"/manga/\d+/([^/]+)/\d+/(\d+)-bolum")
# uzaymanga.com yeni format chapter URL ve CDN pattern
_UZAY_CDN_RE = re.compile(r"cdn-u\.efsaneler\d+\.can\.re/_manga/\d+/\d+/[^\s\"'<>]+")

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

    host = urlparse(url).netloc.lstrip("www.")

    # CF turnstile ile kalıcı bloklu siteler
    if any(host.endswith(d) for d in _CF_BLOCKED):
        raise RuntimeError(
            f"Bu site Cloudflare koruması altında, indirme yapılamıyor: {host}\n"
            "Çözüm: Bölüm URL'sini çalışan bir kaynakla güncelle (mangawow.org vb.)"
        )

    if "mangadex.org" in url:
        return await _mangadex_chapter(url, output_dir, on_progress)
    elif host.endswith("uzaymanga.com"):
        return await _uzaymanga_chapter(url, output_dir, on_progress)
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

    # Madara standart sınıf yok ama sayfa yüklenmiş olabilir — hemen hata atma

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


async def _uzaymanga_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    """uzaymanga.com chapter indir. Eski URL formatını otomatik yeni formata çevirir."""
    fetch_url = url

    # Eski format: /manga/{num}/{slug}/{id}/{ch}-bolum → yeni: /manga/{slug}/{ch}-bolum-oku
    m = _UZAY_OLD_RE.search(url)
    if m:
        slug, ch_num = m.group(1), m.group(2)
        fetch_url = f"https://uzaymanga.com/manga/{slug}/{ch_num}-bolum-oku"

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=_HEADERS) as client:
        r = await client.get(fetch_url)
        if r.status_code == 404 and m:
            raise RuntimeError(
                f"uzaymanga.com URL 404: '{fetch_url}'\n"
                f"Bu manga uzaymanga.com'dan kaldırılmış olabilir. "
                f"Bölüm URL'sini çalışan bir kaynakla güncelle."
            )
        r.raise_for_status()
        html = r.text

    # CDN image URL'lerini çıkar: cdn-u.efsanelerN.can.re/_manga/{id}/{ch}/{page}.avif
    cdn_urls = _UZAY_CDN_RE.findall(html)
    if not cdn_urls:
        raise RuntimeError(f"uzaymanga.com: chapter görselleri bulunamadı — {fetch_url}")

    # Tekrarları kaldır, sırala
    seen: set[str] = set()
    img_urls: list[str] = []
    for u in cdn_urls:
        full = "https://" + u
        if full not in seen:
            seen.add(full)
            img_urls.append(full)

    total = len(img_urls)
    files: list[str] = []
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        for i, img_url in enumerate(img_urls):
            ext = os.path.splitext(img_url.split("?")[0])[1] or ".avif"
            dest = os.path.join(output_dir, f"{i + 1:04d}{ext}")
            img_r = await client.get(img_url)
            img_r.raise_for_status()
            with open(dest, "wb") as fh:
                fh.write(img_r.content)
            files.append(dest)
            if on_progress:
                on_progress(i + 1, total)

    if not files:
        raise RuntimeError(f"uzaymanga.com: hiç sayfa indirilemedi — {fetch_url}")
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
