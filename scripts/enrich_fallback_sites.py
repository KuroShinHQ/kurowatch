"""
enrich_fallback_sites.py — Oto fallback site eşleştirme.

Mantık:
  - Sadece broken/dead site olan içerikleri hedef al
  - Anime  → turkanime.tv + anizm.net'te arama yap
  - Manga  → mangawow.com + mangawow.org + hayalistic.com.tr + ragnarscans.com/net + merlintoon.com'da ara
  - Manhwa → mangawow.com + hayalistic.com.tr'de ara
  - Bulunan URL'yi DB'ye Site olarak ekle (is_primary=False)
  - Zaten aynı domain'de site varsa ekleme

Çalıştır:
  python3 scripts/enrich_fallback_sites.py [--dry-run] [--type anime|manga|manhwa|all] [--limit N]

--dry-run : DB'ye yazma, sadece raporla
--limit N : İlk N içerikle sınırla (test için)
"""
import asyncio
import argparse
import re
import urllib.parse
from typing import Optional

import aiohttp
import sqlite3

# ── Config ────────────────────────────────────────────────────────────
API = "http://localhost:8099/api"
TIMEOUT = aiohttp.ClientTimeout(total=10)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",  # Brotli dışla (aiohttp desteklemiyor)
}

# ── Arama stratejileri ────────────────────────────────────────────────

def _title_slug(title: str) -> str:
    """Başlık → URL slug (boşluk→-, özel karakter kaldır)."""
    s = re.sub(r'[^a-z0-9\s-]', '', title.lower()).strip()
    s = re.sub(r'\s+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')


def _slug_from_tranimeizle_url(site_url: str) -> Optional[str]:
    """
    tranimeizle.co URL'sinden anime slug'ı çıkar.
    /saihate-no-paladin-1-bolum-izle → saihate-no-paladin
    """
    m = re.search(r'/([a-z0-9-]+?)-\d+-(?:bolum|sezon|season|episode)', site_url, re.IGNORECASE)
    return m.group(1) if m else None


async def search_turkanime(session, title: str, site_url: str = "") -> Optional[str]:
    """
    turkanime.tv'de anime ara.
    1. tranimeizle.co slug → turkanime.tv/video/SLUG-1-bolum (direkt)
    2. Başarısız → başlıktan slug türet, dene
    """
    slugs_to_try = []

    # Önce mevcut tranimeizle URL'sinden slug al
    if site_url and "tranimeizle" in site_url:
        s = _slug_from_tranimeizle_url(site_url)
        if s:
            slugs_to_try.append(s)

    # Başlıktan slug türet (fallback)
    slugs_to_try.append(_title_slug(title))

    for slug in slugs_to_try:
        for ep_suffix in ("1-bolum", "1-sezon-1-bolum"):
            ep_url = f"https://www.turkanime.tv/video/{slug}-{ep_suffix}"
            try:
                async with session.get(ep_url, headers=HEADERS, timeout=TIMEOUT) as r:
                    if r.status == 200:
                        html = await r.text()
                        # Gerçek anime sayfası mı? (video player içermeli)
                        if any(k in html for k in ("video-js", "jwplayer", "iframe", "player", "videojs")):
                            return ep_url
            except Exception:
                pass

    return None


async def search_anizm(session, title: str, site_url: str = "") -> Optional[str]:
    """
    anizm.net → direkt slug tahmin.
    1. tranimeizle slug'ından dene
    2. Başlık slug'ından dene
    """
    slugs_to_try = []

    if site_url and "tranimeizle" in site_url:
        s = _slug_from_tranimeizle_url(site_url)
        if s:
            slugs_to_try.append(s)
    slugs_to_try.append(_title_slug(title))

    for slug in slugs_to_try:
        candidates = [
            f"https://anizm.net/{slug}-1-bolum",
            f"https://anizm.net/{slug}-1-sezon-1-bolum",
        ]
        for url in candidates:
            try:
                async with session.get(url, headers={**HEADERS, "Referer": "https://anizm.net/"}, timeout=TIMEOUT) as r:
                    if r.status == 200:
                        html = await r.text()
                        if any(k in html for k in ("anizmplayer", "m3u8", "player", "video-js")):
                            return url
            except Exception:
                pass
    return None


_BAD_URL_PARTS = {"bolum-acma-merkezi", "/feed", "/page/", "wp-json", "wp-admin", "#"}


def _slug_similarity(title: str, url: str) -> bool:
    """URL'deki slug başlıkla yeterince örtüşüyor mu? (False positive engeli)"""
    title_words = set(re.findall(r'[a-z0-9]+', title.lower())) - {"the", "a", "an", "of", "in", "to"}
    url_slug = re.search(r'/(?:manga|manhwa)/([^/]+)', url)
    if not url_slug:
        return False
    slug_words = set(re.sub(r'-+', ' ', url_slug.group(1)).split())
    common = title_words & slug_words
    return len(common) >= max(1, len(title_words) // 3)


async def search_manga_site(session, title: str, base_url: str, site_name: str) -> Optional[str]:
    """Madara tema sitelerde manga arama: direkt slug + WordPress search."""
    slug = _title_slug(title)

    # 1. Direkt slug dene — manga sayfası URL'ini döndür (chapter değil)
    for prefix in ("manga", "manhwa"):
        slug_url = base_url.rstrip("/") + f"/{prefix}/{slug}/"
        try:
            async with session.get(slug_url, headers={**HEADERS, "Referer": base_url}, timeout=TIMEOUT) as r:
                if r.status == 200:
                    html = await r.text()
                    if "reading-content" in html or "wp-manga" in html or "chapter" in html.lower():
                        return slug_url
        except Exception:
            pass

    # 2. WordPress search — başlık benzerliği kontrolü ile
    domain = re.search(r'https?://(?:www\.)?([^/]+)', base_url).group(1)
    search_url = base_url.rstrip("/") + f"/?s={urllib.parse.quote(title)}&post_type=wp-manga"
    try:
        async with session.get(search_url, headers={**HEADERS, "Referer": base_url}, timeout=TIMEOUT) as r:
            if r.status != 200:
                return None
            html = await r.text()
        links = re.findall(
            rf'href=["\']([^"\']*{re.escape(domain)}/(?:manga|manhwa)/[^"\']+)["\']',
            html, re.IGNORECASE
        )
        links = [l for l in links if not any(p in l for p in _BAD_URL_PARTS)]
        # Sadece başlıkla örtüşen slug'ı kabul et
        for link in links:
            if _slug_similarity(title, link):
                return link
    except Exception:
        pass
    return None


# ── Ana mantık ────────────────────────────────────────────────────────

ANIME_SEARCHERS = [
    ("turkanime.tv",  search_turkanime),
    ("anizm.net",     search_anizm),
]

MANGA_SITES = [
    ("mangawow.com",       "https://mangawow.com/"),
    ("mangawow.org",       "https://mangawow.org/"),
    ("hayalistic.com.tr",  "https://hayalistic.com.tr/"),
    ("ragnarscans.com",    "https://ragnarscans.com/"),
    ("ragnarscans.net",    "https://ragnarscans.net/"),
    ("merlintoon.com",     "https://merlintoon.com/"),
    ("mangadenizi.com",    "https://mangadenizi.com/"),
]

MANHWA_SITES = [
    ("mangawow.com",       "https://mangawow.com/"),
    ("hayalistic.com.tr",  "https://hayalistic.com.tr/"),
    ("ragnarscans.net",    "https://ragnarscans.net/"),
]


def domain_of(url: str) -> str:
    m = re.search(r'https?://(?:www\.)?([^/]+)', url or "")
    return m.group(1) if m else ""


async def get_contents(session, content_type: str) -> list:
    """API'den içerikleri çek."""
    async with session.get(f"{API}/content?type={content_type}", timeout=TIMEOUT) as r:
        return await r.json()


async def add_site(session, content_id: int, site_name: str, site_url: str, dry_run: bool) -> bool:
    if dry_run:
        return True
    try:
        async with session.post(
            f"{API}/content/{content_id}/sites",
            json={"site_name": site_name, "site_url": site_url, "is_primary": False},
            timeout=TIMEOUT
        ) as r:
            return r.status in (200, 201)
    except Exception:
        return False


async def process_anime(session, items: list, dry_run: bool, semaphore: asyncio.Semaphore):
    found = 0
    skipped = 0
    not_found = 0

    for item in items:
        cid = item["id"]
        title = item["title"]
        existing_domains = {domain_of(s["site_url"]) for s in item.get("sites", [])}

        # Mevcut tranimeizle URL'sini bul (slug için)
        primary_site_url = next(
            (s["site_url"] for s in item.get("sites", []) if "tranimeizle" in s.get("site_url", "")),
            ""
        )

        async with semaphore:
            for site_name, searcher in ANIME_SEARCHERS:
                target_domain = site_name
                if target_domain in existing_domains:
                    continue

                url = await searcher(session, title, primary_site_url)
                if url:
                    ok = await add_site(session, cid, site_name, url, dry_run)
                    if ok:
                        print(f"  ✅ [{cid}] {title[:40]:40} → {site_name}: {url[:60]}")
                        found += 1
                        break
            else:
                not_found += 1

    return found, skipped, not_found


async def process_manga(session, items: list, manga_sites: list, dry_run: bool, semaphore: asyncio.Semaphore):
    found = 0
    not_found = 0

    for item in items:
        cid = item["id"]
        title = item["title"]
        existing_domains = {domain_of(s["site_url"]) for s in item.get("sites", [])}
        got_one = False

        async with semaphore:
            for site_name, base_url in manga_sites:
                target_domain = site_name
                if target_domain in existing_domains:
                    continue
                url = await search_manga_site(session, title, base_url, site_name)
                if url:
                    ok = await add_site(session, cid, site_name, url, dry_run)
                    if ok:
                        print(f"  ✅ [{cid}] {title[:40]:40} → {site_name}: {url[:60]}")
                        found += 1
                        got_one = True

        if not got_one:
            not_found += 1

    return found, not_found


def has_only_broken_sites(item: dict) -> bool:
    """Sadece ölü/broken siteleri var mı?"""
    sites = item.get("sites", [])
    if not sites:
        return True
    # En az bir çalışan site varsa atla
    BROKEN_DOMAINS = {
        "tranimeizle.co", "tranimeizle.io", "mangatr.net", "mangaokutr.com",
        "ruyamanga.net", "ruyamanga.com", "asurascans.com.tr",
        "manga-sehri.net", "mangasehri.net", "uzaymanga.com",
    }
    working = [s for s in sites if domain_of(s["site_url"]) not in BROKEN_DOMAINS and not s.get("is_dead")]
    return len(working) == 0


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--type", choices=["anime", "manga", "manhwa", "all"], default="all")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()

    dry = args.dry_run
    sem = asyncio.Semaphore(args.concurrency)

    print("=" * 65)
    print(f"Fallback Site Eşleştirme | dry_run={dry} | type={args.type}")
    print("=" * 65)

    async with aiohttp.ClientSession() as session:

        if args.type in ("anime", "all"):
            print("\n[ANİME] turkanime.tv + anizm.net arama...")
            items = await get_contents(session, "anime")
            targets = [i for i in items if has_only_broken_sites(i)]
            if args.limit:
                targets = targets[:args.limit]
            print(f"  Hedef: {len(targets)}/{len(items)} anime (broken/no-site)")
            tasks = [process_anime(session, [t], dry, sem) for t in targets]
            results = await asyncio.gather(*tasks)
            total_found = sum(r[0] for r in results)
            total_nf = sum(r[2] for r in results)
            print(f"  → Bulunan: {total_found} | Bulunamayan: {total_nf}")

        if args.type in ("manga", "all"):
            print("\n[MANGA] Madara sitelerde arama...")
            items = await get_contents(session, "manga")
            targets = [i for i in items if has_only_broken_sites(i)]
            if args.limit:
                targets = targets[:args.limit]
            print(f"  Hedef: {len(targets)}/{len(items)} manga")
            tasks = [process_manga(session, [t], MANGA_SITES, dry, sem) for t in targets]
            results = await asyncio.gather(*tasks)
            total_found = sum(r[0] for r in results)
            total_nf = sum(r[1] for r in results)
            print(f"  → Bulunan: {total_found} | Bulunamayan: {total_nf}")

        if args.type in ("manhwa", "all"):
            print("\n[MANHWA] Madara sitelerde arama...")
            items = await get_contents(session, "manhwa")
            targets = [i for i in items if has_only_broken_sites(i)]
            if args.limit:
                targets = targets[:args.limit]
            print(f"  Hedef: {len(targets)}/{len(items)} manhwa")
            tasks = [process_manga(session, [t], MANHWA_SITES, dry, sem) for t in targets]
            results = await asyncio.gather(*tasks)
            total_found = sum(r[0] for r in results)
            total_nf = sum(r[1] for r in results)
            print(f"  → Bulunan: {total_found} | Bulunamayan: {total_nf}")

    print("\n" + "=" * 65)
    print(f"TAMAMLANDI {'(DRY RUN - DB yazılmadı)' if dry else ''}")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
