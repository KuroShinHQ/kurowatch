"""
fix_duplicate_enrichment.py
----------------------------
Aynı external_id'ye sahip birden fazla içerik kaydını temizler.
Strateji: Her grup için en düşük ID'yi (ilk eklenen) koru,
          diğerlerinin external_id + cover_url + genres'ini sıfırla.

Silme YOK — sadece yanlış enrichment verisi temizlenir.
"""
import asyncio
import json
from collections import defaultdict
from sqlalchemy import select, update
from backend.database import AsyncSessionLocal
from backend.models import Content


async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Content.id, Content.title, Content.external_id, Content.cover_url, Content.genres)
            .where(Content.external_id.isnot(None))
            .order_by(Content.id)
        )
        rows = result.fetchall()

    # external_id'ye göre grupla
    groups = defaultdict(list)
    for row in rows:
        groups[row.external_id].append(row)

    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Toplam duplicate external_id grubu: {len(duplicates)}")

    to_clear = []  # (id, title) tuple listesi
    for ext_id, items in duplicates.items():
        # En düşük id = koru, diğerleri temizle
        items_sorted = sorted(items, key=lambda x: x.id)
        keeper = items_sorted[0]
        losers = items_sorted[1:]
        print(f"\n  ext_id: {ext_id}")
        print(f"    KORU  → id:{keeper.id} '{keeper.title}'")
        for loser in losers:
            print(f"    TEMİZLE → id:{loser.id} '{loser.title}'")
            to_clear.append(loser.id)

    print(f"\n{'='*60}")
    print(f"Temizlenecek kayıt sayısı: {len(to_clear)}")
    print(f"(external_id + cover_url + genres sıfırlanacak, kayıt silinmeyecek)")

    confirm = input("\nDevam? (e/h): ").strip().lower()
    if confirm != 'e':
        print("İptal.")
        return

    async with AsyncSessionLocal() as db:
        cleared = 0
        for content_id in to_clear:
            await db.execute(
                update(Content)
                .where(Content.id == content_id)
                .values(external_id=None, cover_url=None, genres=None)
            )
            cleared += 1
        await db.commit()
        print(f"\n✅ {cleared} kayıt temizlendi.")

    # Gerçek duplicate kontrol (aynı başlık benzeri)
    print("\n--- Gerçek duplicate (aynı başlık) tespiti ---")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Content.id, Content.title).order_by(Content.id))
        all_items = result.fetchall()

    title_groups = defaultdict(list)
    for row in all_items:
        # Normalize: küçük harf, noktalama kaldır
        normalized = row.title.lower().replace("'", "").replace(".", "").replace("-", " ").strip()
        title_groups[normalized].append(row)

    real_dupes = {k: v for k, v in title_groups.items() if len(v) > 1}
    if real_dupes:
        print(f"Benzer başlık grubu: {len(real_dupes)}")
        for norm, items in list(real_dupes.items())[:10]:
            print(f"  '{norm}'")
            for it in items:
                print(f"    id:{it.id} '{it.title}'")
    else:
        print("Gerçek duplicate başlık yok.")


if __name__ == "__main__":
    asyncio.run(main())
