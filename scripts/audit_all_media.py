"""
audit_all_media.py — 676 içerik durum raporu.

Kontroller:
  - cover_url  : HEAD isteği → 200/301/302 OK, diğerleri DEAD
  - site_url   : HEAD isteği → 200/301/302 OK, diğerleri DEAD
  - tags       : boş mu
  - external_score : var mı
  - synopsis   : var mı

Dead site tespiti:
  - Ölü site → PATCH /api/sites/{id}/mark-dead
  - Canlı site → PATCH /api/sites/{id}/mark-alive
  - DB güncellemesi sonrası frontend detail kartında ⚠️ gösterir

Çalıştır:
  cd /mnt/c/Kuroshin/kurowatch (veya PowerShell)
  python3 scripts/audit_all_media.py [--no-mark] [--limit N] [--type anime|manga|all]

--no-mark : Sadece raporla, DB'yi güncelleme
--limit N : İlk N içerikle sınırla (test için)
--output FILE : Raporu JSON dosyasına da kaydet
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime
from typing import Optional
import aiohttp

API = "http://localhost:8099/api"
TIMEOUT = aiohttp.ClientTimeout(total=12)
CONCURRENCY = 20  # eş zamanlı HEAD istek sayısı

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
}

OK_STATUSES = {200, 201, 301, 302, 303, 307, 308}


# ── HTTP HEAD kontrolü ────────────────────────────────────────────────

async def head_check(session: aiohttp.ClientSession, url: str, sem: asyncio.Semaphore) -> tuple[str, int]:
    """URL'ye HEAD isteği at. (url, status_code) döndür. Hata → 0."""
    async with sem:
        try:
            async with session.head(url, headers=HEADERS, allow_redirects=True, timeout=TIMEOUT) as r:
                return url, r.status
        except Exception:
            try:
                # HEAD başarısız → GET ile dene (bazı siteler HEAD desteklemez)
                async with session.get(url, headers=HEADERS, allow_redirects=True, timeout=TIMEOUT) as r:
                    return url, r.status
            except Exception:
                return url, 0


def is_ok(status: int) -> bool:
    return status in OK_STATUSES


# ── API işlemleri ─────────────────────────────────────────────────────

async def get_all_content(session: aiohttp.ClientSession) -> list:
    async with session.get(f"{API}/content", timeout=TIMEOUT) as r:
        return await r.json()


async def mark_site(session: aiohttp.ClientSession, site_id: int, dead: bool, dry_run: bool) -> None:
    if dry_run:
        return
    action = "mark-dead" if dead else "mark-alive"
    try:
        async with session.patch(f"{API}/sites/{site_id}/{action}", timeout=TIMEOUT) as r:
            if r.status not in (200, 201):
                print(f"    [WARN] mark {action} site_id={site_id} → status={r.status}", flush=True)
    except Exception as e:
        print(f"    [ERR] mark {action} site_id={site_id}: {e}", flush=True)


# ── Rapor ─────────────────────────────────────────────────────────────

def _bar(n: int, total: int, width: int = 20) -> str:
    filled = int(width * n / total) if total else 0
    return "█" * filled + "░" * (width - filled)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-mark", action="store_true", help="DB güncelleme — sadece raporla")
    parser.add_argument("--limit",   type=int, default=0)
    parser.add_argument("--type",    choices=["anime", "manga", "manhwa", "game", "all"], default="all")
    parser.add_argument("--output",  default="", help="JSON raporu kaydet")
    args = parser.parse_args()

    dry_run = args.no_mark

    async with aiohttp.ClientSession() as session:
        all_content = await get_all_content(session)

    # Filtrele
    if args.type != "all":
        all_content = [c for c in all_content if c["type"] == args.type]
    if args.limit:
        all_content = all_content[:args.limit]

    total = len(all_content)
    print(f"\n{'='*60}")
    print(f"  KuroWatch Medya Audit — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  Toplam: {total} içerik  |  dry_run={dry_run}")
    print(f"{'='*60}\n")

    # ── URL listesi topla ──────────────────────────────────────────────
    cover_checks: list[tuple[int, str]] = []   # (content_id, url)
    site_checks:  list[tuple[int, int, str]] = []  # (content_id, site_id, url)

    for c in all_content:
        if c.get("cover_url"):
            cover_checks.append((c["id"], c["cover_url"]))
        for s in c.get("sites", []):
            if s.get("site_url"):
                site_checks.append((c["id"], s["id"], s["site_url"]))

    total_urls = len(cover_checks) + len(site_checks)
    print(f"HEAD kontrolü: {len(cover_checks)} cover + {len(site_checks)} site = {total_urls} URL\n")

    # ── Paralel HEAD kontrolleri ───────────────────────────────────────
    sem = asyncio.Semaphore(CONCURRENCY)
    cover_url_set = list(dict.fromkeys(u for _, u in cover_checks))
    site_url_set  = list(dict.fromkeys(u for _, _, u in site_checks))

    print("Cover URL kontrol ediliyor...", flush=True)
    async with aiohttp.ClientSession() as session:
        cover_tasks = [head_check(session, u, sem) for u in cover_url_set]
        cover_results = await asyncio.gather(*cover_tasks)
    cover_status: dict[str, int] = dict(cover_results)

    print("Site URL kontrol ediliyor...", flush=True)
    async with aiohttp.ClientSession() as session:
        site_tasks = [head_check(session, u, sem) for u in site_url_set]
        site_results = await asyncio.gather(*site_tasks)
    site_status: dict[str, int] = dict(site_results)

    # ── DB güncelle (dead/alive) ───────────────────────────────────────
    if not dry_run:
        print("\nSite durumları DB'ye yazılıyor...", flush=True)
        async with aiohttp.ClientSession() as session:
            mark_tasks = []
            for _cid, sid, url in site_checks:
                dead = not is_ok(site_status.get(url, 0))
                mark_tasks.append(mark_site(session, sid, dead, dry_run=False))
            await asyncio.gather(*mark_tasks)

    # ── Rapor oluştur ─────────────────────────────────────────────────
    issues: dict[str, list] = {
        "dead_covers": [],
        "dead_sites":  [],
        "no_cover":    [],
        "no_site":     [],
        "no_tags":     [],
        "no_ext_score":[],
        "no_synopsis": [],
    }

    stats = {
        "total": total,
        "with_cover": 0, "dead_cover": 0,
        "with_site":  0, "dead_site":  0,
        "with_tags":  0,
        "with_score": 0,
        "with_synopsis": 0,
    }

    for c in all_content:
        cid, title, ctype = c["id"], c["title"], c["type"]

        # Cover
        if c.get("cover_url"):
            stats["with_cover"] += 1
            st = cover_status.get(c["cover_url"], 0)
            if not is_ok(st):
                stats["dead_cover"] += 1
                issues["dead_covers"].append({"id": cid, "title": title, "url": c["cover_url"], "status": st})
        else:
            issues["no_cover"].append({"id": cid, "title": title, "type": ctype})

        # Sites
        sites = c.get("sites", [])
        if sites:
            stats["with_site"] += 1
            for s in sites:
                st = site_status.get(s.get("site_url", ""), 0)
                if not is_ok(st):
                    stats["dead_site"] += 1
                    issues["dead_sites"].append({
                        "content_id": cid, "title": title,
                        "site_id": s["id"], "site_name": s["site_name"],
                        "url": s["site_url"], "status": st,
                    })
        else:
            issues["no_site"].append({"id": cid, "title": title, "type": ctype})

        # Tags
        if c.get("tags"):
            stats["with_tags"] += 1
        else:
            issues["no_tags"].append({"id": cid, "title": title})

        # External score
        if c.get("external_score") is not None:
            stats["with_score"] += 1
        else:
            issues["no_ext_score"].append({"id": cid, "title": title})

        # Synopsis
        if c.get("synopsis"):
            stats["with_synopsis"] += 1
        else:
            issues["no_synopsis"].append({"id": cid, "title": title})

    # ── Ekrana yazdır ─────────────────────────────────────────────────
    T = stats["total"]
    print(f"\n{'='*60}")
    print(f"  RAPOR")
    print(f"{'='*60}")
    print(f"  Cover     : {stats['with_cover']:4}/{T}  {_bar(stats['with_cover'], T)}  "
          f"ölü={stats['dead_cover']}")
    print(f"  Site      : {stats['with_site']:4}/{T}  {_bar(stats['with_site'], T)}  "
          f"ölü={stats['dead_site']}")
    print(f"  Tag       : {stats['with_tags']:4}/{T}  {_bar(stats['with_tags'], T)}")
    print(f"  Ext Score : {stats['with_score']:4}/{T}  {_bar(stats['with_score'], T)}")
    print(f"  Synopsis  : {stats['with_synopsis']:4}/{T}  {_bar(stats['with_synopsis'], T)}")

    if issues["dead_covers"]:
        print(f"\n⚠️  ÖLÜDEAD COVER ({len(issues['dead_covers'])}):")
        for x in issues["dead_covers"][:10]:
            print(f"  [{x['id']:4}] {x['title'][:50]} | {x['status']} | {x['url'][:60]}")

    if issues["dead_sites"]:
        print(f"\n⚠️  ÖLÜ SİTE ({len(issues['dead_sites'])}):")
        for x in issues["dead_sites"][:15]:
            print(f"  [{x['content_id']:4}] {x['title'][:35]} | {x['site_name']:15} | "
                  f"{x['status']} | {x['url'][:50]}")

    if issues["no_cover"]:
        print(f"\n📷 COVER-SIZ ({len(issues['no_cover'])}):")
        for x in issues["no_cover"][:10]:
            print(f"  [{x['id']:4}] {x['type']:8} | {x['title'][:55]}")

    if issues["no_site"]:
        print(f"\n🔗 SİTE-SİZ ({len(issues['no_site'])}):")
        for x in issues["no_site"][:10]:
            print(f"  [{x['id']:4}] {x['type']:8} | {x['title'][:55]}")

    print(f"\n{'='*60}")
    if not dry_run:
        print(f"  ✅ {stats['dead_site']} ölü site DB'de işaretlendi (is_dead=True)")
    else:
        print("  ℹ️  --no-mark: DB güncellenmedi")
    print(f"{'='*60}\n")

    # ── JSON çıktı ────────────────────────────────────────────────────
    report = {
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "issues": issues,
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"Rapor kaydedildi: {args.output}")

    return report


if __name__ == "__main__":
    asyncio.run(main())
