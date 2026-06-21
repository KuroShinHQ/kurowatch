"""
enrich_turkanime.py — tranimeizle-only anime için turkanime.tv URL eşleştir.

Strateji:
  1. ta_index.json yükle (build_ta_index.py çıktısı — 4713 slug)
  2. AniList romaji → slug varyantları üret
  3. ta_index'te exact + prefix match ara
  4. Bulunan URL'yi /api/content/{id}/sites ile DB'ye ekle

Çalıştır:
  python3 scripts/enrich_turkanime.py [--dry-run] [--limit N]
"""
import asyncio
import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Optional

import aiohttp
import httpx

API = "http://localhost:8099/api"
TA_BASE = "https://www.turkanime.tv"
INDEX_PATH = Path("/mnt/c/Kuroshin/kurowatch/scripts/ta_index.json")
ROMAJI_CACHE_PATH = Path("/mnt/c/Kuroshin/kurowatch/scripts/ta_romaji_cache.json")

ANILIST_URL = "https://graphql.anilist.co"
_ROMAJI_QUERY = """
query ($id: Int, $malId: Int) {
  Media(id: $id, idMal: $malId) {
    title { romaji english native }
    synonyms
  }
}
"""


def _to_slug(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9\s\-]", " ", s)
    s = re.sub(r"[\s\-]+", "-", s).strip("-")
    return s


def _titles_overlap(content_title: str, romaji: str, english: Optional[str] = None) -> bool:
    """AniList sonucunun içerik başlığıyla anlamlı örtüşmesi var mı?
    Kural: İçerik başlığının ilk anlamlı kelimesi AniList ROMAJI başlığında geçmeli.
    (English title değil — 'walking alone', 'green green' gibi şans eseri eşleşmeleri önler)
    """
    STOP_WORDS = {"the", "and", "for", "with", "from", "that", "this", "have", "will",
                  "your", "its", "into", "their", "than", "been", "also", "when", "after",
                  "dead", "lone", "dark", "deep", "blue", "back", "side", "time", "life",
                  "king", "queen", "hero", "tale", "saga", "epic", "code", "star", "moon",
                  "soul", "fire", "iron", "gold", "wild", "free", "last", "next", "zero"}

    def first_sig_word(s):
        words = re.sub(r"[^a-z0-9\s]", " ", (s or "").lower()).split()
        for w in words:
            if len(w) >= 4 and w not in STOP_WORDS:
                return w
        return None

    def all_words(s):
        return set(w for w in re.sub(r"[^a-z0-9\s]", " ", (s or "").lower()).split() if len(w) >= 4)

    c_first = first_sig_word(content_title)
    if not c_first:
        return True  # Çok kısa başlık → güven ver

    # Önce romaji'de ara (daha güvenilir — chance overlap daha az)
    r_words = all_words(romaji)
    if c_first in r_words:
        return True

    # Romaji'de yoksa english'e bak — ama içerik ilk kelimesi english'in İLK kelimesi olmalı
    # (herhangi bir kelimede olması yetmez — "walking" in "Bungo Stray Dogs: Walking Alone" gibi hataları önler)
    e_first = first_sig_word(english or "")
    if e_first and c_first == e_first:
        return True

    return False


def _slug_variants(romaji: Optional[str], english: Optional[str] = None,
                   synonyms: Optional[list] = None, ta_slug: Optional[str] = None) -> tuple:
    """
    Dönüş: (prefix_variants, exact_only_variants)
    prefix_variants → hem exact hem prefix match için (güvenilir: romaji/english)
    exact_only_variants → sadece exact match için (synonymlar — prefix'te yanlış eşleştirir)
    """
    prefix_v = []
    exact_v = []

    def add_prefix(slug):
        if slug and len(slug) >= 3 and slug not in prefix_v:
            prefix_v.append(slug)

    def add_exact(slug):
        if slug and len(slug) >= 3 and slug not in prefix_v and slug not in exact_v:
            exact_v.append(slug)

    if romaji:
        full = _to_slug(romaji)
        add_prefix(full)
        parts = full.split("-")
        # Prefix varyantları: minimum 2 kelime VE 8+ karakter
        for n in range(2, min(len(parts), 6)):
            candidate = "-".join(parts[:n])
            if len(candidate) >= 8:
                add_prefix(candidate)
        # "no" kelimesiz (Japonca partikel)
        no_no = _to_slug(re.sub(r"\bno\b", "", romaji.lower()).strip())
        add_prefix(no_no)
        # "wo" kelimesiz
        wo_less = _to_slug(re.sub(r"\bwo\b", "", romaji.lower()).strip())
        add_prefix(wo_less)

    if english:
        e_slug = _to_slug(english)
        add_prefix(e_slug)
        e_parts = e_slug.split("-")
        for n in range(2, min(len(e_parts), 4)):
            candidate = "-".join(e_parts[:n])
            if len(candidate) >= 8:
                add_prefix(candidate)

    # Synonymlar sadece exact match — prefix'te yanlış eşleştirir
    for syn in (synonyms or []):
        if syn:
            add_exact(_to_slug(syn))

    if ta_slug:
        add_prefix(ta_slug)

    return prefix_v, exact_v


def _slug_word_overlap(content_title: str, matched_slug: str, romaji: Optional[str]) -> bool:
    """Eşleşen slug ile içerik başlığı veya romaji arasında anlamlı örtüşme var mı?
    Slug kelimelerine veya romaji kelimelerine bakarak doğrular.
    """
    def words(s):
        return set(w for w in re.sub(r"[^a-z0-9]", " ", (s or "").lower()).split() if len(w) >= 4)

    slug_words = words(matched_slug.replace("-", " "))
    title_words = words(content_title)
    romaji_words = words(romaji or "")

    # Slug ile başlık arasında kelime örtüşmesi
    if slug_words & title_words:
        return True
    # Romaji slug, variant'lardan birinin prefix'i mi?
    # (romaji-based eşleşmelerde slug ile romaji kelimeleri örtüşür)
    if slug_words & romaji_words:
        return True
    return False


def lookup_in_index(index: dict, prefix_variants: list, exact_variants: list,
                    content_title: str = "", romaji: Optional[str] = None) -> Optional[tuple]:
    """
    1. Exact match (tüm variant'lar — güvenilir)
    2. Prefix match (sadece prefix_variants, min 8 karakter)
    3. Post-match doğrulama: slug ile başlık/romaji örtüşmeli
    Dönüş: (matched_slug, ep_url) veya None
    """
    index_slugs = list(index.keys())
    all_for_exact = list(dict.fromkeys(prefix_variants + exact_variants))

    def validate(slug):
        return _slug_word_overlap(content_title, slug, romaji)

    # 1. Exact match
    for v in all_for_exact:
        if v in index:
            slug = v
            if validate(slug):
                return (slug, index[slug])

    # 2. Prefix match — sadece güvenilir (romaji/english) variant'lardan, min 8 karakter
    for v in prefix_variants:
        if len(v) < 8:
            continue
        matches = [s for s in index_slugs if s.startswith(v + "-") or s == v]
        if matches:
            best = min(matches, key=len)
            if validate(best):
                return (best, index[best])

    return None


def load_romaji_cache() -> dict:
    """ta_romaji_cache.json → {content_id: {romaji, english, synonyms}}"""
    if not ROMAJI_CACHE_PATH.exists():
        return {}
    with open(ROMAJI_CACHE_PATH) as f:
        data = json.load(f)
    return {str(e["id"]): e for e in data}


DB_PATH = "/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db"

def add_site_db(content_id: int, url: str) -> bool:
    """SQLite'a direkt yaz — API yerine (WSL←→Windows bağlantı sorunu)."""
    try:
        conn = sqlite3.connect(DB_PATH)
        # Duplicate kontrolü
        exists = conn.execute(
            "SELECT 1 FROM site WHERE content_id=? AND site_url=?", (content_id, url)
        ).fetchone()
        if exists:
            conn.close()
            return True  # Zaten var
        conn.execute(
            "INSERT INTO site (content_id, site_name, site_url, is_primary, is_dead) VALUES (?,?,?,0,0)",
            (content_id, "turkanime.tv", url),
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False


async def add_site(session: aiohttp.ClientSession, content_id: int, url: str, dry_run: bool) -> bool:
    if dry_run:
        return True
    return add_site_db(content_id, url)


def get_targets() -> list:
    """DB'den sadece tranimeizle URL'si olan animeleri çek."""
    conn = sqlite3.connect("/mnt/c/Kuroshin/kurowatch/memory/kurowatch.db")
    q = """
        SELECT c.id, c.title, c.external_id,
               (SELECT s.site_url FROM site s
                WHERE s.content_id=c.id AND s.site_url LIKE '%tranimeizle%'
                LIMIT 1) as ta_url
        FROM content c
        WHERE c.type = 'anime'
        AND EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%tranimeizle%')
        AND NOT EXISTS (SELECT 1 FROM site s WHERE s.content_id=c.id AND s.site_url LIKE '%turkanime%')
        ORDER BY c.title
    """
    rows = conn.execute(q).fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "external_id": r[2], "tranimeizle_url": r[3]} for r in rows]


def _slug_from_ta_url(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"/([a-z0-9-]+?)-\d+-(?:bolum|sezon|season|episode)", url, re.IGNORECASE)
    return m.group(1) if m else None


async def process(item: dict, index: dict, romaji_cache: dict,
                   session: aiohttp.ClientSession, dry_run: bool) -> str:
    cid = item["id"]
    title = item["title"]
    ta_url = item.get("tranimeizle_url") or ""

    romaji = english = None
    synonyms = []

    cached = romaji_cache.get(str(cid))
    if cached:
        romaji = cached.get("romaji")
        english = cached.get("english")
        synonyms = cached.get("synonyms") or []
        # Güven kontrolü: AniList sonucu içerik başlığıyla uyuşmuyor mu?
        # Eğer hiçbir kelime örtüşmesi yoksa, yanlış anime eşleşmesi demektir
        if romaji and not _titles_overlap(title, romaji, english):
            romaji = english = None
            synonyms = []

    ta_slug = _slug_from_ta_url(ta_url)
    title_slug = _to_slug(title)
    prefix_v, exact_v = _slug_variants(romaji, english, synonyms, ta_slug)

    # Başlık slug'ını prefix listesine ekle (fallback)
    if title_slug and len(title_slug) >= 3 and title_slug not in prefix_v:
        prefix_v.append(title_slug)
        parts = title_slug.split("-")
        for n in range(2, min(len(parts), 4)):
            candidate = "-".join(parts[:n])
            if len(candidate) >= 8 and candidate not in prefix_v:
                prefix_v.append(candidate)

    result = lookup_in_index(index, prefix_v, exact_v, title, romaji)

    if result:
        matched_slug, ep_url = result
        ok = await add_site(session, cid, ep_url, dry_run)
        status = "✅" if ok else "⚠️"
        print(f"  {status} [{cid}] {title[:42]:42} → {matched_slug}")
        return "found"
    else:
        tried = ", ".join(prefix_v[:3])
        print(f"  ❌ [{cid}] {title[:42]:42}  (denendi: {tried[:55]})")
        return "not_found"


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=6)
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print("HATA: ta_index.json bulunamadı. Önce build_ta_index.py çalıştır.")
        return

    with open(INDEX_PATH) as f:
        index = json.load(f)
    print(f"Index yüklendi: {len(index)} slug")

    romaji_cache = load_romaji_cache()
    print(f"Romaji cache: {len(romaji_cache)} kayıt")

    targets = get_targets()
    if args.limit:
        targets = targets[:args.limit]

    print("=" * 65)
    print(f"turkanime.tv Eşleştirme | hedef={len(targets)} | dry={args.dry_run}")
    print("=" * 65)

    sem = asyncio.Semaphore(args.concurrency)
    connector = aiohttp.TCPConnector(ssl=False, limit=args.concurrency)

    async with aiohttp.ClientSession(connector=connector) as session:
        async def _task(item):
            async with sem:
                return await process(item, index, romaji_cache, session, args.dry_run)

        results = await asyncio.gather(*[_task(t) for t in targets])

    found = results.count("found")
    not_found = results.count("not_found")

    print()
    print("=" * 65)
    print(f"SONUÇ: Bulunan={found} | Bulunamayan={not_found} | Toplam={len(targets)}")
    if args.dry_run:
        print("(DRY RUN — DB'ye yazılmadı)")
    print("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
