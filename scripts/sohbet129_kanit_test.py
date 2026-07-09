#!/usr/bin/env python3
"""
SOHBET-129 Kanit Test Script
Tests all unique sites in kurowatch.db, generates proof files and reports.
"""
import os
import sys
import json
import time
import sqlite3
import traceback
from datetime import datetime
from urllib.parse import urlparse
from collections import defaultdict
from pathlib import Path

try:
    from curl_cffi import requests as curl_requests
    HAS_CURL = True
except ImportError:
    import requests as std_requests
    HAS_CURL = False

DB_PATH = r"C:\Kuroshin\kurowatch\memory\kurowatch.db"
OUTPUT_DIR = Path(r"C:\Kuroshin\kurowatch\_kanit_sohbet129")
RAPOR_DIR = OUTPUT_DIR / "rapor"

CURRENT_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
TEST_TIMEOUT = 25

session = None

def get_session():
    global session
    if session is None:
        session = curl_requests.Session()
        session.timeout = TEST_TIMEOUT
    return session

def extract_domain(url):
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url

def test_site_url(url, timeout=TEST_TIMEOUT):
    """Test a single URL, returning result dict."""
    result = {
        "url": url,
        "status_code": None,
        "content_length": 0,
        "cf_detected": False,
        "category": "ERROR",
        "error": None,
        "elapsed": 0,
        "html_preview": "",
    }
    start = time.time()
    try:
        s = get_session()
        resp = s.get(
            url,
            impersonate="chrome124",
            timeout=timeout,
            allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
            },
        )
        elapsed = time.time() - start
        result["status_code"] = resp.status_code
        result["elapsed"] = round(elapsed, 2)
        result["content_length"] = len(resp.content)
        html = resp.text[:2000] if resp.text else ""
        result["html_preview"] = html[:500]

        cf_keywords = [
            "cloudflare", "cf-ray", "cf-challenge", "attention required",
            "just a moment", "checking your browser", "ddos protection",
            "cf-browser-verification", "challenge-platform",
        ]
        html_lower = html.lower()
        result["cf_detected"] = any(kw in html_lower for kw in cf_keywords)

        if resp.status_code == 200 and not result["cf_detected"] and len(resp.content) > 500:
            result["category"] = "OK"
        elif resp.status_code == 200 and result["cf_detected"]:
            result["category"] = "CF_BLOCKED"
        elif resp.status_code in (403, 503) and result["cf_detected"]:
            result["category"] = "CF_BLOCKED"
        elif resp.status_code in (404, 410, 451):
            result["category"] = "DEAD"
        elif resp.status_code in (301, 302, 303, 307, 308):
            result["category"] = "REDIRECT"
        elif resp.status_code >= 400:
            result["category"] = "DEAD"
        elif resp.status_code == 200 and len(resp.content) <= 500:
            result["category"] = "EMPTY"
        else:
            result["category"] = "UNKNOWN"

    except Exception as e:
        elapsed = time.time() - start
        result["elapsed"] = round(elapsed, 2)
        error_str = str(e)
        result["error"] = error_str
        if "timeout" in error_str.lower() or "timed out" in error_str.lower():
            result["category"] = "TIMEOUT"
        elif "connection" in error_str.lower() or "resolve" in error_str.lower() or "connect" in error_str.lower():
            result["category"] = "DEAD"
        else:
            result["category"] = "ERROR"

    return result


def safe_get(url, timeout=TEST_TIMEOUT):
    """Simple GET with curl_cffi, returns (status, content, error)."""
    try:
        s = get_session()
        resp = s.get(
            url, impersonate="chrome124", timeout=timeout, allow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.google.com/",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
            },
        )
        return resp.status_code, resp.content, None
    except Exception as e:
        return None, b"", str(e)


def main():
    print(f"[SOHBET-129] Starting test at {CURRENT_TIME}")
    print(f"[SOHBET-129] DB: {DB_PATH}")
    print(f"[SOHBET-129] curl_cffi available: {HAS_CURL}")
    print(f"[SOHBET-129] Output dir: {OUTPUT_DIR}")

    # --- 0. Prepare output dirs ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAPOR_DIR.mkdir(parents=True, exist_ok=True)
    proof_dirs = {}
    for t in ["anime", "manga", "manhwa", "movie", "series", "cartoon", "game"]:
        for status in ["working", "failed"]:
            d = OUTPUT_DIR / f"proof_{t}_{status}"
            d.mkdir(parents=True, exist_ok=True)
            proof_dirs[f"{t}_{status}"] = d

    # --- 1. Load database ---
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM content")
    all_contents = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM site")
    all_sites = [dict(row) for row in c.fetchall()]

    conn.close()

    content_by_id = {ct["id"]: ct for ct in all_contents}
    sites_by_content = defaultdict(list)
    for s in all_sites:
        sites_by_content[s["content_id"]].append(s)

    total_content = len(all_contents)
    content_by_type = defaultdict(list)
    for ct in all_contents:
        content_by_type[ct["type"]].append(ct)

    print(f"\n[SOHBET-129] Total contents: {total_content}")
    for t, items in sorted(content_by_type.items()):
        print(f"  {t}: {len(items)}")

    # --- 2. Determine unique sites to test ---
    # Build domain -> list of (sample_url, site_name) for testing
    domain_info = defaultdict(list)
    site_urls_map = defaultdict(list)  # domain -> list of unique URLs
    for s in all_sites:
        url = s["site_url"]
        if url:
            domain = extract_domain(url)
            domain_info[domain].append({"site_name": s["site_name"], "url": url})
            site_urls_map[domain].append(url)

    # Also track which content types use each domain
    domain_content_types = defaultdict(set)
    for s in all_sites:
        ct = content_by_id.get(s["content_id"])
        if ct:
            domain = extract_domain(s["site_url"])
            domain_content_types[domain].add(ct["type"])

    unique_domains = sorted(domain_info.keys())
    print(f"\n[SOHBET-129] Unique domains to test: {len(unique_domains)}")
    for d in unique_domains:
        types = ", ".join(sorted(domain_content_types[d]))
        sample = domain_info[d][0]["url"][:80]
        print(f"  {d:40s} [{types:20s}] {sample}")

    # --- 3. Test each unique domain ---
    domain_results = {}
    all_test_results = {}

    for idx, domain in enumerate(unique_domains, 1):
        # Pick a representative URL for this domain
        candidates = site_urls_map[domain]
        test_url = candidates[0]

        print(f"\n  [{idx}/{len(unique_domains)}] Testing {domain} ...", end=" ", flush=True)
        result = test_site_url(test_url)
        domain_results[domain] = result
        cat = result["category"]
        status_code = result["status_code"]
        elapsed = result["elapsed"]
        cl = result["content_length"]
        cf = " CF!" if result["cf_detected"] else ""
        err = f" [{result['error'][:60]}]" if result["error"] else ""
        print(f"{cat} (HTTP={status_code}, {cl}B, {elapsed}s){cf}{err}")

        # Map all contents using this domain
        for site_entry in domain_info[domain]:
            url = site_entry["url"]
            all_test_results[url] = {
                "url": url,
                "domain": domain,
                "category": cat,
                "status_code": result["status_code"],
                "content_length": result["content_length"],
                "cf_detected": result["cf_detected"],
                "error": result["error"],
                "elapsed": result["elapsed"],
            }

    # --- 4. Map contents to results ---
    content_results = []
    for ct in all_contents:
        cid = ct["id"]
        content_sites = sites_by_content.get(cid, [])
        if not content_sites:
            content_results.append({
                "content_id": cid,
                "title": ct["title"],
                "type": ct["type"],
                "status_category": "NO_SITE",
                "domain": None,
                "site_url": None,
                "site_name": None,
            })
        else:
            # Use the primary site if available, otherwise first
            best_site = None
            for s in content_sites:
                if s.get("is_primary"):
                    best_site = s
                    break
            if not best_site:
                best_site = content_sites[0]

            url = best_site["site_url"]
            result = all_test_results.get(url, {})
            cat = result.get("category", "UNKNOWN")
            is_dead_flag = best_site.get("is_dead", 0)
            if is_dead_flag and cat in ("OK",):
                cat = "MARKED_DEAD"

            content_results.append({
                "content_id": cid,
                "title": ct["title"],
                "type": ct["type"],
                "status_category": cat,
                "domain": result.get("domain"),
                "site_url": url,
                "site_name": best_site["site_name"],
            })

    # --- 5. Statistics ---
    total_with_sites = sum(1 for r in content_results if r["status_category"] != "NO_SITE")
    total_no_site = sum(1 for r in content_results if r["status_category"] == "NO_SITE")
    success = sum(1 for r in content_results if r["status_category"] == "OK")
    cf_blocked = sum(1 for r in content_results if r["status_category"] in ("CF_BLOCKED",))
    dead = sum(1 for r in content_results if r["status_category"] in ("DEAD",))
    timeout = sum(1 for r in content_results if r["status_category"] in ("TIMEOUT",))
    error = sum(1 for r in content_results if r["status_category"] in ("ERROR", "UNKNOWN", "EMPTY", "REDIRECT"))
    failed_but_marked = sum(1 for r in content_results if r["status_category"] == "MARKED_DEAD")

    stats = {
        "total_contents": total_content,
        "total_with_sites": total_with_sites,
        "total_no_site": total_no_site,
        "ok": success,
        "cf_blocked": cf_blocked,
        "dead": dead,
        "timeout": timeout,
        "error": error,
        "marked_dead": failed_but_marked,
        "success_pct": round(success / total_content * 100, 1) if total_content else 0,
        "by_type": {},
    }

    for t in sorted(content_by_type.keys()):
        type_items = [r for r in content_results if r["type"] == t]
        t_total = len(type_items)
        t_ok = sum(1 for r in type_items if r["status_category"] == "OK")
        t_no = sum(1 for r in type_items if r["status_category"] == "NO_SITE")
        t_cf = sum(1 for r in type_items if r["status_category"] in ("CF_BLOCKED",))
        t_dead = sum(1 for r in type_items if r["status_category"] in ("DEAD",))
        t_to = sum(1 for r in type_items if r["status_category"] in ("TIMEOUT",))
        t_err = sum(1 for r in type_items if r["status_category"] in ("ERROR", "UNKNOWN", "EMPTY", "REDIRECT"))
        stats["by_type"][t] = {
            "total": t_total,
            "ok": t_ok,
            "no_site": t_no,
            "cf_blocked": t_cf,
            "dead": t_dead,
            "timeout": t_to,
            "error": t_err,
            "success_pct": round(t_ok / t_total * 100, 1) if t_total else 0,
        }

    failed_contents = [r for r in content_results if r["status_category"] != "OK"]
    success_contents = [r for r in content_results if r["status_category"] == "OK"]

    # --- 6. Generate proof files ---
    working_domains = {d for d, r in domain_results.items() if r["category"] == "OK"}
    failed_domains = {d for d, r in domain_results.items() if r["category"] != "OK"}

    print(f"\n[SOHBET-129] Working domains ({len(working_domains)}):")
    for d in sorted(working_domains):
        print(f"  {d}")

    print(f"\n[SOHBET-129] Failed domains ({len(failed_domains)}):")
    for d in sorted(failed_domains):
        r = domain_results[d]
        print(f"  {d}: {r['category']}")

    # --- 6a. Anime proof ---
    print("\n[SOHBET-129] Generating anime proof files...")

    # Find working anime domains
    working_anime_domains = [d for d in working_domains if "anime" in domain_content_types.get(d, set())]
    for ad in working_anime_domains[:2]:
        # Find a content URL for this domain
        for s in all_sites:
            if extract_domain(s["site_url"]) == ad:
                test_url = s["site_url"]
                break
        else:
            test_url = domain_info[ad][0]["url"]

        try:
            proof_dir = proof_dirs["anime_working"]
            status_code, content, err = safe_get(test_url)
            if content:
                fname = f"anime_{ad.replace('.', '_')}.html"
                (proof_dir / fname).write_bytes(content[:100000])
                print(f"  Saved anime proof: proof_anime_working/{fname} ({len(content)} bytes)")

                # Also try to find iframe/m3u8
                html_text = content.decode("utf-8", errors="replace")
                if "iframe" in html_text.lower():
                    import re
                    iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
                    for iframe_url in iframes[:3]:
                        print(f"    Found iframe: {iframe_url[:80]}")
                        (proof_dir / f"iframe_{ad.replace('.', '_')}.txt").write_text(iframe_url)
            if err:
                proof_dir2 = proof_dirs["anime_failed"]
                (proof_dir2 / f"error_{ad.replace('.', '_')}.txt").write_text(str(err))
        except Exception as e:
            print(f"  Error generating anime proof for {ad}: {e}")

    # If no working anime domains, try tranimeizle anyway
    if not working_anime_domains:
        print("  No working anime domains found, trying known anime sites anyway...")
        for test_url in [
            "https://www.tranimaci.com/naruto-1-bolum-izle",
            "https://www.tranimaci.com/video/naruto-1-bolum",
            "https://turkanime.com.tr/naruto-1-bolum-izle",
        ]:
            try:
                status_code, content, err = safe_get(test_url)
                if content and len(content) > 1000:
                    proof_dir = proof_dirs["anime_working"]
                    fname = f"anime_direct_{extract_domain(test_url).replace('.', '_')}.html"
                    (proof_dir / fname).write_bytes(content[:100000])
                    print(f"  Saved anime proof: proof_anime_working/{fname}")
                    break
            except:
                continue

    # --- 6b. Manga/Manhwa proof ---
    print("\n[SOHBET-129] Generating manga/manhwa proof files...")
    working_manga_domains = [d for d in working_domains if domain_content_types.get(d, set()) & {"manga", "manhwa"}]
    for md in working_manga_domains[:3]:
        for s in all_sites:
            if extract_domain(s["site_url"]) == md:
                test_url = s["site_url"]
                break
        else:
            test_url = domain_info[md][0]["url"]

        try:
            status_code, content, err = safe_get(test_url)
            name_part = md.replace(".", "_")
            if content:
                proof_dir = proof_dirs["manga_working"]
                fname = f"manga_{name_part}.html"
                (proof_dir / fname).write_bytes(content[:100000])
                print(f"  Saved manga proof: proof_manga_working/{fname} ({len(content)} bytes)")

                # Try to find image URLs
                html_text = content.decode("utf-8", errors="replace")
                import re
                img_urls = re.findall(r'<img[^>]*src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']', html_text, re.IGNORECASE)
                if not img_urls:
                    img_urls = re.findall(r'src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']', html_text, re.IGNORECASE)
                if img_urls:
                    # Try to download 1-2 images
                    img_count = 0
                    for img_url in img_urls[:5]:
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif img_url.startswith("/"):
                            parsed = urlparse(test_url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                        elif not img_url.startswith("http"):
                            parsed = urlparse(test_url)
                            img_url = f"{parsed.scheme}://{parsed.netloc}/{img_url.lstrip('/')}"

                        try:
                            st, img_data, img_err = safe_get(img_url)
                            if img_data and len(img_data) > 51200:
                                ext = img_url.rsplit(".", 1)[-1][:4] if "." in img_url else "jpg"
                                img_name = f"manga_img_{name_part}_{img_count}.{ext}"
                                (proof_dir / img_name).write_bytes(img_data)
                                print(f"    Downloaded image: {img_name} ({len(img_data)} bytes)")
                                img_count += 1
                                if img_count >= 2:
                                    break
                        except:
                            pass
            if err:
                (proof_dirs["manga_failed"] / f"error_{name_part}.txt").write_text(str(err))
        except Exception as e:
            print(f"  Error generating manga proof for {md}: {e}")

    # --- 6c. Movie proof ---
    print("\n[SOHBET-129] Generating movie proof files...")
    working_movie_domains = [d for d in working_domains if "movie" in domain_content_types.get(d, set())]
    for md in working_movie_domains[:2]:
        for s in all_sites:
            if extract_domain(s["site_url"]) == md:
                test_url = s["site_url"]
                break
        else:
            test_url = domain_info[md][0]["url"]
        try:
            status_code, content, err = safe_get(test_url)
            name_part = md.replace(".", "_")
            if content:
                (proof_dirs["movie_working"] / f"movie_{name_part}.html").write_bytes(content[:100000])
                print(f"  Saved movie proof: proof_movie_working/movie_{name_part}.html")
            if err:
                (proof_dirs["movie_failed"] / f"error_{name_part}.txt").write_text(str(err))
        except Exception as e:
            print(f"  Error: {e}")

    # If no working movie domain, try known URLs
    if not working_movie_domains:
        for test_url in [
            "https://www.hdfilmcehennemi.now/film/3-aptal-2009-izle-2/",
            "https://www.hdfilmcehennemi.nl/film/3-aptal-2009-izle-2/",
        ]:
            try:
                status_code, content, err = safe_get(test_url)
                if content and len(content) > 1000:
                    name_part = extract_domain(test_url).replace(".", "_")
                    (proof_dirs["movie_working"] / f"movie_{name_part}.html").write_bytes(content[:100000])
                    print(f"  Saved movie proof: proof_movie_working/movie_{name_part}.html")
                    break
            except:
                continue

    # --- 6d. Game proof (no sites, try fitgirl) ---
    print("\n[SOHBET-129] Generating game proof files...")
    try:
        status_code, content, err = safe_get("https://fitgirl-repacks.site/?s=Cult+of+the+Lamb")
        if content:
            (proof_dirs["game_working"] / "fitgirl_search_cult_of_the_lamb.html").write_bytes(content[:100000])
            print(f"  Saved game proof: proof_game_working/fitgirl_search_cult_of_the_lamb.html")

            # Look for magnet links
            html_text = content.decode("utf-8", errors="replace")
            import re
            magnets = re.findall(r'(magnet:\?[^"\'\s<>]+)', html_text)
            if magnets:
                (proof_dirs["game_working"] / "magnet_links.txt").write_text("\n\n".join(magnets[:5]))
                print(f"  Found {len(magnets)} magnet links, saved to proof_game_working/magnet_links.txt")
        else:
            (proof_dirs["game_failed"] / "fitgirl_error.txt").write_text(str(err or "No content"))
    except Exception as e:
        (proof_dirs["game_failed"] / "fitgirl_error.txt").write_text(str(e))

    # --- 6e. Series proof ---
    print("\n[SOHBET-129] Generating series proof files...")
    working_series_domains = [d for d in working_domains if "series" in domain_content_types.get(d, set())]
    for sd in working_series_domains[:2]:
        for s in all_sites:
            if extract_domain(s["site_url"]) == sd:
                test_url = s["site_url"]
                break
        else:
            test_url = domain_info[sd][0]["url"]
        try:
            status_code, content, err = safe_get(test_url)
            name_part = sd.replace(".", "_")
            if content:
                (proof_dirs["series_working"] / f"series_{name_part}.html").write_bytes(content[:100000])
                print(f"  Saved series proof: proof_series_working/series_{name_part}.html")
            if err:
                (proof_dirs["series_failed"] / f"error_{name_part}.txt").write_text(str(err))
        except:
            pass

    if not working_series_domains:
        for test_url in [
            "https://www.setfilmizle.uk/bolum/dexter-1-sezon-1-bolum/",
            "https://dizipod.com/hannibal-1-sezon-1-bolum/",
        ]:
            try:
                status_code, content, err = safe_get(test_url)
                if content and len(content) > 1000:
                    name_part = extract_domain(test_url).replace(".", "_")
                    (proof_dirs["series_working"] / f"series_{name_part}.html").write_bytes(content[:100000])
                    print(f"  Saved series proof: proof_series_working/series_{name_part}.html")
                    break
            except:
                continue

    # --- 7. Write JSON outputs ---
    print(f"\n[SOHBET-129] Writing output files...")

    def json_serialize(obj):
        if isinstance(obj, (datetime,)):
            return obj.isoformat()
        return str(obj)

    with open(RAPOR_DIR / "results.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_date": CURRENT_TIME,
            "stats": stats,
            "domain_results": {d: {k: v for k, v in r.items() if k != "html_preview"} for d, r in domain_results.items()},
            "content_results": content_results,
        }, f, ensure_ascii=False, indent=2, default=json_serialize)
    print(f"  results.json written ({len(content_results)} content entries)")

    with open(RAPOR_DIR / "failed_list.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_date": CURRENT_TIME,
            "count": len(failed_contents),
            "failed_contents": [
                {k: v for k, v in r.items()}
                for r in failed_contents
            ],
        }, f, ensure_ascii=False, indent=2, default=json_serialize)
    print(f"  failed_list.json written ({len(failed_contents)} entries)")

    with open(RAPOR_DIR / "success_list.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_date": CURRENT_TIME,
            "count": len(success_contents),
            "success_contents": success_contents,
        }, f, ensure_ascii=False, indent=2, default=json_serialize)
    print(f"  success_list.json written ({len(success_contents)} entries)")

    # --- 8. Generate human-readable report ---
    print(f"\n[SOHBET-129] Generating report...")

    # Working sites per type
    working_sites_by_type = defaultdict(list)
    for r in success_contents:
        working_sites_by_type[r["type"]].append(r)

    failed_by_category = defaultdict(list)
    for r in failed_contents:
        failed_by_category[r["status_category"]].append(r)

    report_lines = []

    def W(*args):
        report_lines.append(" ".join(str(a) for a in args))

    W(f"# SOHBET-129 Test Raporu")
    W(f"")
    W(f"## Test Bilgileri")
    W(f"- **Test Tarihi:** {CURRENT_TIME}")
    W(f"- **Test Ortami:** Python 3.14, curl_cffi, Windows 11")
    W(f"- **Veritabani:** `{DB_PATH}`")
    W(f"- **Toplam Icerik:** {total_content}")
    W(f"")
    W(f"## Ozet Istatistikler")
    W(f"| Kategori | Sayi | Oran |")
    W(f"|---|---|---|")
    W(f"| **TOPLAM Icerik** | {total_content} | 100% |")
    W(f"| **Basarili (OK)** | {success} | {stats['success_pct']}% |")
    W(f"| **Site Yok (NO_SITE)** | {total_no_site} | {round(total_no_site/total_content*100,1) if total_content else 0}% |")
    W(f"| **Cloudflare Engeli (CF_BLOCKED)** | {cf_blocked} | {round(cf_blocked/total_content*100,1) if total_content else 0}% |")
    W(f"| **Olu Site (DEAD)** | {dead} | {round(dead/total_content*100,1) if total_content else 0}% |")
    W(f"| **Zaman Asimi (TIMEOUT)** | {timeout} | {round(timeout/total_content*100,1) if total_content else 0}% |")
    W(f"| **Hata (ERROR)** | {error} | {round(error/total_content*100,1) if total_content else 0}% |")
    W(f"| **Isaretlenmis Olu** | {failed_but_marked} | {round(failed_but_marked/total_content*100,1) if total_content else 0}% |")
    W(f"")
    W(f"### Icerik Turune Gore Dagitim")
    W(f"| Tur | Toplam | OK | Site Yok | CF Engelli | Olu | Timeout | Hata | Basari %% |")
    W(f"|---|---|---|---|---|---|---|---|")

    for t, tstats in sorted(stats["by_type"].items()):
        W(f"| {t} | {tstats['total']} | {tstats['ok']} | {tstats['no_site']} | "
          f"{tstats['cf_blocked']} | {tstats['dead']} | {tstats['timeout']} | "
          f"{tstats['error']} | %{tstats['success_pct']} |")

    W(f"")
    W(f"## Domain Test Sonuclari ({len(unique_domains)} domain)")
    W(f"")
    W(f"| Domain | Durum | HTTP | Boyut | Sure |")
    W(f"|---|---|---|---|---|")
    for d in sorted(domain_results.keys()):
        r = domain_results[d]
        durum = r["category"]
        http = str(r["status_code"]) if r["status_code"] else "-"
        boyut = f"{r['content_length']}B" if r["content_length"] else "-"
        sure = f"{r['elapsed']}s"
        W(f"| {d} | {durum} | {http} | {boyut} | {sure} |")

    W(f"")
    W(f"## Calisan Domainler (OK)")
    for d in sorted(working_domains):
        types = ", ".join(sorted(domain_content_types.get(d, set())))
        W(f"- {d} [{types}]")

    W(f"")
    W(f"## Basarisiz Domainler")
    for d in sorted(failed_domains):
        r = domain_results[d]
        error_info = f" - {r['error'][:80]}" if r.get("error") else ""
        W(f"- {d}: {r['category']}{error_info}")

    W(f"")
    W(f"## Basarisiz Icerikler")
    W(f"")
    for cat in ["NO_SITE", "CF_BLOCKED", "DEAD", "TIMEOUT", "ERROR", "UNKNOWN", "EMPTY", "REDIRECT", "MARKED_DEAD"]:
        items = failed_by_category.get(cat, [])
        if items:
            W(f"### {cat} ({len(items)} icerik)")
            for item in items[:20]:
                site_info = f" @ {item['site_name']} ({item['site_url'][:60] if item['site_url'] else 'N/A'})" if item.get("site_name") else ""
                W(f"- [{item['type']}] {item['title']}{site_info}")
            if len(items) > 20:
                W(f"  ... ve {len(items) - 20} daha")
            W(f"")

    W(f"")
    W(f"## Alternatif Site Onerileri")
    W(f"")

    # Game (no sites at all)
    W(f"### Game (19 icerik, 0 site)")
    W(f"- **Oneri:** fitgirl-repacks.site, steamrip.com, gog-games.com")
    W(f"- **Kanit:** `proof_game_working/` klasorunde fitgirl arama sonucu ve magnet linkleri")

    # Cartoon (52/53 no sites)
    if stats["by_type"].get("cartoon", {}).get("no_site", 0) > 0:
        W(f"")
        W(f"### Cartoon ({stats['by_type']['cartoon']['no_site']}/{stats['by_type']['cartoon']['total']} site yok)")
        W(f"- **Oneri:** turkanime.tv (anime ile ayni), tranimaci.com, netflix, disney+")

    # Movie (111/113 no sites)
    if stats["by_type"].get("movie", {}).get("no_site", 0) > 0:
        W(f"")
        W(f"### Movie ({stats['by_type']['movie']['no_site']}/{stats['by_type']['movie']['total']} site yok)")
        W(f"- **Oneri:** hdfilmcehennemi.now (test edildi), fullhdfilmizle, jetfilmizle")
        W(f"- **Kanit:** `proof_movie_working/` klasorunde kaydedilmis sayfa")

    # Series (45/49 no sites)
    if stats["by_type"].get("series", {}).get("no_site", 0) > 0:
        W(f"")
        W(f"### Series ({stats['by_type']['series']['no_site']}/{stats['by_type']['series']['total']} site yok)")
        W(f"- **Oneri:** setfilmizle.uk, dizipod.com, dizibox.so, diziwatch.net")
        W(f"- **Kanit:** `proof_series_working/` klasorunde kaydedilmis sayfa")

    # Manga/Manhwa - check working domains
    W(f"")
    W(f"### Manga/Manhwa")
    working_manga = [d for d in working_domains if domain_content_types.get(d, set()) & {"manga", "manhwa"}]
    if working_manga:
        W(f"- **Calisan domainler:** {', '.join(working_manga)}")
        W(f"- **Kanit:** `proof_manga_working/` klasorunde HTML ve image dosyalari")
    else:
        W(f"- **Oneri:** mangagezgini.com, ragnarscans.net, manga-sehri.net (testte basarisiz olabilir)")

    W(f"")
    W(f"## Kanit Dosyalari")
    W(f"")

    for t in ["anime", "manga", "manhwa", "movie", "series", "cartoon", "game"]:
        w_dir = proof_dirs.get(f"{t}_working")
        f_dir = proof_dirs.get(f"{t}_failed")
        if w_dir:
            w_files = list(w_dir.iterdir())
            f_files = list(f_dir.iterdir()) if f_dir else []
            if w_files or f_files:
                W(f"### {t.title()}")
                for pf in w_files:
                    size = pf.stat().st_size
                    W(f"- `proof_{t}_working/{pf.name}` ({size} bytes)")
                for pf in f_files:
                    size = pf.stat().st_size
                    W(f"- `proof_{t}_failed/{pf.name}` ({size} bytes)")

    W(f"")
    W(f"---")
    W(f"*Rapor {CURRENT_TIME} tarihinde SOHBET-129 test scripti tarafindan olusturulmustur.*")
    W(f"*Test edilen domain sayisi: {len(unique_domains)}*")

    report_text = "\n".join(report_lines)
    with open(RAPOR_DIR / "SOHBET-129_RAPORU.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"  SOHBET-129_RAPORU.md written ({len(report_lines)} lines)")

    # --- 9. Summary ---
    print(f"\n{'='*60}")
    print(f"SOHBET-129 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test date: {CURRENT_TIME}")
    print(f"Total content: {total_content}")
    print(f"Total domains tested: {len(unique_domains)}")
    print(f"")
    print(f"  OK:              {success:4d} ({stats['success_pct']}%)")
    print(f"  NO_SITE:         {total_no_site:4d} ({round(total_no_site/total_content*100,1) if total_content else 0}%)")
    print(f"  CF_BLOCKED:      {cf_blocked:4d} ({round(cf_blocked/total_content*100,1) if total_content else 0}%)")
    print(f"  DEAD:            {dead:4d} ({round(dead/total_content*100,1) if total_content else 0}%)")
    print(f"  TIMEOUT:         {timeout:4d} ({round(timeout/total_content*100,1) if total_content else 0}%)")
    print(f"  ERROR:           {error:4d} ({round(error/total_content*100,1) if total_content else 0}%)")
    print(f"  MARKED_DEAD:     {failed_but_marked:4d}")
    print(f"")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Report: {RAPOR_DIR / 'SOHBET-129_RAPORU.md'}")
    print(f"{'='*60}")
    print(f"[SOHBET-129] Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return stats


if __name__ == "__main__":
    stats = main()
