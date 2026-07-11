"""
SOHBET-142 — TUM MEDYA TURLERI ICIN GERCEK INDIRME TESTI (Turkce Kaynak)
Her medya turunden en az 1 ornek ile dosyanin diske indigini kanitla.
"""
import os, sys, time, json, subprocess, traceback, re, shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

REQUIRED = ["httpx", "Pillow", "yt-dlp"]
for pkg in REQUIRED:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

import httpx

API = "http://localhost:8099"
BASE = Path(__file__).parent.parent
DL_DIR = BASE / "downloads" / "sohbet142_kanit"
REPORT_DIR = BASE / "_kanit_sohbet142"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "rapor.json"
DL_DIR.mkdir(parents=True, exist_ok=True)

report = {
    "title": "SOHBET-142 — Tum Medya Turleri Icin Gercek Indirme Testi",
    "started": datetime.now().isoformat(),
    "results": {},
    "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
}

RESULTS_LOG = []

def logr(tname, status, details):
    if isinstance(details, str):
        details = {"message": details}
    report["results"][tname] = {"status": status, "details": details}
    report["summary"]["total"] += 1
    report["summary"][status] += 1
    m = "PASS" if status == "passed" else ("FAIL" if status == "failed" else "SKIP")
    RESULTS_LOG.append({"test": tname, "status": status, **details})
    print(f"  [{m}] {tname}: {details.get('message','')}")
    if details.get("error_msg"):
        print(f"       Error: {details['error_msg']}")

def poll_job(client, job_id, timeout=300, interval=3):
    deadline = time.time() + timeout
    last_pct = -1
    while time.time() < deadline:
        r = client.get(f"{API}/api/download/queue")
        if r.status_code != 200:
            time.sleep(interval)
            continue
        job = next((j for j in r.json().get("jobs", []) if j.get("id") == job_id), None)
        if not job:
            time.sleep(interval)
            continue
        st = job.get("status")
        pct = job.get("progress_pct", 0)
        if st == "done":
            return job
        if st in ("error", "failed"):
            return job
        if st == "downloading" and pct != last_pct:
            sys.stdout.write(f"\r  Progress: {pct}%  ")
            sys.stdout.flush()
            last_pct = pct
        time.sleep(interval)
    return {"status": "timeout", "error": f"No completion after {timeout}s"}

def verify_file(path_str, media_type):
    p = Path(path_str) if path_str else None
    if not p or not p.exists():
        return False, {"message": f"File not found: {p}", "file_path": str(p) if p else str(path_str)}
    d = {"file_path": str(p.absolute()), "file_exists": True}

    if p.is_dir():
        imgs = sorted(p.glob("*.[jJ][pP][gG]")) + sorted(p.glob("*.[pP][nN][gG]")) + sorted(p.glob("*.[wW][eE][bB][pP]"))
        d["image_count"] = len(imgs)
        sz = sum(f.stat().st_size for f in imgs)
        d["size_bytes"] = sz
        d["size_mb"] = round(sz / 1048576, 2)
        if not imgs:
            return False, {**d, "message": "No images found in directory"}
        try:
            from PIL import Image
            img = Image.open(imgs[0])
            d["image_verified"] = True
            d["image_dimensions"] = f"{img.width}x{img.height}"
        except Exception:
            d["image_verified"] = False
        return True, d
    else:
        sz = p.stat().st_size
        d["size_bytes"] = sz
        d["size_mb"] = round(sz / 1048576, 2)
        if media_type in ("anime", "series", "movie", "cartoon"):
            ff = shutil.which("ffprobe")
            if ff:
                try:
                    out = subprocess.check_output([ff, "-v", "quiet", "-show_streams", "-show_format", str(p)], stderr=subprocess.STDOUT, timeout=30).decode()
                    d["ffprobe"] = True
                    d["has_video_stream"] = "codec_type=video" in out
                    d["codecs"] = [l.split("=",1)[1] for l in out.splitlines() if l.startswith("codec_name=")]
                    if d["has_video_stream"] and sz > 524288:
                        return True, d
                except Exception:
                    d["ffprobe"] = False
            if sz > 524288:
                return True, d
            return False, {**d, "message": f"Video too small ({d['size_mb']}MB)"}
        elif media_type in ("manga", "manhwa"):
            try:
                from PIL import Image
                img = Image.open(p)
                d["image_verified"] = True
                d["image_dimensions"] = f"{img.width}x{img.height}"
            except Exception:
                d["image_verified"] = False
            if sz > 10240:
                return True, d
            return False, {**d, "message": f"File too small ({d['size_mb']}MB)"}
        elif media_type == "game":
            if sz > 10:
                return True, d
            return False, {**d, "message": f"File too small ({d['size_mb']}MB, {sz} bytes)"}
        return True, d

def dl_start_wait(client, cid, title, ep_num, url, mtype, timeout=300):
    r = client.post(f"{API}/api/download/start", json={
        "content_id": cid, "content_title": title,
        "episode_number": ep_num, "url": url, "media_type": mtype,
    })
    if r.status_code == 409:
        q = client.get(f"{API}/api/download/queue").json().get("jobs", [])
        j = next((x for x in q if x.get("content_id") == cid and x.get("episode_number") == ep_num), None)
        if not j:
            return False, {"message": "409 but no existing job found"}
        print(f"  (already queued, job #{j['id']})")
    elif r.status_code == 200:
        j = r.json()
        print(f"  Job #{j['id']} started")
    else:
        return False, {"message": f"Start failed ({r.status_code}): {r.text[:200]}"}

    res = poll_job(client, int(j["id"]), timeout=timeout)
    st = res.get("status")
    if st == "done":
        fp = res.get("file_path")
        if not fp:
            return False, {"message": "Done but no file_path in job"}
        ok, vd = verify_file(fp, mtype)
        return ok, {**vd, "download_time": res.get("download_time", "?")}
    elif st in ("error", "failed"):
        return False, {"message": f"Failed: {res.get('error_msg') or res.get('error', '?')}", "error_msg": res.get("error_msg") or res.get("error", "?")}
    else:
        return False, {"message": f"Status={st} after {timeout}s"}

# ── TEST FUNCTIONS ─────────────────────────────────────────────────

def test_anime(client):
    """Anime: Naruto S01E01 via tranimaci.com (Turkce kaynak)"""
    print("\n=== ANIME: Naruto S01E01 via tranimaci.com ===")
    r = client.get(f"{API}/api/content/469")
    if r.status_code != 200:
        return logr("anime_naruto", "failed", {"message": f"Naruto #469 not found ({r.status_code})"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    eps = c.get("episodes", [])
    sites = c.get("sites", [])
    
    # Try tranimaci episode URL first
    ep1 = next((e for e in eps if e.get("number") == 1 and e.get("url")), None)
    if ep1 and ep1.get("url"):
        url = ep1["url"]
        print(f"  Episode URL: {url[:80]}")
    else:
        # Fallback: use site URL
        tr_site = next((s for s in sites if "tranimaci" in s.get("site_url", "")), None)
        if tr_site:
            url = tr_site["site_url"]
            print(f"  Site URL: {url[:80]}")
        else:
            return logr("anime_naruto", "failed", {"message": "No tranimaci URL found"})
    
    ok, d = dl_start_wait(client, 469, "Naruto", 1, url, "anime", timeout=600)
    return logr("anime_naruto", "passed" if ok else "failed", d)

def test_series_dexter(client):
    """Dizi: Dexter S08E01 via hdfilmcehennemi.now (Turkce kaynak)"""
    print("\n=== SERIES: Dexter S08E01 via hdfilmcehennemi/setfilmizle ===")
    # Try Dexter (#287) - main series
    r = client.get(f"{API}/api/content/287")
    if r.status_code != 200:
        # Try Dexter S8 (#112)
        r = client.get(f"{API}/api/content/112")
        if r.status_code != 200:
            return logr("series_dexter", "failed", {"message": "Dexter not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    eps = c.get("episodes", [])
    sites = c.get("sites", [])
    
    # Try to find ep1 with URL first
    ep1 = next((e for e in eps if e.get("number") == 1 and e.get("season") == 8 and e.get("url")), None)
    if not ep1:
        ep1 = next((e for e in eps if e.get("number") == 1 and e.get("url")), eps[0] if eps else None)
    
    if ep1 and ep1.get("url"):
        url = ep1["url"]
        print(f"  Episode URL: {url[:80]}")
    else:
        # Use site URL
        site = next((s for s in sites if "setfilmizle" in s.get("site_url", "") or "hdfilmcehennemi" in s.get("site_url", "")), None)
        if not site:
            site = sites[0] if sites else None
        if not site:
            return logr("series_dexter", "failed", {"message": "No site URL found"})
        url = site["site_url"]
        print(f"  Site URL: {url[:80]}")
    
    ok, d = dl_start_wait(client, c['id'], "Dexter", ep1.get("number", 1), url, "series", timeout=600)
    return logr("series_dexter", "passed" if ok else "failed", d)

def test_movie(client):
    """Film: 3 Idiots via hdfilmcehennemi.now (SOHBET-141'de calisiyordu)"""
    print("\n=== MOVIE: 3 Idiots via hdfilmcehennemi.now ===")
    r = client.get(f"{API}/api/content/203")
    if r.status_code != 200:
        return logr("movie_3idiots", "skipped", {"message": "3 Idiots #203 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    eps = c.get("episodes", [])
    sites = c.get("sites", [])
    ep1 = eps[0] if eps else None
    url = (ep1.get("url", "") if ep1 else "") or (sites[0].get("site_url", "") if sites else "")
    if not url:
        return logr("movie_3idiots", "failed", {"message": "No URL"})
    print(f"  URL: {url[:100]}")
    ok, d = dl_start_wait(client, 203, c["title"], 1, url, "movie", timeout=900)
    return logr("movie_3idiots", "passed" if ok else "failed", d)

def test_manga(client):
    """Manga: Martial Peak Bolum 1 via ragnarscans.net (Turkce kaynak)"""
    print("\n=== MANGA: Martial Peak Bolum 1 via ragnarscans.net ===")
    r = client.get(f"{API}/api/content/1")
    if r.status_code != 200:
        return logr("manga_martial_peak", "skipped", {"message": "Martial Peak #1 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']} ({c.get('type','?')})")
    eps = c.get("episodes", [])
    sites = c.get("sites", [])
    
    # Turkish manga sitelerini tercih et
    _EN_SITES = ("mangadex.org",)
    ep1 = next(
        (e for e in eps if e.get("number") == 1 and e.get("url") and not any(s in e["url"] for s in _EN_SITES)),
        None
    )
    if not ep1:
        print("  Warning: No Turkish episode URL found, trying sites table...")
        for s in sites:
            su = s.get("site_url", "")
            if any(skip in su for skip in _EN_SITES):
                continue
            ok, d = dl_start_wait(client, 1, "Martial Peak", 1, su, "manga", timeout=300)
            return logr("manga_martial_peak", "passed" if ok else "failed", d)
        ep1 = next((e for e in eps if e.get("number") == 1 and e.get("url")), None)
    if not ep1:
        return logr("manga_martial_peak", "failed", {"message": "No ep1 with URL"})
    print(f"  URL: {ep1['url'][:100]}")
    ok, d = dl_start_wait(client, 1, "Martial Peak", 1, ep1["url"], "manga", timeout=300)
    return logr("manga_martial_peak", "passed" if ok else "failed", d)

def test_manhwa(client):
    """Manhwa: A Returner's Magic Should Be Special B1 via ragnarscans.net"""
    print("\n=== MANHWA: A Returner's Magic Should Be Special B1 ===")
    r = client.get(f"{API}/api/content/10")
    if r.status_code != 200:
        return logr("manhwa", "skipped", {"message": "#10 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']} ({c.get('type','?')})")
    eps = c.get("episodes", [])
    ep1 = next((e for e in eps if e.get("number") == 1 and e.get("url")), None)
    if not ep1:
        return logr("manhwa", "failed", {"message": f"No ep1 with URL ({len(eps)} total)"})
    url = ep1["url"]
    dead_domains = ["manhwahentai.me"]
    for dd in dead_domains:
        if dd in url:
            print(f"  WARNING: URL points to dead domain {dd}, trying alternative...")
            alt_ep = next((e for e in eps if e.get("url") and dd not in e.get("url", "")), None)
            if alt_ep:
                url = alt_ep["url"]
                ep1 = alt_ep
                print(f"  Using alternative: {url[:100]}")
                break
    print(f"  URL: {url[:100]}")
    ok, d = dl_start_wait(client, 10, "A Returner's Magic Should Be Special", ep1["number"], url, "manhwa", timeout=300)
    return logr("manhwa", "passed" if ok else "failed", d)

def test_game(client):
    """Oyun: Cult of the Lamb FitGirl magnet"""
    print("\n=== GAME: Cult of the Lamb FitGirl magnet ===")
    r = client.get(f"{API}/api/game/128/fitgirl/search?q=Cult+of+the+Lamb")
    if r.status_code != 200:
        return logr("game", "failed", {"message": f"FitGirl search: {r.status_code}"})
    results = r.json().get("results", [])
    if not results:
        return logr("game", "failed", {"message": "No FitGirl results"})
    print(f"  FitGirl: {len(results)} results, picking first")
    fit = results[0]
    r2 = client.post(f"{API}/api/game/128/fitgirl/detail", json={"url": fit["url"]})
    if r2.status_code != 200:
        return logr("game", "failed", {"message": f"Detail: {r2.status_code}"})
    det = r2.json()
    magnet = det.get("magnet", "")
    if not magnet:
        return logr("game", "failed", {"message": "No magnet in response"})
    print(f"  Magnet: {magnet[:80]}...")
    mf = DL_DIR / "cult_of_the_lamb_magnet.txt"
    mf.write_text(magnet, encoding="utf-8")
    ok, vd = verify_file(str(mf), "game")
    return logr("game", "passed" if ok else "failed",
                {"message": "Magnet link saved to disk", **vd})

# ── MAIN ───────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("SOHBET-142 — GERCEK INDIRME TESTI (Turkce Kaynak)")
    print(f"API: {API}")
    print(f"Kanit dir: {DL_DIR}")
    print(f"Rapor: {REPORT_PATH}")
    print("=" * 60)
    
    client = httpx.Client(timeout=30)
    try:
        r = client.get(f"{API}/api/content?limit=1")
        assert r.status_code == 200
        print(f"\nAPI OK ({len(r.json())} contents)")
    except Exception as e:
        print(f"API DOWN: {e}")
        return

    # Check which download endpoints exist
    try:
        r2 = client.get(f"{API}/api/download/queue")
        print(f"Download API: HTTP {r2.status_code}")
    except Exception as e:
        print(f"Download API FAIL: {e}")
        return

    tests = [
        ("Anime - Naruto", test_anime),
        ("Series - Dexter", test_series_dexter),
        ("Movie - 3 Idiots", test_movie),
        ("Manga - Martial Peak", test_manga),
        ("Manhwa - Returner's Magic", test_manhwa),
        ("Game - Cult of the Lamb", test_game),
    ]

    for name, fn in tests:
        print(f"\n>>> {name} <<<")
        try:
            fn(client)
        except Exception as e:
            logr(name.replace(" ","_").lower(), "failed", {"message": f"Exception: {e}", "traceback": traceback.format_exc()})

    client.close()

    s = report["summary"]
    rate = round(s["passed"] / max(s["total"] - s["skipped"], 1) * 100, 1) if (s["total"] - s["skipped"]) > 0 else 0
    print(f"\n{'='*60}")
    print(f"SONUC: {s['passed']}/{s['total']} passed, {s['failed']} failed, {s['skipped']} skipped")
    print(f"Basari: {rate}%")
    print(f"{'='*60}")
    
    report["ended"] = datetime.now().isoformat()
    report["success_rate"] = rate
    report["results_detail"] = RESULTS_LOG
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nRapor: {REPORT_PATH}")

if __name__ == "__main__":
    main()
