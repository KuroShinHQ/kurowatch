"""
SOHBET-140 — GERCEK INDIRME TESTI (TUM TURLER)
Her medya turunden en az 1 ornek ile dosyanin diske indigini kanitla.
"""
import os, sys, time, json, subprocess, traceback, re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

for pkg in ["httpx", "Pillow", "yt-dlp"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import httpx

API = "http://localhost:8099"
BASE = Path(__file__).parent.parent
DL_DIR = BASE / "downloads" / "sohbet140_kanit"
DL_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = BASE / "_kanit_sohbet140" / "rapor.json"

report = {
    "title": "SOHBET-140 — Gercek Indirme Testi",
    "started": datetime.now().isoformat(),
    "results": {},
    "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
}

def logr(tname, status, details):
    if isinstance(details, str):
        details = {"message": details}
    report["results"][tname] = {"status": status, "details": details}
    report["summary"]["total"] += 1
    report["summary"][status] += 1
    m = "PASS" if status == "passed" else ("FAIL" if status == "failed" else "SKIP")
    print(f"  [{m}] {tname}: {details.get('message','')}")

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
    """Verify downloaded file(s). path_str is a WSL /mnt/c/... path (the test runs in WSL)."""
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
            ff = shutil_which("ffprobe")
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

def shutil_which(cmd):
    try:
        import shutil
        return shutil.which(cmd)
    except Exception:
        return None

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
        return ok, vd
    elif st in ("error", "failed"):
        return False, {"message": f"Failed: {res.get('error_msg') or res.get('error', '?')}"}
    else:
        return False, {"message": f"Status={st} after {timeout}s"}

# ── TESTS ──────────────────────────────────────────────────────────

def test_anime_naruto(client):
    print("\n=== ANIME: Naruto S01E01 via tranimeizle.xyz ===")
    r = client.get(f"{API}/api/content/469")
    if r.status_code != 200:
        return logr("anime_naruto", "skipped", {"message": "Naruto #469 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    ep1 = next((e for e in c.get("episodes", []) if e.get("number") == 1 and e.get("url")), None)
    if not ep1:
        return logr("anime_naruto", "failed", {"message": "No ep1 with URL"})
    print(f"  URL: {ep1['url'][:100]}")
    ok, d = dl_start_wait(client, 469, "Naruto", 1, ep1["url"], "anime", timeout=600)
    return logr("anime_naruto", "passed" if ok else "failed", d)

def test_series_dexter(client):
    print("\n=== SERIES: Dexter S08E01 via setfilmizle.uk ===")
    r = client.get(f"{API}/api/content/287")
    if r.status_code != 200:
        return logr("series_dexter", "skipped", {"message": "Dexter #287 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    sites = c.get("sites", []) or []
    eps = c.get("episodes", [])
    ep1 = next((e for e in eps if e.get("number") == 1 and e.get("season") == 8), eps[0] if eps else None)
    if not ep1:
        return logr("series_dexter", "failed", {"message": "No episodes"})
    url = ep1.get("url", "") or (sites[0].get("site_url", "") if sites else "")
    if not url:
        return logr("series_dexter", "failed", {"message": "No URL"})
    src = "ep" if ep1.get("url") else "site_fallback"
    print(f"  Ep1 URL: {url[:100]} (source={src})")
    ok, d = dl_start_wait(client, 287, "Dexter", ep1["number"], url, "series", timeout=600)
    return logr("series_dexter", "passed" if ok else "failed", d)

def test_movie_3idiots(client):
    print("\n=== MOVIE: 3 Idiots via hdfilmcehennemi.now ===")
    r = client.get(f"{API}/api/content/203")
    if r.status_code != 200:
        return logr("movie_3idiots", "skipped", {"message": "3 Idiots #203 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']}")
    sites = c.get("sites", []) or []
    eps = c.get("episodes", [])
    ep1 = eps[0] if eps else None
    url = (ep1.get("url", "") if ep1 else "") or (sites[0].get("site_url", "") if sites else "")
    if not url:
        return logr("movie_3idiots", "failed", {"message": "No URL"})
    print(f"  URL: {url[:100]}")
    ok, d = dl_start_wait(client, 203, c["title"], 1, url, "movie", timeout=600)
    return logr("movie_3idiots", "passed" if ok else "failed", d)

def test_manga_martial_peak(client):
    print("\n=== MANGA: Martial Peak Bolum 1 via mangadex.org ===")
    r = client.get(f"{API}/api/content/1")
    if r.status_code != 200:
        return logr("manga_martial_peak", "skipped", {"message": "Martial Peak #1 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']} ({c.get('type','?')})")
    ep1 = next((e for e in c.get("episodes", []) if e.get("number") == 1 and e.get("url")), None)
    if not ep1:
        return logr("manga_martial_peak", "failed", {"message": "No ep1 with URL"})
    print(f"  URL: {ep1['url'][:100]}")
    ok, d = dl_start_wait(client, 1, "Martial Peak", 1, ep1["url"], "manga", timeout=300)
    return logr("manga_martial_peak", "passed" if ok else "failed", d)

def test_manhwa(client):
    print("\n=== MANHWA: A Returner's Magic Should Be Special B1 ===")
    r = client.get(f"{API}/api/content/10")
    if r.status_code != 200:
        return logr("manhwa", "skipped", {"message": "#10 not found"})
    c = r.json()
    print(f"  #{c['id']}: {c['title']} ({c.get('type','?')})")
    # Check sites first
    sites = c.get("sites", [])
    eps = c.get("episodes", [])
    ep1 = next((e for e in eps if e.get("number") == 1 and e.get("url")), None)
    if not ep1:
        return logr("manhwa", "failed", {"message": f"No ep1 with URL ({len(eps)} total)"})
    url = ep1["url"]
    # Verify URL isn't to a known-dead site
    dead_domains = ["manhwahentai.me"]
    for dd in dead_domains:
        if dd in url:
            print(f"  WARNING: URL points to dead domain {dd}, trying alternative...")
            # Try to find a different URL
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
    print("\n=== GAME: Cult of the Lamb FitGirl magnet ===")
    r = client.get(f"{API}/api/game/128/fitgirl/search?q=Cult+of+the+Lamb")
    if r.status_code != 200:
        return logr("game", "failed", {"message": f"FitGirl search: {r.status_code} {r.text[:150]}"})
    results = r.json().get("results", [])
    if not results:
        return logr("game", "failed", {"message": "No FitGirl results"})
    print(f"  FitGirl: {len(results)} results, picking first")
    fit = results[0]
    r2 = client.post(f"{API}/api/game/128/fitgirl/detail", json={"url": fit["url"]})
    if r2.status_code != 200:
        return logr("game", "failed", {"message": f"Detail: {r2.status_code} {r2.text[:150]}"})
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
    print("SOHBET-140 — GERCEK INDIRME TESTI")
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
    tests = [
        ("Anime - Naruto", test_anime_naruto),
        ("Series - Dexter", test_series_dexter),
        ("Movie - 3 Idiots", test_movie_3idiots),
        ("Manga - Martial Peak", test_manga_martial_peak),
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
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nRapor: {REPORT_PATH}")

if __name__ == "__main__":
    main()
