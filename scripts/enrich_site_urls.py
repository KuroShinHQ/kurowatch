"""
enrich_site_urls.py — Site-siz içeriklere otomatik URL ekle.

Anime (Japon)  → tranimeizle.co  : https://www.tranimeizle.co/{slug}-1-bolum-izle
Türk dizi/TV   → dizibox.live    : https://www.dizibox.live/{slug}-izle/
Batı film/dizi → hdfilmcehennemi : https://www.hdfilmcehennemi.nl/{slug}-izle/
Manga/Manhwa   → mangaokutr.com  : https://mangaokutr.com/{slug}-bolum-1/
               + mangatr.net     : https://mangatr.net/manga/{slug}/bolum-1/
               + merlintoon.com  : https://merlintoon.com/seri/{slug}/  (pattern: test edildi)

Slug türetme:
  1. Başlıktaki (Romaji) parantezinden al
  2. Yoksa başlığı direkt kullan
  3. (S2)/(Season 2) tespiti → sezon parametresi ekle
  4. Lowercase, özel karakter temizle, boşluk → tire

Çalıştır:
  cd /mnt/c/Kuroshin/kurowatch
  python3 scripts/enrich_site_urls.py [--dry-run] [--type anime|manga|tr|west|all]
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

_TR_MAP = str.maketrans("ışğüöçİŞĞÜÖÇ", "isguocisguo c".replace(" ", ""))
_TR_MAP = str.maketrans({
    "ı": "i", "İ": "i",
    "ş": "s", "Ş": "s",
    "ğ": "g", "Ğ": "g",
    "ü": "u", "Ü": "u",
    "ö": "o", "Ö": "o",
    "ç": "c", "Ç": "c",
})


def slugify(text: str) -> str:
    text = text.lower().translate(_TR_MAP)       # ı ş ğ ü ö ç → ASCII
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[''']", "", text)
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_romaji(title: str) -> tuple[str, int]:
    season = 1
    sm = re.search(r'\bS(\d+)\b|\bSeason\s+(\d+)\b|(\d+)\.\s*(?:Sezon|Season|Kısım)\b', title, re.I)
    if sm:
        season = int(next(g for g in sm.groups() if g is not None))

    paren = re.findall(r'\(([^)]+)\)', title)
    romaji_from_paren = None
    for p in paren:
        if not re.match(r'^S\d+$|^Season\s+\d+$|^\d+\.\s*(Kısım|Sezon|Season|Part)$', p.strip(), re.I):
            romaji_from_paren = p.strip()
            break

    base = re.sub(r'\s*\([^)]*\)', '', title).strip()
    base = re.sub(r'\s+\d+\.\s*(Kısım|Sezon|Season|Part)\b.*$', '', base, flags=re.I).strip()
    base = re.sub(r'\s*S\d+$', '', base).strip()

    clean = romaji_from_paren or base
    return clean, season


def _clean_title(title: str) -> str:
    """Parantez, sezon bilgisi ve Türkçe/İngilizce çeviri parantezini kaldır."""
    clean = re.sub(r'\s*\([^)]*\)', '', title).strip()
    clean = re.sub(r'\s+\d+\.\s*(Kısım|Sezon|Season|Part)\b.*$', '', clean, flags=re.I).strip()
    return clean


# ── URL builder'lar ───────────────────────────────────────────────────

def build_tranimeizle_url(title: str) -> str:
    clean, season = extract_romaji(title)
    slug = slugify(clean) or slugify(title)
    if season > 1:
        return f"https://www.tranimeizle.co/{slug}-{season}-sezon-1-bolum-izle"
    return f"https://www.tranimeizle.co/{slug}-1-bolum-izle"


def build_dizibox_url(title: str) -> str:
    clean = _clean_title(title)
    slug = slugify(clean) or slugify(title)
    return f"https://www.dizibox.live/{slug}-izle/"


def build_hdfilm_url(title: str) -> str:
    clean = _clean_title(title)
    slug = slugify(clean) or slugify(title)
    return f"https://www.hdfilmcehennemi.nl/{slug}-izle/"


def build_manga_url(title: str) -> str:
    clean = _clean_title(title)
    slug = slugify(clean)
    return f"https://mangaokutr.com/{slug}-bolum-1/"


def build_mangatr_url(title: str) -> str:
    clean = _clean_title(title)
    slug = slugify(clean)
    return f"https://mangatr.net/manga/{slug}/bolum-1/"


def build_merlintoon_url(title: str) -> str:
    clean = _clean_title(title)
    slug = slugify(clean)
    return f"https://merlintoon.com/seri/{slug}/"


# ── İçerik sınıflandırma ─────────────────────────────────────────────

TURKISH_TV_KEYWORDS = [
    "kurtlar vadisi", "komedi dükkanı", "çok güzel", "öyle bir",
    "zamana karşı", "gladio", "recep ivedik", "çocuklar duymasın",
    "1 kadın", "yenilmez serisi",
]

WESTERN_MOVIE_KEYWORDS = [
    "real steel", "the maze runner", "maze runner", "lord of the rings",
    "yüzüklerin efendisi", "wolf of wall street", "para avcısı",
    "3 idiots", "howl's moving castle", "yürüyen şato",
    "undisputed",  # Batı yapımı dövüş filmi
]

CARTOON_KEYWORDS = [
    "green lantern", "secret saturdays", "my little pony",
    "monsters at work", "spider-man", "batman", "superman",
]


def classify_skipped(title: str) -> str:
    """
    Tranimeizle'ye gitmeyen içeriği sınıflandır.
    Returns: 'tr_tv' | 'west_movie' | 'cartoon' | 'unknown'
    """
    t_lower = title.lower()

    # Türk TV anahtar kelimeleri önce — explicit keyword eşleşmesi
    for kw in TURKISH_TV_KEYWORDS:
        if kw in t_lower:
            return "tr_tv"

    # Batı filmleri / Ghibli — explicit keyword eşleşmesi
    for kw in WESTERN_MOVIE_KEYWORDS:
        if kw in t_lower:
            return "west_movie"

    for kw in CARTOON_KEYWORDS:
        if kw in t_lower:
            return "cartoon"

    # Türkçe özel char var → Türk yapımı
    if re.search(r'[şğüöçıŞĞÜÖÇİ]', title):
        return "tr_tv"

    # Başlık tamamen Latin → Batı
    return "west_movie"


def should_skip_anime(title: str) -> bool:
    t_lower = title.lower()
    for kw in TURKISH_TV_KEYWORDS + WESTERN_MOVIE_KEYWORDS + CARTOON_KEYWORDS:
        if kw in t_lower:
            return True
    turkish_chars = sum(1 for c in t_lower if c in "şğüöçı")
    if turkish_chars >= 2:
        return True
    return False


# ── API işlemleri ─────────────────────────────────────────────────────

async def get_all_content(session: aiohttp.ClientSession):
    async with session.get(f"{API}/content") as r:
        return await r.json()


async def add_site(session: aiohttp.ClientSession, content_id: int,
                   site_name: str, site_url: str, dry_run: bool,
                   is_primary: bool = True) -> bool:
    if dry_run:
        primary_tag = "[ANA]" if is_primary else "[ek ]"
        print(f"    [DRY] {primary_tag} {site_name} -> {site_url}")
        return True
    try:
        async with session.post(
            f"{API}/content/{content_id}/sites",
            json={"site_name": site_name, "site_url": site_url, "is_primary": is_primary},
        ) as r:
            return r.status in (200, 201)
    except Exception as e:
        print(f"    [ERR] {e}")
        return False


# ── Ana işlem ─────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="DB'ye yazmadan sadece göster")
    parser.add_argument("--type", choices=["anime", "manga", "tr", "west", "all"], default="all",
                        help="anime=Japon | manga=manga/manhwa | tr=Türk dizi | west=Batı film | all=hepsi")
    parser.add_argument("--limit", type=int, default=0, help="Max içerik sayısı (test için)")
    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        all_content = await get_all_content(session)

    no_site = [c for c in all_content if not c.get("sites")]
    print(f"Site-siz toplam: {len(no_site)}")

    anime_list  = [c for c in no_site if c["type"] == "anime"]
    manga_list  = [c for c in no_site if c["type"] in ("manhwa", "manga")]

    results = {
        "anime_ok": 0, "tr_ok": 0, "west_ok": 0,
        "manga_ok": 0, "err": 0, "unknown": 0,
    }

    async with aiohttp.ClientSession() as session:

        # ── JAP ANİME ──
        if args.type in ("anime", "all"):
            targets = [c for c in anime_list if not should_skip_anime(c["title"])]
            if args.limit:
                targets = targets[:args.limit]
            print(f"\n=== JAP ANİME ({len(targets)}) ===")
            for c in targets:
                title, cid = c["title"], c["id"]
                url = build_tranimeizle_url(title)
                print(f"  [{cid}] {title[:55]}")
                print(f"        -> {url}")
                ok = await add_site(session, cid, "tranimeizle", url, args.dry_run)
                results["anime_ok" if ok else "err"] += 1
                await asyncio.sleep(0.05)

        # ── TÜRK DİZİ/TV ──
        if args.type in ("tr", "all"):
            targets = [c for c in anime_list if classify_skipped(c["title"]) == "tr_tv"]
            if args.limit:
                targets = targets[:args.limit]
            print(f"\n=== TÜRK DİZİ/TV ({len(targets)}) ===")
            for c in targets:
                title, cid = c["title"], c["id"]
                url = build_dizibox_url(title)
                print(f"  [{cid}] {title[:55]}")
                print(f"        -> {url}")
                ok = await add_site(session, cid, "dizibox", url, args.dry_run)
                results["tr_ok" if ok else "err"] += 1
                await asyncio.sleep(0.05)

        # ── BATI FİLM/DİZİ + CARTOON ──
        if args.type in ("west", "all"):
            targets = [c for c in anime_list
                       if classify_skipped(c["title"]) in ("west_movie", "cartoon", "unknown")]
            if args.limit:
                targets = targets[:args.limit]
            print(f"\n=== BATI FİLM/DİZİ ({len(targets)}) ===")
            for c in targets:
                title, cid = c["title"], c["id"]
                url = build_hdfilm_url(title)
                print(f"  [{cid}] {title[:55]}")
                print(f"        -> {url}")
                ok = await add_site(session, cid, "hdfilmcehennemi", url, args.dry_run)
                results["west_ok" if ok else "err"] += 1
                await asyncio.sleep(0.05)

        # ── MANGA/MANHWA ──
        if args.type in ("manga", "all"):
            targets = manga_list[:args.limit] if args.limit else manga_list
            print(f"\n=== MANGA/MANHWA ({len(targets)}) ===")
            for c in targets:
                title, cid = c["title"], c["id"]
                url_primary   = build_manga_url(title)
                url_secondary = build_mangatr_url(title)
                url_merlin    = build_merlintoon_url(title)
                print(f"  [{cid}] {c['type']} | {title[:50]}")
                print(f"        -> {url_primary}")
                ok = await add_site(session, cid, "mangaokutr",   url_primary,   args.dry_run, is_primary=True)
                await add_site(session, cid, "mangatr",       url_secondary, args.dry_run, is_primary=False)
                await add_site(session, cid, "merlintoon",    url_merlin,    args.dry_run, is_primary=False)
                results["manga_ok" if ok else "err"] += 1
                await asyncio.sleep(0.05)

    print(f"\n=== SONUÇ ===")
    print(f"Jap anime  : {results['anime_ok']} eklendi")
    print(f"Türk dizi  : {results['tr_ok']} eklendi")
    print(f"Batı film  : {results['west_ok']} eklendi")
    print(f"Manga      : {results['manga_ok']} eklendi")
    print(f"Hata       : {results['err']}")


if __name__ == "__main__":
    asyncio.run(main())
