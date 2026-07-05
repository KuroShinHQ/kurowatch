#!/usr/bin/env python3
"""
KuroWatch Content Health Checker v1.0
Tüm içeriklerin 1. bölüm URL'lerini test eder.
Anime: CF'ye takılanları tranimaci.com'da kurtarır.
Manga/Manhwa: akıllı isim eşleştirme ile alternatif URL dener.

Kullanım:
  python -m backend.tools.content_health             # tüm içerikler
  python -m backend.tools.content_health --type anime # sadece anime
  python -m backend.tools.content_health --id 18      # tek içerik
  python -m backend.tools.content_health --dead-only  # sadece kırık URL'ler
  python -m backend.tools.content_health --fix        # kurtarılan URL'leri DB'de güncelle
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

# Proje kökünü sys.path'e ekle
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models import Content, Episode, Site
from backend.tools.url_ping import (
    http_ping, slugify, construct_tranimaci_url,
    construct_madara_url, PING_RESULT, PingResult,
)

# ── Rapor kategorileri ────────────────────────────────────────────────

class HealthStatus:
    OK = "OK"              # Test geçti, URL çalışıyor
    SITE_YOK = "SITE_YOK"  # 404 — sitede bu içerik mevcut değil
    CF_BLOCKED = "CF_BLOCKED"  # 403 Cloudflare
    OFFLINE = "OFFLINE"    # Site kapalı/erişilemez
    DNS_FAIL = "DNS_FAIL"
    TIMEOUT = "TIMEOUT"
    CONN_REFUSED = "CONN_REFUSED"
    PARSE_HATASI = "PARSE_HATASI"
    KURTARILDI = "KURTARILDI"  # Fallback ile çalışan URL bulundu
    TURKISH_PASS = "TURKISH_PASS"  # TR chapter/URL çalışıyor
    EP_YOK = "EP_YOK"     # Hiç episode URL'si yok
    NAME_MISMATCH = "NAME_MISMATCH"  # İsim eşleşmedi
    HATA = "HATA"

    @classmethod
    def is_pass(cls, s: str) -> bool:
        return s in (cls.OK, cls.KURTARILDI, cls.TURKISH_PASS)

    @classmethod
    def is_fail(cls, s: str) -> bool:
        return s in (cls.SITE_YOK, cls.CF_BLOCKED, cls.OFFLINE,
                     cls.DNS_FAIL, cls.TIMEOUT, cls.CONN_REFUSED,
                     cls.PARSE_HATASI, cls.HATA)


@dataclass
class ContentHealth:
    id: int
    title: str
    title_tr: str
    type: str
    ep_url: Optional[str]
    site_url: Optional[str]
    site_name: Optional[str]

    # Test sonuçları
    status: str = HealthStatus.EP_YOK
    tested_url: str = ""
    used_fallback: str = ""
    detail: str = ""
    ping: Optional[PingResult] = None


# ── Ana Sağlık Kontrol Sınıfı ────────────────────────────────────────

class HealthChecker:
    def __init__(self, dead_only: bool = False, verbose: bool = False,
                 fix: bool = False):
        self.dead_only = dead_only
        self.verbose = verbose
        self.fix = fix
        self.results: list[ContentHealth] = []
        self.stats: dict[str, int] = {}
        self._start_time = 0.0
        self._fixed_count = 0

    async def run(self, content_type: Optional[str] = None,
                  content_id: Optional[int] = None):
        self._start_time = time.time()
        items = await self._load_content(content_type, content_id)
        total = len(items)
        print(f"\n{'='*60}")
        print(f"KUROWATCH İÇERİK SAĞLIĞI TARAMASI")
        print(f"{'='*60}")
        print(f"  Toplam: {total} içerik")
        if self.dead_only:
            print(f"  Mod: sadece ölü/hatalı URL'ler")
        print(f"  Başlangıç: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")

        for i, item in enumerate(items, 1):
            ch = await self._check_one(item)
            self.results.append(ch)

            if not HealthStatus.is_pass(ch.status):
                print(f"  ❌ [{i}/{total}] #{ch.id} {ch.title[:50]:<50} "
                      f"{ch.status}")
                if self.verbose and ch.detail:
                    print(f"      → {ch.detail}")
            elif self.dead_only:
                pass  # sadece ölüleri göster
            else:
                icon = "✅" if ch.status == HealthStatus.OK else \
                       "🔄" if ch.status == HealthStatus.KURTARILDI else \
                       "🇹🇷"
                print(f"  {icon} [{i}/{total}] #{ch.id} {ch.title[:50]:<50} "
                      f"{ch.status}")

        self._print_report()

    async def _load_content(self, content_type: Optional[str] = None,
                             content_id: Optional[int] = None):
        async with AsyncSessionLocal() as db:
            stmt = select(Content).options(
                selectinload(Content.episodes),
                selectinload(Content.sites),
            )
            if content_id:
                stmt = stmt.where(Content.id == content_id)
            if content_type:
                stmt = stmt.where(Content.type == content_type)
            stmt = stmt.order_by(Content.id)
            result = await db.execute(stmt)
            return result.scalars().all()

    async def _check_one(self, c: Content) -> ContentHealth:
        ch = ContentHealth(
            id=c.id, title=c.title, title_tr=c.title_tr or "",
            type=c.type,
            ep_url=None, site_url=None, site_name=None,
        )

        eps = sorted(c.episodes or [], key=lambda e: e.number)
        ep1 = next((e for e in eps if e.number == 1), eps[0] if eps else None)

        if not ep1 or not ep1.url:
            ch.status = HealthStatus.EP_YOK
            return ch

        ch.ep_url = ep1.url
        sites = sorted(c.sites or [],
                       key=lambda s: (0 if s.is_primary else 1))
        if sites:
            ch.site_url = sites[0].site_url
            ch.site_name = sites[0].site_name

        # 1. Doğrudan test
        result = await http_ping(ch.ep_url)
        ch.ping = result
        ch.tested_url = ch.ep_url

        if result.is_ok():
            ch.status = HealthStatus.OK
            return ch

        if result.is_blocked():
            ch.detail = f"Doğrudan: {result.detail}"

        elif result.is_dead():
            ch.detail = f"Doğrudan: {result.detail}"
        else:
            ch.detail = f"Doğrudan: {result.detail}"

        # 2. Fallback mekanizması
        if c.type == "anime":
            await self._anime_fallback(ch, c)
        elif c.type in ("manga", "manhwa"):
            await self._manga_fallback(ch, c)
        else:
            ch.status = self._classify_result(result)

        return ch

    def _classify_result(self, r: PingResult) -> str:
        return r.status

    async def _update_ep_url(self, content_id: int, new_url: str):
        """Episode 1 URL'sini DB'de güncelle."""
        if not self.fix:
            return
        from sqlalchemy import update as sql_update
        async with AsyncSessionLocal() as db:
            stmt = select(Episode).where(
                Episode.content_id == content_id,
                Episode.number == 1,
            ).limit(1)
            result = await db.execute(stmt)
            ep = result.scalar_one_or_none()
            if ep:
                ep.url = new_url
                await db.commit()
                self._fixed_count += 1

    async def _anime_fallback(self, ch: ContentHealth, c: Content):
        """Anime: CF/takılma durumunda tranimaci.com'da dene."""
        titles = [c.title]
        if c.title_tr:
            titles.insert(0, c.title_tr)

        for title in titles:
            url = construct_tranimaci_url(title, ep=1)
            ch.detail += f" | Fallback: {url[:60]}..."
            result = await http_ping(url)

            if result.is_ok():
                ch.status = HealthStatus.KURTARILDI
                ch.used_fallback = url
                ch.ping = result
                ch.tested_url = url
                ch.detail = f"Kurtarıldı: tranimaci.com (eski: {ch.ep_url})"
                if self.fix:
                    await self._update_ep_url(c.id, url)
                return

            if result.is_dead():
                ch.detail += f" | {result.status}: {result.detail[:40]}"
                continue

            # CF/timout → başka title dene
            ch.detail += f" | {result.status}"

        # Hiçbiri işe yaramadı — durumu koru
        ch.status = self._classify_result(ch.ping) if ch.ping else HealthStatus.HATA

    async def _manga_fallback(self, ch: ContentHealth, c: Content):
        """Manga/Manhwa: çalışan sitelerde akıllı isim eşleştirme dene."""
        from backend.downloader.manga import _MADARA_DOMAINS, _CF_BLOCKED, _OFFLINE

        working_sites = [d for d in _MADARA_DOMAINS
                         if d not in _CF_BLOCKED and d not in _OFFLINE]

        titles = [c.title]
        if c.title_tr:
            titles.insert(0, c.title_tr)

        # İngilizce title'ı da dene
        if c.title != c.title and not c.title_tr:
            titles.append(c.title)

        tried: list[str] = []
        for title in titles:
            for site in working_sites:
                url = construct_madara_url(f"https://{site}", title, ep=1)
                tried.append(url)
                ch.detail += f" | Denenen: {url[:60]}..."
                result = await http_ping(url)

                if result.is_ok():
                    ch.status = HealthStatus.KURTARILDI
                    ch.used_fallback = url
                    ch.ping = result
                    ch.tested_url = url
                    ch.detail = f"Kurtarıldı: {site} (eski: {ch.ep_url})"
                    if self.fix:
                        await self._update_ep_url(c.id, url)
                    return

                if result.is_blocked():
                    continue

                if result.is_dead():
                    continue

                # SITE_YOK → isim eşleşmedi, başka title dene
                if result.status == "SITE_YOK":
                    ch.detail += " isim eşleşmedi"
                    continue

        # Tüm denemeler başarısız
        if ch.ping and ch.ping.status == "CF_BLOCKED":
            ch.status = HealthStatus.CF_BLOCKED
        elif ch.ping and ch.ping.is_dead():
            ch.status = HealthStatus.SITE_YOK if ch.ping.status == "SITE_YOK" else HealthStatus.OFFLINE
        elif ch.ping and ch.ping.status == "SITE_YOK":
            ch.status = HealthStatus.NAME_MISMATCH
            ch.detail = f"Ne DB'deki ne de alternatif isimler {len(tried)} sitede bulundu"
        else:
            ch.status = self._classify_result(ch.ping) if ch.ping else HealthStatus.HATA

    def _print_report(self):
        elapsed = time.time() - self._start_time
        cats: dict[str, int] = {}
        type_cats: dict[str, dict[str, int]] = {}
        for r in self.results:
            cats[r.status] = cats.get(r.status, 0) + 1
            if r.type not in type_cats:
                type_cats[r.type] = {}
            type_cats[r.type][r.status] = type_cats[r.type].get(r.status, 0) + 1

        total = len(self.results)
        passed = sum(v for k, v in cats.items() if HealthStatus.is_pass(k))
        failed = sum(v for k, v in cats.items() if HealthStatus.is_fail(k))
        no_ep = cats.get(HealthStatus.EP_YOK, 0)

        print(f"\n{'='*60}")
        print(f"  RAPOR")
        print(f"{'='*60}")
        print(f"  Süre: {elapsed:.1f}sn")
        print(f"  Toplam: {total}")
        print(f"  ✅ Geçen: {passed} (%{passed*100//total if total else 0})")
        print(f"  ❌ Kalan: {failed}")
        print(f"  ⏭️  Ep yok: {no_ep}")
        if self.fix:
            print(f"  🔧 Düzeltilen: {self._fixed_count}")
        print()

        for t in ("anime", "manga", "manhwa", "game"):
            if t not in type_cats:
                continue
            tc = type_cats[t]
            t_pass = sum(v for k, v in tc.items() if HealthStatus.is_pass(k))
            t_fail = sum(v for k, v in tc.items() if HealthStatus.is_fail(k))
            print(f"  [{t.upper()}] Geçen: {t_pass}  Kalan: {t_fail}  "
                  f"Ep yok: {tc.get(HealthStatus.EP_YOK, 0)}")

        print()
        for cat in sorted(cats.keys()):
            print(f"    {cat}: {cats[cat]}")

        # Detaylı kırık liste
        broken = [r for r in self.results if HealthStatus.is_fail(r.status)]
        if broken:
            print(f"\n{'='*60}")
            print(f"  KIRIK URL'LER ({len(broken)} adet)")
            print(f"{'='*60}")
            for r in sorted(broken, key=lambda x: x.id):
                print(f"  #{r.id} [{r.type}] {r.title}")
                print(f"    URL: {r.ep_url or '(yok)'}")
                if r.used_fallback:
                    print(f"    Fallback: {r.used_fallback}")
                print(f"    Durum: {r.status}")
                if r.detail:
                    print(f"    Detay: {r.detail[:120]}")
                print()

        # Kurtarılanlar
        saved = [r for r in self.results if r.status == HealthStatus.KURTARILDI]
        if saved:
            print(f"\n{'='*60}")
            print(f"  KURTARILANLAR ({len(saved)} adet)")
            print(f"{'='*60}")
            for r in saved:
                print(f"  #{r.id} [{r.type}] {r.title}")
                print(f"    Eski: {r.ep_url}")
                print(f"    Yeni: {r.tested_url}")
                print()

        # JSON çıktı
        report_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "health_report.json"
        )
        report = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_sec": round(elapsed, 1),
            "total": total,
            "passed": passed,
            "failed": failed,
            "no_ep": no_ep,
            "fixed": self._fixed_count,
            "by_type": {t: {"pass": sum(v for k, v in tc.items()
                                       if HealthStatus.is_pass(k)),
                            "fail": sum(v for k, v in tc.items()
                                       if HealthStatus.is_fail(k))}
                        for t, tc in type_cats.items()},
            "by_status": dict(sorted(cats.items())),
            "broken": [
                {"id": r.id, "type": r.type, "title": r.title,
                 "url": r.ep_url, "status": r.status, "detail": r.detail[:200]}
                for r in broken
            ],
            "saved": [
                {"id": r.id, "type": r.type, "title": r.title,
                 "old_url": r.ep_url, "new_url": r.tested_url}
                for r in saved
            ],
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"  Rapor kaydedildi: {report_path}")
        print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(
        description="KuroWatch İçerik Sağlığı Taraması"
    )
    parser.add_argument("--type", choices=["anime", "manga", "manhwa", "game"],
                        help="Sadece belirli tipteki içerikleri tara")
    parser.add_argument("--id", type=int, dest="content_id",
                        help="Sadece belirli ID'deki içeriği tara")
    parser.add_argument("--dead-only", action="store_true",
                        help="Sadece ölü/hatalı URL'leri göster")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Detaylı çıktı")
    parser.add_argument("--fix", action="store_true",
                        help="Kurtarılan URL'leri DB'de güncelle")
    args = parser.parse_args()

    checker = HealthChecker(dead_only=args.dead_only, verbose=args.verbose,
                            fix=args.fix)
    await checker.run(content_type=args.type, content_id=args.content_id)


if __name__ == "__main__":
    asyncio.run(main())
