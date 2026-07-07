"""
KuroWatch Tip Yeniden Sınıflandırma Aracı (SOHBET-118 eki)

Kullanım: Backend ayaktayken POST /api/analytics/reclassify
         veya direkt: cd backend && python reclassify.py

Kurallar:
  1. title veya title_tr icinde belirli anahtar kelimeler varsa → series/movie
  2. external_id uzerinden AniList format kontrolu (opsiyonel)
  3. Manuel ID mapping (en guvenilir)
"""
import asyncio
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models import Content, Tag, ContentTag


# ── MANUEL MAPPING: ID → yeni tip ─────────────────────────────────────
# Kesin bilinen yanlis siniflandirmalar. Genisletmek icin buraya ekle.
MANUAL_MAP: dict[int, str] = {
    # Live-action TV series → series
    112: "series",   # Dexter (S8)
    287: "series",   # Dexter
    346: "series",   # Hannibal
    # Western animation (kullanici karari) → series
    113: "series",   # Rick and Morty (S7)
    505: "series",   # Rick and Morty
    114: "series",   # Marvel's What If (S3)
    650: "series",   # What If...?
}

# ── ANAHTAR KELIME KURALLARI ─────────────────────────────────────────
# title icinde gecen kelime → yeni tip (case-insensitive)
KEYWORD_RULES: list[tuple[str, str]] = [
    # TV kanal / yapim sirketi
]

# ── DISARDAN FILTRE: asla anime kalmasi gerekenler (keyword kurallarini ezmek icin)
KEEP_ANIME_IDS: set[int] = {
    715,  # Black Butler: Book of Murder (Japon anime)
    716,  # Black Butler: Public School Arc (Japon anime)
}


async def ensure_tags(db: AsyncSession) -> dict[str, int]:
    """series/movie tag'lerini yoksa olustur, id'lerini don."""
    tag_ids = {}
    for name in ("series", "movie", "anime", "manga", "manhwa", "game"):
        r = await db.execute(
            select(Tag).where(Tag.tag_type == "api", Tag.name == name)
        )
        t = r.scalar_one_or_none()
        if t:
            tag_ids[name] = t.id
    return tag_ids


async def reclassify(dry_run: bool = True) -> dict:
    """
    Tum icerikleri tara, MANUAL_MAP ve kurallara gore tip guncelle.
    dry_run=True: sadece rapor, DB'ye yazma.
    """
    stats = {"checked": 0, "changed": 0, "skipped": 0, "errors": 0}
    changes = []

    async with AsyncSessionLocal() as db:
        tag_ids = await ensure_tags(db)

        r = await db.execute(select(Content))
        all_items = r.scalars().all()

        for c in all_items:
            stats["checked"] += 1
            new_type = None

            # Manuel mapping (en yuksek oncelik)
            if c.id in MANUAL_MAP:
                new_type = MANUAL_MAP[c.id]

            # Keep-anime listesi
            if c.id in KEEP_ANIME_IDS:
                new_type = None

            if new_type and new_type != c.type:
                changes.append((c.id, c.title, c.type, new_type))
                stats["changed"] += 1
                if not dry_run:
                    old_type = c.type
                    c.type = new_type

                    # Eski tip tag'ini kaldir
                    if old_type in tag_ids:
                        ct_tbl = ContentTag.__table__
                        await db.execute(
                            ct_tbl.delete().where(
                                ct_tbl.c.content_id == c.id,
                                ct_tbl.c.tag_id == tag_ids[old_type],
                            )
                        )

                    # Yeni tip tag'ini ekle
                    if new_type in tag_ids:
                        ct_tbl = ContentTag.__table__
                        exists = await db.execute(
                            select(ContentTag).where(
                                ct_tbl.c.content_id == c.id,
                                ct_tbl.c.tag_id == tag_ids[new_type],
                            )
                        )
                        if not exists.scalar_one_or_none():
                            db.add(ContentTag(content_id=c.id, tag_id=tag_ids[new_type]))
            else:
                stats["skipped"] += 1

        if not dry_run:
            await db.commit()

    return {
        "dry_run": dry_run,
        "stats": stats,
        "changes": [{"id": c[0], "title": c[1], "from": c[2], "to": c[3]} for c in changes],
    }


async def main():
    print("=== DRY RUN ===")
    result = await reclassify(dry_run=True)
    print(f"Kontrol: {result['stats']['checked']}, Degisecek: {result['stats']['changed']}")
    for ch in result["changes"]:
        print(f"  ID={ch['id']} | {ch['from']:8} → {ch['to']:8} | {ch['title'][:50]}")

    print(f"\n=== GERCEK CALISTIRMAK ICIN: python reclassify.py --apply ===")


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    result = asyncio.run(reclassify(dry_run=dry))
    mode = "GERCEK" if not dry else "DRY RUN"
    print(f"\n=== {mode} ===")
    print(f"Kontrol: {result['stats']['checked']}, Degisti: {result['stats']['changed']}")
    for ch in result["changes"]:
        print(f"  ID={ch['id']} | {ch['from']:8} → {ch['to']:8} | {ch['title'][:50]}")
    if dry:
        print("\nCalistirmak icin: python backend/reclassify.py --apply")
