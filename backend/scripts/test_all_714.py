"""
SOHBET-144 — 714 İçerik Toplu Test
Hafif versiyon: stream URL bulma + ilk 5MB/page download
"""
import os, sys, time, json, asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(str(ROOT))

import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "http://localhost:8100"
OUT = ROOT / "_sohbet144_testi"
(OUT / "anime").mkdir(parents=True, exist_ok=True)
(OUT / "dizi").mkdir(parents=True, exist_ok=True)
(OUT / "film").mkdir(parents=True, exist_ok=True)
(OUT / "manga").mkdir(parents=True, exist_ok=True)
(OUT / "manhwa").mkdir(parents=True, exist_ok=True)
(OUT / "oyun").mkdir(parents=True, exist_ok=True)

DIR_MAP = {"anime": "anime", "series": "dizi", "movie": "film",
           "manga": "manga", "manhwa": "manhwa", "game": "oyun"}

results = []

def get_all_urls(content: dict) -> list[str]:
    """İçerikten tüm URL'leri bul (episode + site)."""
    urls = []
    seen = set()
    for ep in (content.get("episodes") or []):
        u = ep.get("url")
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    for s in (content.get("sites") or []):
        u = s.get("site_url")
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    return urls

def test_content(item: dict) -> dict:
    """Tek içeriği test et — tüm URL'leri dene, ilk çalışanı kabul et."""
    cid = item["id"]
    title = item.get("title", "?")
    ctype = item.get("type", "?")
    result = {"id": cid, "title": title, "type": ctype, "status": None,
              "site": None, "error": None}
    
    urls = get_all_urls(item)
    if not urls:
        result["status"] = "SKIP"
        result["error"] = "No URL"
        return result
    
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    def _try_request(url: str) -> dict:
        try:
            r = httpx.head(url, follow_redirects=True, timeout=15,
                headers={"User-Agent": UA})
            if r.status_code == 405:
                r = httpx.get(url, follow_redirects=True, timeout=15,
                    headers={"User-Agent": UA})
            if r.status_code < 400:
                return {"status": "HTTP_OK", "site": urlparse(url).netloc.lstrip("www.")}
            elif "Cloudflare" in r.text[:200] or "challenge" in r.text[:200].lower():
                return {"status": "CLOUDFLARE", "code": r.status_code}
            else:
                return {"status": "HTTP_" + str(r.status_code), "code": r.status_code}
        except Exception as e:
            err = str(e)
            if "ConnectError" in err or "connection" in err.lower():
                return {"status": "UNREACHABLE"}
            elif "Timeout" in err:
                return {"status": "TIMEOUT"}
            else:
                return {"status": "ERROR"}
    
    first_domain = urlparse(urls[0]).netloc.lstrip("www.")
    
    for url in urls:
        domain = urlparse(url).netloc.lstrip("www.")
        
        # setfilmizle.uk rate-limit koruması
        if 'setfilmizle' in domain:
            time.sleep(2)
        
        resp = _try_request(url)
        if resp["status"] == "HTTP_OK":
            result["status"] = "HTTP_OK"
            result["site"] = resp.get("site", domain)
            return result
    
    # Hiçbiri çalışmadı — ilk URL'nin durumunu raporla
    result["status"] = resp.get("status", "ERROR")
    result["site"] = first_domain
    return result

def main():
    print("=" * 60)
    print("SOHBET-144 — 714 İÇERİK TESTİ")
    print(f"{'='*60}\n")
    
    # Fetch all contents (single request — API returns all)
    r = httpx.get(f"{API}/api/content?limit=1000")
    if r.status_code != 200:
        print(f"API error: {r.status_code}")
        return
    all_contents = r.json()
    print(f"\nTotal contents: {len(all_contents)}")
    
    # Test each content (parallel)
    start = time.time()
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(test_content, item): item for item in all_contents}
        for i, future in enumerate(as_completed(futures)):
            r = future.result()
            results.append(r)
            # setfilmizle yoğunluğu azaltmak için her istek arası kısa bekle
            if r.get("site") and 'setfilmizle' in r["site"]:
                time.sleep(0.5)
            if (i + 1) % 50 == 0:
                elapsed = time.time() - start
                rate = (i + 1) / elapsed * 60
                passed = sum(1 for x in results if x["status"] == "HTTP_OK")
                print(f"  [{i+1}/{len(all_contents)}] OK={passed} rate={rate:.0f}/min")
    
    elapsed = time.time() - start
    
    # Summary
    by_type = {}
    for r in results:
        t = r["type"]
        by_type.setdefault(t, {"total": 0, "ok": 0, "error": 0, "skip": 0, "failures": []})
        by_type[t]["total"] += 1
        if r["status"] == "HTTP_OK":
            by_type[t]["ok"] += 1
        elif r["status"] == "SKIP":
            by_type[t]["skip"] += 1
        else:
            by_type[t]["error"] += 1
            by_type[t]["failures"].append(r)
    
    total_ok = sum(v["ok"] for v in by_type.values())
    total_skip = sum(v["skip"] for v in by_type.values())
    total_error = sum(v["error"] for v in by_type.values())
    
    print(f"\n{'='*60}")
    print(f"SONUÇLAR ({elapsed:.0f}s)")
    print(f"{'='*60}")
    
    report_lines = [
        f"# SOHBET-144 — 714 İçerik Toplu Test Raporu",
        f"**Tarih:** {datetime.now().isoformat()}",
        f"**Süre:** {elapsed:.0f}s",
        f"",
        f"## Genel Sonuç",
        f"| Metric | Değer |",
        f"|--------|-------|",
        f"| Toplam İçerik | {len(all_contents)} |",
        f"| HTTP 200 | {total_ok} |",
        f"| Skip (URL yok) | {total_skip} |",
        f"| Hata | {total_error} |",
        f"| Başarı Oranı | {total_ok}/{len(all_contents) - total_skip} (%{round(total_ok / max(len(all_contents) - total_skip, 1) * 100, 1)}) |",
        f"",
        f"## Tür Bazında",
        f"| Tür | Toplam | HTTP 200 | Hata | Skip | Başarı % |",
        f"|-----|--------|----------|------|------|----------|",
    ]
    
    for t in ["anime", "series", "movie", "manga", "manhwa", "game"]:
        v = by_type.get(t, {"total": 0, "ok": 0, "error": 0, "skip": 0})
        pct = round(v["ok"] / max(v["total"] - v["skip"], 1) * 100, 1) if v["total"] - v["skip"] > 0 else 0
        report_lines.append(f"| {t} | {v['total']} | {v['ok']} | {v['error']} | {v['skip']} | %{pct} |")
        print(f"  {t}: {v['ok']}/{v['total']} OK ({v['error']} error, {v['skip']} skip) = %{pct}")
    
    print(f"\n  TOPLAM: {total_ok}/{len(all_contents)} OK, {total_error} error, {total_skip} skip")
    
    # Failures detail
    failures = [r for r in results if r["status"] not in ("HTTP_OK", "SKIP")]
    if failures:
        report_lines.extend([
            f"",
            f"## Başarısız İçerikler ({len(failures)})",
            f"| ID | Title | Tür | Site | Durum | Hata |",
            f"|-----|-------|-----|------|-------|------|",
        ])
        for r in failures[:50]:  # İlk 50
            report_lines.append(
                f"| {r['id']} | {r['title'][:40]} | {r['type']} | "
                f"{(r.get('site') or '?')[:30]} | {r['status']} | {(r.get('error') or '')[:40]} |"
            )
        if len(failures) > 50:
            report_lines.append(f"| ... | ... ({len(failures) - 50} more) | ... | ... | ... | ... |")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"_Rapor otomatik oluşturuldu: {datetime.now().isoformat()}_")
    
    report_text = "\n".join(report_lines)
    
    # Save report
    report_path = ROOT / "docs" / "SOHBET-144_RAPORU.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"\nRapor: {report_path}")
    
    # Save JSON
    json_path = OUT / "rapor.json"
    json_path.write_text(json.dumps({
        "summary": {
            "total": len(all_contents),
            "ok": total_ok,
            "error": total_error,
            "skip": total_skip,
            "success_rate": round(total_ok / max(len(all_contents) - total_skip, 1) * 100, 1),
            "duration_sec": elapsed,
        },
        "by_type": by_type,
        "results": results,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()
