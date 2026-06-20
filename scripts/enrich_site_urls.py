"""
enrich_site_urls.py — Site-siz anime/manhwa'lara otomatik URL ekle.

Anime  → tranimeizle.co  : https://www.tranimeizle.co/{slug}-1-bolum-izle
Manga/Manhwa → mangaokutr.com : https://mangaokutr.com/{slug}-bolum-1/
              fallback mangatr.net : https://mangatr.net/manga/{slug}/bolum-1/

Slug türetme:
  1. Başlıktaki (Romaji) parantezinden al
  2. Yoksa başlığı direkt kullan
  3. (S2)/(Season 2) tespiti → sezon parametresi ekle
  4. Lowercase, özel karakter temizle, boşluk → tire

Çalıştır:
  cd /mnt/c/Kuroshin/kurowatch
  python3 scripts/enrich_site_urls.py [--dry-run] [--type anime|manga|all]
"""

import asyncio
import re
import sys
import argparse
import unicodedata
from typing import Optional
import aiohttp

API = "http://localhost:8099/api"

# ── Slug türetme ──────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[''']", "", text)          # apostrof kaldır
    text = re.sub(r"[^a-z0-9\s-]", " ", text)  # özel char → boşluk
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_romaji(title: str) -> tuple[str, int]:
    """
    Başlıktan (romaji) ve sezon numarası çıkar.
    Returns: (clean_title, season_num)
    """
    # Sezon tespiti: (S2), (S3), Season 2, 2. Sezon, 2. Kısım
    season = 1
    sm = re.search(r'\bS(\d+)\b|\bSeason\s+(\d+)\b|(\d+)\.\s*(?:Sezon|Season|Kısım)\b', title, re.I)
    if sm:
        season = int(next(g for g in sm.groups() if g is not None))

    # Parantez içi romaji: "Title (RomajiTitle)"
    # Ama bazı parantezler sezon: "(S2)", "(Season 2)", "(Part 2)"
    paren = re.findall(r'\(([^)]+)\)', title)
    romaji_from_paren = None
    for p in paren:
        # Sezon parantezi değilse romaji kabul et
        if not re.match(r'^S\d+$|^Season\s+\d+$|^\d+\.\s*(Kısım|Sezon|Season|Part)$', p.strip(), re.I):
            romaji_from_paren = p.strip()
            break

    # Temel başlığı bul (parantezleri ve sezon bilgisini kaldır)
    base = re.sub(r'\s*\([^)]*\)', '', title).strip()
    base = re.sub(r'\s+\d+\.\s*(Kısım|Sezon|Season|Part)\b.*$', '', base, flags=re.I).strip()
    base = re.sub(r'\s*S\d+$', '', base).strip()

    clean = romaji_from_paren or base
    return clean, season


def build_tranimeizle_url(title: str) -> str:
    clean, season = extract_romaji(title)
    slug = slugify(clean)
    if not slug:
        slug = slugify(title)
    if season > 1:
        return f"https://www.tranimeizle.co/{slug}-{season}-sezon-1-bolum-izle"
    return f"https://www.tranimeizle.co/{slug}-1-bolum-izle"


def build_manga_url(title: str) -> str:
    # Parantez içi temizle (remake, S2 vb.)
    clean = re.sub(r'\s*\([^)]*\)', '', title).strip()
    slug = slugify(clean)
    return f"https://mangaokutr.com/{slug}-bolum-1/"


def build_mangatr_url(title: str) -> str:
    clean = re.sub(r'\s*\([^)]*\)', '', title).strip()
    slug = slugify(clean)
    return f"https://mangatr.net/manga/{slug}/bolum-1/"

# ── Türk/Batı içerik filtresi ─────────────────────────────────────────

# Bu kelimeler başlıkta varsa Türk/Batı yapımı — tranimeizle'de olmaz
SKIP_KEYWORDS_TR_WEST = [
    "kurtlar vadisi", "komedi dükkanı", "çok güzel", "öyle bir",
    "zamana karşı", "gladio", "recep ivedik", "1 kadın", "3 idiots",
    "real steel", "green lantern", "secret saturdays", "my little pony",
    "monsters at work", "howl's moving castle",  # Ghibli .co'da olabilir ama skip
    "undisputed", "yenilmez serisi",
]

def should_skip_anime(title: str) -> bool:
    t_lower = title.lower()
    for kw in SKIP_KEYWORDS_TR_WEST:
        if kw in t_lower:
            return True
    # Türkçe özel karakterler → muhtemelen Türk yapımı
    # (ama "Spy x Family" gibi başlıklar da geçerli)
    turkish_chars = sum(1 for c in t_lower if c in "şğüöçı")
    if turkish_chars >= 2:
        return True
    return False

# ── API işlemleri ─────────────────────────────────────────────────────

async def get_all_content(session: aiohttp.ClientSession):
    async with session.get(f"{API}/content") as r:
        return await r.json()


async def add_site(session: aiohttp.ClientSession, content_id: int,
                   site_name: str, site_url: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"    [DRY] POST /api/content/{content_id}/sites  {site_name} -> {site_url}")
        return True
    try:
        async with session.post(
            f"{API}/content/{content_id}/sites",
            json={"site_name": site_name, "site_url": site_url, "is_primary": True},
        ) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"    [ERR] {e}")
        return False

# ── Ana işlem ─────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazmadan sadece göster")
    parser.add_argument("--type", choices=["anime", "manga", "all"], default="all")
    parser.add_argument("--limit", type=int, default=0, help="Max içerik sayısı (test için)")
    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        all_content = await get_all_content(session)

    # Site-siz içerikleri filtrele
    no_site = [c for c in all_content if not c.get("sites")]
    print(f"Site-siz toplam: {len(no_site)}")

    anime_list = [c for c in no_site if c["type"] == "anime"]
    manga_list = [c for c in no_site if c["type"] in ("manhwa", "manga")]

    results = {"anime_ok": 0, "anime_skip": 0, "manga_ok": 0, "manga_err": 0}

    async with aiohttp.ClientSession() as session:

        # ── ANİME ──
        if args.type in ("anime", "all"):
            targets = anime_list[:args.limit] if args.limit else anime_list
            print(f"\n=== ANİME ({len(targets)}) ===")
            for c in targets:
                title = c["title"]
                cid   = c["id"]

                if should_skip_anime(title):
                    print(f"  [SKIP] [{cid}] {title}")
                    results["anime_skip"] += 1
                    continue

                url = build_tranimeizle_url(title)
                print(f"  [{cid}] {title[:55]}")
                print(f"        -> {url}")

                ok = await add_site(session, cid, "tranimeizle", url, args.dry_run)
                if ok:
                    results["anime_ok"] += 1
                else:
                    results["manga_err"] += 1
                await asyncio.sleep(0.05)  # DB rate limit

        # ── MANGA/MANHWA ──
        if args.type in ("manga", "all"):
            targets = manga_list[:args.limit] if args.limit else manga_list
            print(f"\n=== MANGA/MANHWA ({len(targets)}) ===")
            for c in targets:
                title = c["title"]
                cid   = c["id"]

                url_primary  = build_manga_url(title)
                url_secondary = build_mangatr_url(title)
                print(f"  [{cid}] {c['type']} | {title[:50]}")
                print(f"        -> {url_primary}")

                ok = await add_site(session, cid, "mangaokutr", url_primary, args.dry_run)
                # İkincil site de ekle
                await add_site(session, cid, "mangatr", url_secondary, args.dry_run)
                if ok:
                    results["manga_ok"] += 1
                else:
                    results["manga_err"] += 1
                await asyncio.sleep(0.05)

    print(f"\n=== SONUÇ ===")
    print(f"Anime eklendi: {results['anime_ok']}  |  Atlandı: {results['anime_skip']}")
    print(f"Manga eklendi: {results['manga_ok']}  |  Hata: {results['manga_err']}")


if __name__ == "__main__":
    asyncio.run(main())
