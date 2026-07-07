"""
SOHBET-120 backend integrity test.

Run directly for the real end-to-end path:
    python tests/test_backend_integrity.py

No mocks are used. This script talks to the live API, reads the live SQLite DB,
calls the real scraper, validates downloaded files on disk, then calls DELETE
and verifies that API state and physical files are gone.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.downloader.integrity import (
    probe_video_codec,
    validate_manga_dir,
    validate_video_file_playable,
)
from backend.downloader.manga import download_manga_chapter
from backend.downloader.stream_finder import find_stream_url


API_BASE_DEFAULT = os.environ.get("KUROWATCH_API_BASE", "http://127.0.0.1:8099")
DB_PATH_DEFAULT = os.environ.get("KUROWATCH_DB_PATH", str(ROOT / "memory" / "kurowatch.db"))
TERMINAL = {"done", "failed", "error", "cancelled", "deleted"}


def log(msg: str) -> None:
    print(f"[integrity] {msg}", flush=True)


def fail(msg: str) -> None:
    raise AssertionError(msg)


def host_path(path: str | None) -> Path:
    if not path:
        return Path("")
    normalized = path.replace("\\", "/")
    if normalized.startswith("/mnt/") and len(normalized) > 6 and normalized[6] == "/":
        drive = normalized[5].upper()
        rest = normalized[7:]
        return Path(f"{drive}:/{rest}")
    return Path(normalized)


def connect_db(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists() or path.stat().st_size == 0:
        fail(f"SQLite DB not found or empty: {path}")
    return sqlite3.connect(path)


def verify_sqlite_wal(db_path: str) -> None:
    with connect_db(db_path) as con:
        before = con.execute("PRAGMA journal_mode").fetchone()[0]
        mode = con.execute("PRAGMA journal_mode=WAL").fetchone()[0]
        con.execute("PRAGMA busy_timeout=30000")
        busy = con.execute("PRAGMA busy_timeout").fetchone()[0]
    log(f"SQLite journal_mode before={before}, after_request={mode}, busy_timeout={busy}ms")
    if mode.lower() != "wal":
        fail(f"SQLite WAL is not active: {mode}")
    if int(busy) < 30000:
        fail(f"SQLite busy_timeout too low: {busy}")


def pick_manga_candidate(db_path: str) -> dict:
    title = os.environ.get("KUROWATCH_INTEGRITY_TITLE", "Nano Machine").lower()
    episode = int(os.environ.get("KUROWATCH_INTEGRITY_EPISODE", "1"))
    with connect_db(db_path) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT c.id, c.title, c.type, e.number, e.url
            FROM content c
            JOIN episode e ON e.content_id = c.id
            WHERE c.type IN ('manga', 'manhwa')
              AND e.url IS NOT NULL
              AND e.url != ''
              AND lower(c.title) LIKE ?
              AND e.number = ?
            ORDER BY
              CASE
                WHEN e.url LIKE '%ragnarscans%' THEN 0
                WHEN e.url LIKE '%manhwahentai%' THEN 1
                WHEN e.url LIKE '%monomanga%' THEN 2
                WHEN e.url LIKE '%merlintoon%' THEN 3
                ELSE 9
              END,
              e.id
            LIMIT 1
            """,
            (f"%{title}%", episode),
        ).fetchall()
        if not rows:
            rows = con.execute(
                """
                SELECT c.id, c.title, c.type, e.number, e.url
                FROM content c
                JOIN episode e ON e.content_id = c.id
                WHERE c.type IN ('manga', 'manhwa')
                  AND e.url IS NOT NULL
                  AND e.url != ''
                ORDER BY c.id, e.number
                LIMIT 1
                """
            ).fetchall()
    if not rows:
        fail("No manga/manhwa episode with URL found in DB")
    row = dict(rows[0])
    log(f"Selected manga candidate: #{row['id']} {row['title']} ep{row['number']} {row['url']}")
    return row


def pick_anime_candidate(db_path: str) -> dict | None:
    title = os.environ.get("KUROWATCH_INTEGRITY_VIDEO_TITLE", "")
    with connect_db(db_path) as con:
        con.row_factory = sqlite3.Row
        if title:
            rows = con.execute(
                """
                SELECT c.id, c.title, c.type, e.number, e.url
                FROM content c
                JOIN episode e ON e.content_id = c.id
                WHERE c.type IN ('anime', 'series', 'movie', 'cartoon')
                  AND e.url IS NOT NULL
                  AND e.url != ''
                  AND lower(c.title) LIKE ?
                ORDER BY e.number
                LIMIT 1
                """,
                (f"%{title.lower()}%",),
            ).fetchall()
        else:
            rows = con.execute(
                """
                SELECT c.id, c.title, c.type, e.number, e.url
                FROM content c
                JOIN episode e ON e.content_id = c.id
                WHERE c.type = 'anime'
                  AND e.url IS NOT NULL
                  AND e.url != ''
                  AND e.url LIKE '%tranimaci.com%'
                ORDER BY c.id, e.number
                LIMIT 1
                """
            ).fetchall()
    if not rows:
        log("No anime/video candidate found; video probe skipped")
        return None
    row = dict(rows[0])
    log(f"Selected video candidate: #{row['id']} {row['title']} ep{row['number']} {row['url']}")
    return row


async def direct_scraper_check(candidate: dict) -> None:
    tmp_parent = ROOT / "downloads" / "_integrity_tmp"
    tmp_parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="scraper_", dir=tmp_parent))
    progress: list[tuple[int, int]] = []

    async def on_progress(done: int, total: int) -> None:
        progress.append((done, total))

    try:
        log("Direct scraper check starting")
        files = await download_manga_chapter(candidate["url"], str(tmp_dir), on_progress)
        files_abs, total_bytes = validate_manga_dir(str(tmp_dir))
        if len(files_abs) != len(files):
            fail(f"Scraper file count mismatch: returned={len(files)}, disk={len(files_abs)}")
        sample = files_abs[0]
        log(
            "Direct scraper PASS: "
            f"pages={len(files_abs)}, bytes={total_bytes}, first_page={Path(sample).name}, progress_events={len(progress)}"
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def assert_api_alive(client: httpx.Client) -> None:
    r = client.get("/api/content")
    log(f"API health GET /api/content -> HTTP {r.status_code}")
    if r.status_code != 200:
        fail(f"API not healthy: HTTP {r.status_code} {r.text[:200]}")
    if not isinstance(r.json(), list):
        fail("API /api/content did not return a list")


def poll_job(client: httpx.Client, job_id: int, timeout_s: int) -> dict:
    started = time.time()
    last: dict | None = None
    while time.time() - started < timeout_s:
        r = client.get("/api/download/queue")
        if r.status_code != 200:
            fail(f"GET /api/download/queue failed: HTTP {r.status_code} {r.text[:200]}")
        jobs = r.json().get("jobs", [])
        last = next((j for j in jobs if int(j.get("id")) == int(job_id)), None)
        if last:
            log(
                "Job poll: "
                f"id={job_id}, status={last.get('status')}, pct={last.get('progress_pct')}, "
                f"size={last.get('file_size_bytes')}, error={last.get('error_msg')}"
            )
            if last.get("status") in TERMINAL:
                return last
        time.sleep(2)
    fail(f"Job {job_id} did not reach terminal state in {timeout_s}s; last={last}")


def verify_job_absent(client: httpx.Client, job_id: int) -> None:
    r = client.get("/api/download/queue")
    if r.status_code != 200:
        fail(f"Queue check after delete failed: HTTP {r.status_code}")
    jobs = r.json().get("jobs", [])
    if any(int(j.get("id")) == int(job_id) for j in jobs):
        fail(f"Deleted job is still present in API queue: {job_id}")

    jobs_file = ROOT / "downloads" / "jobs.json"
    if jobs_file.exists():
        data = json.loads(jobs_file.read_text(encoding="utf-8") or "[]")
        if any(int(j.get("id")) == int(job_id) for j in data):
            fail(f"Deleted job is still present in jobs.json: {job_id}")
    log(f"Delete persistence PASS: job_id={job_id} absent from API queue and jobs.json")


def api_download_delete_check(client: httpx.Client, candidate: dict, timeout_s: int) -> None:
    payload = {
        "content_id": candidate["id"],
        "content_title": candidate["title"],
        "media_type": candidate["type"],
        "episode_number": candidate["number"],
        "url": candidate["url"],
        "quality": "720p",
    }
    r = client.post("/api/download/start", json=payload)
    log(f"POST /api/download/start -> HTTP {r.status_code}")
    if r.status_code != 200:
        fail(f"Download start failed: HTTP {r.status_code} {r.text[:500]}")
    job_id = int(r.json()["id"])

    job = poll_job(client, job_id, timeout_s)
    if job.get("status") != "done":
        fail(f"Download job did not complete: {job}")

    disk_path = host_path(job.get("file_path"))
    if not disk_path.exists():
        fail(f"Completed job path missing on disk: {disk_path}")
    files, total_bytes = validate_manga_dir(str(disk_path))
    log(f"API download disk PASS: job_id={job_id}, pages={len(files)}, bytes={total_bytes}, path={disk_path}")

    pages_r = client.get(f"/api/download/pages/{job_id}")
    log(f"GET /api/download/pages/{job_id} -> HTTP {pages_r.status_code}")
    if pages_r.status_code != 200:
        fail(f"Pages endpoint failed: HTTP {pages_r.status_code} {pages_r.text[:500]}")
    page_count = int(pages_r.json().get("count", 0))
    if page_count <= 0:
        fail(f"Pages endpoint returned zero pages for done job {job_id}")

    first_page_url = pages_r.json()["pages"][0]
    first_r = client.get(first_page_url)
    content_type = first_r.headers.get("content-type", "")
    log(
        f"GET {first_page_url} -> HTTP {first_r.status_code}, "
        f"content-type={content_type}, bytes={len(first_r.content)}"
    )
    if first_r.status_code != 200 or len(first_r.content) < 256 or "image" not in content_type:
        fail("First manga page endpoint did not return a valid image")

    delete_r = client.delete(f"/api/download/{job_id}")
    log(f"DELETE /api/download/{job_id} -> HTTP {delete_r.status_code}, body={delete_r.text[:300]}")
    if delete_r.status_code != 200:
        fail(f"Delete failed: HTTP {delete_r.status_code} {delete_r.text[:500]}")
    body = delete_r.json()
    if not body.get("ok"):
        fail(f"Delete returned ok=false: {body}")

    time.sleep(1)
    verify_job_absent(client, job_id)
    if disk_path.exists():
        fail(f"Deleted job path still exists on disk: {disk_path}")
    log(f"Physical delete PASS: removed_path={disk_path}")


async def video_stream_probe(candidate: dict) -> None:
    log("Video stream probe starting")
    actual_url = await find_stream_url(candidate["url"])
    parsed_source = urlparse(candidate["url"])
    referer = f"{parsed_source.scheme}://{parsed_source.netloc}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "video/webm,video/mp4,video/*;q=0.9,*/*;q=0.8",
        "Range": "bytes=0-65535",
        "Referer": referer,
    }
    async with httpx.AsyncClient(timeout=45.0, follow_redirects=True, headers=headers) as client:
        r = await client.get(actual_url)
    content_type = r.headers.get("content-type", "")
    log(
        "Video stream probe result: "
        f"url={actual_url[:140]}, HTTP={r.status_code}, content-type={content_type}, bytes={len(r.content)}"
    )
    if r.status_code not in (200, 206):
        fail(f"Video stream probe failed HTTP status: {r.status_code}")
    if len(r.content) == 0:
        fail("Video stream probe returned zero bytes")
    if "text/html" in content_type.lower():
        fail(f"Video stream probe returned HTML instead of media: {content_type}")


def api_video_download_check(client: httpx.Client, candidate: dict, timeout_s: int) -> None:
    payload = {
        "content_id": candidate["id"],
        "content_title": candidate["title"],
        "media_type": "anime",
        "episode_number": candidate["number"],
        "url": candidate["url"],
        "quality": "720p",
    }
    r = client.post("/api/download/start", json=payload)
    log(f"POST /api/download/start video -> HTTP {r.status_code}")
    if r.status_code != 200:
        fail(f"Video download start failed: HTTP {r.status_code} {r.text[:500]}")
    job_id = int(r.json()["id"])
    job = poll_job(client, job_id, timeout_s)
    if job.get("status") != "done":
        fail(f"Video download job did not complete: {job}")
    disk_path = host_path(job.get("file_path"))
    size = validate_video_file_playable(str(disk_path))
    codec_info = probe_video_codec(str(disk_path))
    codec_name = codec_info.get("codec_name", "unknown") if codec_info else "ffprobe-unavailable"
    resolution = ""
    if codec_info and codec_info.get("width") and codec_info.get("height"):
        resolution = f"{codec_info['width']}x{codec_info['height']}"
    log(
        f"API video disk PASS: job_id={job_id}, bytes={size}, "
        f"codec={codec_name}, res={resolution or 'n/a'}, path={disk_path}"
    )
    serve_r = client.get(f"/api/download/serve/{job_id}", headers={"Range": "bytes=0-65535"})
    log(f"GET /api/download/serve/{job_id} -> HTTP {serve_r.status_code}, bytes={len(serve_r.content)}")
    if serve_r.status_code not in (200, 206) or len(serve_r.content) == 0:
        fail("Video serve endpoint did not return media bytes")
    delete_r = client.delete(f"/api/download/{job_id}")
    log(f"DELETE /api/download/{job_id} video -> HTTP {delete_r.status_code}, body={delete_r.text[:300]}")
    if delete_r.status_code != 200 or not delete_r.json().get("ok"):
        fail(f"Video delete failed: HTTP {delete_r.status_code} {delete_r.text[:500]}")
    time.sleep(1)
    verify_job_absent(client, job_id)
    if disk_path.exists():
        fail(f"Deleted video path still exists on disk: {disk_path}")
    log(f"Physical video delete PASS: removed_path={disk_path}")


async def run(args: argparse.Namespace) -> None:
    log("NO MOCK MODE: this script uses live API, live DB, real scraper, and disk checks")
    verify_sqlite_wal(args.db)
    manga = pick_manga_candidate(args.db)
    await direct_scraper_check(manga)

    with httpx.Client(base_url=args.api, timeout=20.0) as client:
        assert_api_alive(client)
        api_download_delete_check(client, manga, args.timeout)

        video = pick_anime_candidate(args.db)
        if video and not args.skip_video_probe:
            await video_stream_probe(video)
        if video and args.include_video_download:
            api_video_download_check(client, video, args.video_timeout)
        elif video:
            log("Full video API download skipped; pass --include-video-download to download and delete a real video file")

    log("BACKEND INTEGRITY PASS")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=API_BASE_DEFAULT, help="KuroWatch API base URL")
    parser.add_argument("--db", default=DB_PATH_DEFAULT, help="SQLite DB path")
    parser.add_argument("--timeout", type=int, default=int(os.environ.get("KUROWATCH_INTEGRITY_TIMEOUT", "180")))
    parser.add_argument("--video-timeout", type=int, default=int(os.environ.get("KUROWATCH_INTEGRITY_VIDEO_TIMEOUT", "1800")))
    parser.add_argument("--skip-video-probe", action="store_true")
    parser.add_argument("--include-video-download", action="store_true")
    return parser.parse_args(argv)


def test_backend_integrity_real_e2e():
    import pytest

    if os.environ.get("KUROWATCH_RUN_INTEGRITY") != "1":
        pytest.skip("Real backend integrity E2E is skipped unless KUROWATCH_RUN_INTEGRITY=1")
    asyncio.run(run(parse_args([])))


if __name__ == "__main__":
    asyncio.run(run(parse_args(sys.argv[1:])))
