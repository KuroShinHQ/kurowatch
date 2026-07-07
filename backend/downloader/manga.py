import asyncio
import os
import re
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx

from backend.downloader.integrity import validate_image_file, validate_manga_files
from backend.scraper.tag_extractor import extract_manga_source_tags

_MADARA_DOMAINS = [
    # 5 Tem 2026 — gerçek chapter testi ile onaylanan siteler
    "mangawow.com", "mangawow.org",
    "hayalistic.com.tr",
    "ragnarscans.com", "ragnarscans.net",
    "merlintoon.com",
    "mangadenizi.com",
    "manhwahentai.me",
    # Eski (şimdilik 403/offline — fallback için kodda kalır)
    "manga-sehri.net", "mangakeyf.com", "mangahost.net",
    "okumangatr.com", "turkmanga.net", "mangaturk.org",
    "ruyamanga.com", "ruyamanga.net", "asurascans.com.tr",
]

# CF turnstile siteler — curl_cffi impersonate ile aşılır
_CF_BLOCKED = {
    "ragnarscans.com", "ragnarscans.net",
    "manhwahentai.me",
    "hayalistic.com.tr",
    "mangasehri.net", "mangasehri.com",
}

# Next.js App Router siteler — RSC payload'dan CDN görsel URL'leri çekilir
# Tarayıcı gerekmez, tek httpx GET + regex yeterli
_NEXTJS_DOMAINS = {
    "monomanga.com.tr",
}

# DNS fail / offline siteler — anında hata döndür
# 5 Tem 2026: mangagezgini.com HTTP 525 SSL handshake failed
_OFFLINE = {
    "majorscans.com", "majorscans.net", "mangatr.net", "mangaokutr.com",
    "mangagezgini.com",
    "mangagezgini.com",  # HTTP 525 SSL handshake failed (5 Tem 2026)
}

# uzaymanga.com eski URL pattern: /manga/{num}/{slug}/{manga_id}/{ch}-bolum
_UZAY_OLD_RE = re.compile(r"/manga/\d+/([^/]+)/\d+/(\d+)-bolum")
# uzaymanga.com yeni format chapter URL ve CDN pattern
_UZAY_CDN_RE = re.compile(r"cdn-u\.efsaneler\d+\.can\.re/_manga/\d+/\d+/[^\s\"'<>]+")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}


def _image_headers(referer: str) -> dict[str, str]:
    headers = dict(_HEADERS)
    headers.update({
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": referer,
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    })
    return headers


_LAZY_ATTRS = ("data-src", "data-lazy-src", "data-lazy", "data-original", "data-cfsrc", "src")

_READING_SECTION_RE = re.compile(
    r'<div[^>]*(?:class|id)\s*=\s*["\'][^"\']*(?:reading-content|page-break|vung-doc|read-container|chapter-content)[^"\']*["\'][^>]*>',
    re.IGNORECASE
)

_READING_END_RE = re.compile(
    r'<(?:div|section|footer|nav)[^>]*(?:class|id)\s*=\s*["\'][^"\']*(?:comments?|site-footer|footer|sidebar|navigation|nav-below|chapter-nav|disqus|responsive-nav)[^"\']*["\']',
    re.IGNORECASE
)

_SKIP_PATTERNS = (
    "logo", "favicon", "banner", "avatar", "icon", "wp-content/themes",
    "elementor", "gravatar", "placeholder", "spinner", "loading",
    "emoji", "rating", "star", "button", "social", "/ads/", "advert",
    "doubleclick", "googlesyndication", "adservice", "adsense",
    "sidebar", "header", "footer", "menu", "search", "comment",
    "blank", "transparent", "1x1", "thumb",
    "wp-includes", "captcha", "badge", "ribbon", "arrow", "close",
    "admin-bar", "sprite", "currency", "flag",
)

_PAGE_URL_HINTS = (
    "/manga/", "/chapter/", "/chapters/", "/uploads/", "/webtoon/",
    "/wp-content/uploads/", "/reader/", "/content/", "/series/",
    "/ch_", "/pages/", "/bolumler/", "/bolum/",
)


def _extract_reading_section(html: str) -> str:
    m = _READING_SECTION_RE.search(html)
    if not m:
        return ""
    start = m.start()
    section = html[start:]
    end_m = _READING_END_RE.search(section)
    if end_m and end_m.start() > 200:
        section = section[:end_m.start()]
    return section


def _extract_img_urls_from_section(section: str, seen: set) -> list:
    urls: list[str] = []
    for m in re.finditer(r'<img[^>]*>', section, re.IGNORECASE):
        tag = m.group(0)
        if re.search(r'class\s*=\s*["\'][^"\']*(?:placeholder|avatar|logo|icon|emoji|rating|button|sidebar|header|footer|menu|social|ad-)[^"\']*["\']', tag, re.IGNORECASE):
            continue
        for attr in _LAZY_ATTRS:
            am = re.search(rf'{attr}\s*=\s*["\']([^"\']*)["\']', tag, re.IGNORECASE)
            if am:
                src = am.group(1).strip()
                if src.startswith("//"):
                    src = "https:" + src
                if not src or not src.startswith("http"):
                    continue
                if any(s in src.lower() for s in _SKIP_PATTERNS):
                    break
                if src not in seen:
                    seen.add(src)
                    urls.append(src)
                break
    return urls


def _save_image_response(resp: httpx.Response, dest: str, img_url: str) -> None:
    resp.raise_for_status()
    content_type = (resp.headers.get("content-type") or "").lower()
    if "text/html" in content_type or "application/json" in content_type:
        raise RuntimeError(f"Görsel yerine {content_type or 'bilinmeyen'} döndü: {img_url}")
    if not resp.content:
        raise RuntimeError(f"Boş görsel cevabı: {img_url}")
    with open(dest, "wb") as fh:
        fh.write(resp.content)
    try:
        validate_image_file(dest)
    except Exception:
        try:
            os.remove(dest)
        except OSError:
            pass
        raise


def _is_madara(url: str) -> bool:
    host = urlparse(url).netloc.lstrip("www.")
    return any(host.endswith(d) for d in _MADARA_DOMAINS)


async def download_manga_chapter(
    url: str,
    output_dir: str,
    on_progress: Optional[Callable] = None,
) -> list[str]:
    """Manga bölümü indir. Sayfa dosyalarının yol listesini döner."""
    os.makedirs(output_dir, exist_ok=True)

    host = urlparse(url).netloc.lstrip("www.")

    # Offline / DNS fail siteler
    if any(host.endswith(d) for d in _OFFLINE):
        raise RuntimeError(
            f"Bu site erişilemez durumda (offline/DNS fail): {host}\n"
            "Çözüm: Bölüm URL'sini çalışan bir kaynakla güncelle."
        )

    if "mangadex.org" in url:
        return await _mangadex_chapter(url, output_dir, on_progress)
    elif any(host.endswith(d) for d in _NEXTJS_DOMAINS):
        return await _nextjs_chapter(url, output_dir, on_progress)
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

            img_r = await client.get(img_url, timeout=60, headers=_image_headers(url))
            _save_image_response(img_r, dest, img_url)

            files.append(dest)
            if on_progress:
                await on_progress(i + 1, total)

        validate_manga_files(files)
        return files


async def _nextjs_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    """Next.js App Router siteler (monomanga.com.tr) — RSC payload'dan CDN URL çıkar."""
    import httpx

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise RuntimeError(f"NextJS: HTTP {resp.status_code} — {url}")
        html = resp.text

    # RSC payload'larını çıkar: self.__next_f.push([...])
    rsc_payloads = re.findall(
        r"self\.__next_f\.push\(\[(.*?)\]\)",
        html, re.DOTALL
    )
    if not rsc_payloads:
        raise RuntimeError(f"NextJS: RSC payload bulunamadı — {url}")

    all_payloads = " ".join(rsc_payloads)

    # CDN image URL'lerini çıkar
    cdn_urls = re.findall(
        r"https://cdn\.monomanga\.com\.tr/chapters/[^\"'\\\s,}\]]+\.(?:webp|jpg|png)",
        all_payloads
    )

    # Ayrıca HTML'deki doğrudan <img> tag'lerinden de topla
    img_tags = re.findall(
        r'<img[^>]+src="(https://cdn\.monomanga\.com\.tr/chapters/[^"]+)"',
        html
    )
    cdn_urls.extend(img_tags)

    # Benzersiz yap + sırala
    seen: set[str] = set()
    img_urls: list[str] = []
    for u in cdn_urls:
        if u not in seen:
            seen.add(u)
            img_urls.append(u)

    if not img_urls:
        raise RuntimeError(f"NextJS: hiç görsel URL bulunamadı — {url}")

    # 00.webp varsa önce onu al (ilk sayfa genelde 00)
    img_urls.sort(key=lambda u: (
        int(re.search(r'/(\d+)\.(?:webp|jpg|png)', u).group(1))
        if re.search(r'/(\d+)\.(?:webp|jpg|png)', u) else 999
    ))

    total = len(img_urls)
    files: list[str] = []

    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
        for i, img_url in enumerate(img_urls):
            ext = os.path.splitext(img_url.split("?")[0])[1] or ".webp"
            dest = os.path.join(output_dir, f"{i + 1:04d}{ext}")
            img_r = await client.get(img_url, headers=_image_headers(url))
            _save_image_response(img_r, dest, img_url)
            files.append(dest)
            if on_progress:
                await on_progress(i + 1, total)

    if not files:
        raise RuntimeError(f"NextJS: hiç sayfa indirilemedi — {url}")
    validate_manga_files(files)
    return files


async def _fetch_with_cf(url: str) -> tuple[str, str]:
    """curl_cffi impersonate ile CF korumalı sayfa getir; httpx fallback."""
    try:
        from curl_cffi.requests import AsyncSession
        async with AsyncSession(impersonate="chrome131") as s:
            resp = await s.get(url, timeout=20)
            if resp.status_code == 200 and "challenge" not in (resp.url or "").lower():
                text = resp.text
                if len(text) > 500 and "captcha" not in text[:300].lower():
                    return text, resp.url
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("curl_cffi hatası, httpx fallback: %s", exc)

    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers=_HEADERS) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.text, str(r.url)


async def _madara_chapter(url: str, output_dir: str, on_progress) -> list[str]:
    """Madara WordPress tema sitelerinden manga bölümü indir (?style=list ile)."""
    list_url = url.rstrip("/") + "/?style=list"

    try:
        html, _ = await _fetch_with_cf(list_url)
    except Exception:
        html, _ = await _fetch_with_cf(url)

    seen: set[str] = set()
    chapter_imgs: list[str] = []

    # 1. Reading-content section isolation — en hedefli, UI/icon/reklam dışlar
    reading_section = _extract_reading_section(html)
    if reading_section:
        chapter_imgs = _extract_img_urls_from_section(reading_section, seen)
        if chapter_imgs:
            hinted = [u for u in chapter_imgs if any(h in u.lower() for h in _PAGE_URL_HINTS)]
            if len(hinted) >= max(3, len(chapter_imgs) // 2):
                chapter_imgs = hinted

    # 2. wp-manga-chapter-img class'lı img'leri dene (Madara standart)
    if not chapter_imgs:
        for m in re.finditer(r'<img[^>]+class=["\'][^"\']*wp-manga-chapter-img[^"\']*["\'][^>]*>', html, re.IGNORECASE):
            tag = m.group(0)
            for attr in _LAZY_ATTRS:
                am = re.search(rf'{attr}\s*=\s*["\']([^"\']*)["\']', tag, re.IGNORECASE)
                if am:
                    src = am.group(1).strip()
                    if src.startswith("//"):
                        src = "https:" + src
                    if src and src.startswith("http") and src not in seen:
                        seen.add(src)
                        chapter_imgs.append(src)
                    break

    # 3. page-break class'lı img'leri dene
    if not chapter_imgs:
        for m in re.finditer(r'<img[^>]+class=["\'][^"\']*(?:page-break|reading-content|chapter-img)[^"\']*["\'][^>]*>', html, re.IGNORECASE):
            tag = m.group(0)
            for attr in _LAZY_ATTRS:
                am = re.search(rf'{attr}\s*=\s*["\']([^"\']*)["\']', tag, re.IGNORECASE)
                if am:
                    src = am.group(1).strip()
                    if src.startswith("//"):
                        src = "https:" + src
                    if src and src.startswith("http") and src not in seen:
                        seen.add(src)
                        chapter_imgs.append(src)
                    break

    # 4. Broad fallback — tighter filtrelerle (genişletilmiş lazy attrs + skip patterns)
    if not chapter_imgs:
        for m in re.finditer(r'(?:data-src|data-lazy-src|data-lazy|data-original|data-cfsrc|src)=["\']([^"\']*\.(?:jpg|jpeg|png|webp|avif)[^"\']*)["\']', html, re.IGNORECASE):
            src = m.group(1).strip()
            if src.startswith("//"):
                src = "https:" + src
            if not src or not src.startswith("http") or any(s in src.lower() for s in _SKIP_PATTERNS):
                continue
            if src not in seen:
                seen.add(src)
                chapter_imgs.append(src)
        hinted = [u for u in chapter_imgs if any(h in u.lower() for h in _PAGE_URL_HINTS)]
        if hinted:
            chapter_imgs = hinted
        else:
            numbered = [u for u in chapter_imgs if re.search(r'/\d{1,4}\.(?:jpg|jpeg|png|webp|avif)', u, re.IGNORECASE)]
            if numbered:
                chapter_imgs = numbered

    # URL'leri sırala (001, 002, ... sırasını koru)
    chapter_imgs.sort(key=lambda u: re.search(r'(\d+)\.(?:jpg|jpeg|png|webp|avif)', u, re.IGNORECASE).group(1)
                      if re.search(r'(\d+)\.(?:jpg|jpeg|png|webp|avif)', u, re.IGNORECASE) else u)

    if not chapter_imgs:
        raise RuntimeError(f"Madara: hiç sayfa görseli bulunamadı — {list_url}")

    total = len(chapter_imgs)
    files: list[str] = []

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=_HEADERS) as client:
        for i, img_url in enumerate(chapter_imgs):
            ext = re.search(r'\.(jpg|jpeg|png|webp)', img_url, re.IGNORECASE)
            ext_str = "." + (ext.group(1).lower() if ext else "jpg")
            dest = os.path.join(output_dir, f"{i + 1:04d}{ext_str}")
            img_r = await client.get(img_url, headers=_image_headers(list_url))
            _save_image_response(img_r, dest, img_url)
            files.append(dest)
            if on_progress:
                await on_progress(i + 1, total)

    if not files:
        raise RuntimeError(f"Madara: hiç sayfa indirilemedi — {url}")
    validate_manga_files(files)
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
            img_r = await client.get(img_url, headers=_image_headers(fetch_url))
            _save_image_response(img_r, dest, img_url)
            files.append(dest)
            if on_progress:
                await on_progress(i + 1, total)

    if not files:
        raise RuntimeError(f"uzaymanga.com: hiç sayfa indirilemedi — {fetch_url}")
    validate_manga_files(files)
    return files


async def extract_manga_chapter_tags(url: str) -> list[str]:
    """Manga/manhwa bölüm sayfasından yerel kaynak etiketlerini çıkar."""
    try:
        html, _ = await _fetch_with_cf(url)
        return extract_manga_source_tags(html, url)
    except Exception as exc:  # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning("Manga tag extraction failed for %s: %s", url[:60], exc)
        return []


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
                await on_progress(count, 0)

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
    validate_manga_files(files)
    return files
