#!/usr/bin/env python3
"""SOHBET-153 Madde 3+6: Tüm türlerden GERÇEK indirme testi."""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import AsyncSessionLocal
from backend.models import Content
from backend.downloader.manga import download_manga_chapter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

SAMPLES_PER_TYPE = 10
DOWNLOAD_BASE = "/mnt/c/Kuroshin/kurowatch/downloads/test_final"
RESULTS: list[dict] = []

async def test_content(c: Content, db) -> dict:
    result = {
        "id": c.id,
        "title": c.title,
        "type": c.type,
        "status": "FAILED",
        "error": None,
        "files": [],
        "total_bytes": 0,
        "duration_sec": 0,
        "site_used": None,
        "url_used": None,
    }

    if c.type == "game":
        result["status"] = "SKIPPED"
        result["error"] = "Oyunlar ayri test gerektirir"
        return result

    # Find primary working site
    primary = next((s for s in (c.sites or []) if s.is_primary and not s.is_dead), None)
    working = primary or next((s for s in (c.sites or []) if not s.is_dead and s.site_url), None)
    if not working:
        result["error"] = "Hic calisan site bulunamadi"
        RESULTS.append(result)
        return result

    # Get ep 1 URL for anime/series/movie, or chapter 1 URL for manga/manhwa
    from backend.routers.episodes import _extract_ep_from_url, _derive_ep_url
    site_url = working.site_url
    current_ep = _extract_ep_from_url(site_url)
    if not current_ep:
        result["error"] = "Site URL'sinden bolum numarasi cikarilamadi"
        RESULTS.append(result)
        return result

    result["site_used"] = working.site_name
    result["url_used"] = site_url

    # Derive url for ep 1
    ep1_url = _derive_ep_url(site_url, current_ep, 1)
    if not ep1_url:
        result["error"] = "1. bolum URL'si turetilenmedi"
        RESULTS.append(result)
        return result

    # Determine output dir
    type_dir = c.type
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in c.title)[:40]
    output_dir = os.path.join(DOWNLOAD_BASE, type_dir, f"{c.id}_{safe_title}", "ep001")

    start = time.time()
    try:
        if c.type in ("anime", "series", "movie", "cartoon"):
            from backend.downloader.anime import download_anime_episode
            files = await download_anime_episode(ep1_url, output_dir)
        else:
            files = await download_manga_chapter(ep1_url, output_dir)

        duration = time.time() - start

        total_bytes = 0
        file_details = []
        for f in files:
            if os.path.exists(f):
                sz = os.path.getsize(f)
                total_bytes += sz
                file_details.append({"path": f, "size": sz})

        if file_details:
            result["status"] = "OK"
            result["files"] = file_details
            result["total_bytes"] = total_bytes
            result["duration_sec"] = round(duration, 1)
            print(f"  OK: {c.title} -> {len(file_details)} dosya, {total_bytes/1024:.1f}KB, {duration:.1f}s")
        else:
            result["status"] = "FAILED"
            result["error"] = "Dosya indirildi ama diskte bulunamadi"
            print(f"  FAILED: {c.title} -> dosya bulunamadi")

    except Exception as exc:
        duration = time.time() - start
        result["status"] = "FAILED"
        result["error"] = str(exc)[:200]
        result["duration_sec"] = round(duration, 1)
        print(f"  FAILED: {c.title} -> {exc}")

    RESULTS.append(result)
    return result

async def main():
    os.makedirs(DOWNLOAD_BASE, exist_ok=True)

    async with AsyncSessionLocal() as db:
        r = await db.execute(
            select(Content).options(selectinload(Content.sites))
            .order_by(Content.id)
        )
        all_items = r.scalars().all()

    # Group by type
    by_type: dict[str, list] = {}
    for c in all_items:
        by_type.setdefault(c.type, []).append(c)

    print("=== TURLERE GORE TEST BASLIYOR ===")

    all_types = ["anime", "manga", "manhwa", "movie", "series", "cartoon"]
    for t in all_types:
        items = by_type.get(t, [])
        if not items:
            print(f"\n[tur={t}] Hic icerik yok, atlaniyor")
            continue

        # Pick first SAMPLES_PER_TYPE items that have working sites
        candidates = []
        for c in items:
            if len(candidates) >= SAMPLES_PER_TYPE:
                break
            working = any(s for s in (c.sites or []) if not s.is_dead and s.site_url)
            if working and c.external_id:
                candidates.append(c)

        if not candidates:
            print(f"\n[tur={t}] Calisan siteye sahip icerik bulunamadi")
            continue

        print(f"\n[tur={t}] {len(candidates)} icerik test ediliyor...")
        async with AsyncSessionLocal() as db:
            for c in candidates:
                r = await db.execute(
                    select(Content).options(selectinload(Content.sites))
                    .where(Content.id == c.id)
                )
                c_full = r.scalar_one_or_none()
                if c_full:
                    await test_content(c_full, db)
                await asyncio.sleep(1)

    # Generate summary
    print("\n\n=== TEST SONUCLARI ===")
    by_status: dict[str, int] = {}
    by_type_status: dict[str, dict] = {}
    for r in RESULTS:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_type_status.setdefault(r["type"], {})
        by_type_status[r["type"]][r["status"]] = by_type_status[r["type"]].get(r["status"], 0) + 1

    print(f"\nGenel: {len(RESULTS)} test")
    for s, cnt in sorted(by_status.items()):
        pct = cnt / len(RESULTS) * 100 if RESULTS else 0
        print(f"  {s}: {cnt} ({pct:.1f}%)")

    print("\nTure gore:")
    for t, statuses in sorted(by_type_status.items()):
        total_t = sum(statuses.values())
        ok_t = statuses.get("OK", 0)
        print(f"  {t}: {ok_t}/{total_t} basarili ({ok_t/total_t*100:.1f}%)" if total_t else f"  {t}: 0 test")

    # Save results to JSON
    report_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "SOHBET-153_TEST_SONUCLARI.json")
    with open(report_path, "w") as f:
        json.dump(RESULTS, f, indent=2, ensure_ascii=False)
    print(f"\nSonuclar kaydedildi: {report_path}")

    # Summary line for report
    ok_count = sum(1 for r in RESULTS if r["status"] == "OK")
    fail_count = sum(1 for r in RESULTS if r["status"] == "FAILED")
    skip_count = sum(1 for r in RESULTS if r["status"] == "SKIPPED")
    print(f"\nOZET: {ok_count} OK / {fail_count} FAILED / {skip_count} SKIPPED / {len(RESULTS)} TOTAL")
    print(f"Basari: {ok_count/max(len(RESULTS)-skip_count, 1)*100:.1f}% (skip haric)")

if __name__ == "__main__":
    asyncio.run(main())
