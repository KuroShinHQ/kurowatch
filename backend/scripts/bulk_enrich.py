import asyncio
import json
import os
import re as _re
import sqlite3
import time
import sys
from datetime import datetime, timezone

import httpx

MAL_BASE = "https://api.myanimelist.net/v2"
TMDB_BASE = "https://api.themoviedb.org/3"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet135")
MAL_CLIENT_ID = "7bf9dbc0538aefb6eb465ca9ef04c8bb"
TMDB_KEY = "f04836fd27e727ace4233602dd71d47c"

MAL_FIELDS = "id,title,num_episodes,num_chapters,genres,mean,start_date,synopsis,status,rating,media_type"

TMDB_MAP = {"anime": "tv", "series": "tv", "cartoon": "tv", "movie": "movie"}

TYPE_COUNT = {"mal": 0, "tmdb": 0, "steam": 0}


def parse_eid(eid):
    if not eid:
        return None, None
    parts = eid.split(":", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else ("anilist", parts[0])


async def fetch_mal(mal_id, content_type, client):
    endpoint = "anime" if content_type in ("anime", "series", "cartoon", "movie") else "manga"
    try:
        r = await client.get(
            f"{MAL_BASE}/{endpoint}/{mal_id}",
            params={"fields": MAL_FIELDS},
            headers={"X-MAL-Client-ID": MAL_CLIENT_ID},
            timeout=12,
        )
        if r.status_code == 200:
            d = r.json()
            result = {"genres": [g["name"] for g in (d.get("genres") or [])]}
            syn = (d.get("synopsis") or "").strip()
            if syn:
                result["synopsis"] = syn
            date = (d.get("start_date") or "")
            if date and len(date) >= 4:
                try:
                    result["release_year"] = int(date[:4])
                except ValueError:
                    pass
            mean = d.get("mean")
            if mean:
                result["external_score"] = round(mean * 10)
            if endpoint == "anime":
                num = d.get("num_episodes")
                if num and num > 0:
                    result["total_episodes"] = num
            else:
                num = d.get("num_chapters")
                if num and num > 0:
                    result["total_chapters"] = num
            return result if len(result) > 1 else None
    except (httpx.TimeoutException, httpx.HTTPError) as e:
        return None
    return None


async def fetch_tmdb(tmdb_id, content_type, client):
    tmdb_type = TMDB_MAP.get(content_type, "tv")
    try:
        r = await client.get(
            f"{TMDB_BASE}/{tmdb_type}/{tmdb_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"},
            timeout=15,
        )
        if r.status_code == 200:
            d = r.json()
            result = {}
            genres = [g["name"] for g in (d.get("genres") or [])]
            if genres:
                result["genres"] = genres
            syn = (d.get("overview") or "").strip()
            if syn:
                result["synopsis"] = syn
            if content_type == "movie":
                date = d.get("release_date", "")
                if date and len(date) >= 4:
                    try:
                        result["release_year"] = int(date[:4])
                    except ValueError:
                        pass
                if d.get("runtime"):
                    result["runtime_minutes"] = d["runtime"]
            else:
                date = d.get("first_air_date", "")
                if date and len(date) >= 4:
                    try:
                        result["release_year"] = int(date[:4])
                    except ValueError:
                        pass
                seasons = d.get("seasons") or []
                total_ep = sum(s.get("episode_count", 0) for s in seasons if s.get("season_number", 0) > 0)
                if total_ep > 0:
                    result["total_episodes"] = total_ep
                runtimes = d.get("episode_run_time") or []
                if runtimes:
                    result["runtime_minutes"] = runtimes[0]
            vote = d.get("vote_average")
            if vote:
                result["external_score"] = round(vote / 2, 1)
            return result if result else None
    except (httpx.TimeoutException, httpx.HTTPError):
        pass
    return None


async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(
        "SELECT id, title, type, external_id, total_episodes, total_chapters, "
        "genres, synopsis, release_year, runtime_minutes, external_score "
        "FROM content ORDER BY id"
    ))
    conn.close()

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "updated": 0,
        "skipped_steam": 0,
        "failed": [],
        "details": [],
    }

    conn2 = sqlite3.connect(DB_PATH, timeout=30)
    lock = asyncio.Lock()
    progress = [0]

    async with httpx.AsyncClient(timeout=15) as client:
        sem = asyncio.Semaphore(15)

        async def process(row):
            async with sem:
                eid = row["external_id"]
                prefix, eid_val = parse_eid(eid)
                TYPE_COUNT[prefix or "none"] = TYPE_COUNT.get(prefix or "none", 0) + 1

                if prefix == "steam":
                    async with lock:
                        report["skipped_steam"] += 1
                    return

                updates = None
                if prefix == "tmdb" and eid_val:
                    updates = await fetch_tmdb(eid_val, row["type"], client)
                elif prefix in ("mal", None) and eid_val:
                    updates = await fetch_mal(eid_val, row["type"], client)

                if not updates:
                    async with lock:
                        report["failed"].append({"id": row["id"], "title": row["title"], "type": row["type"], "reason": "no data from API"})
                    return

                fields, vals = [], []
                for col, val in updates.items():
                    if val is None or val == "":
                        continue
                    if col == "genres":
                        val = json.dumps(val, ensure_ascii=False)
                    fields.append(col)
                    vals.append(val)

                if not fields:
                    return

                set_clause = ", ".join(f"{f}=?" for f in fields)
                conn2.execute(f"UPDATE content SET {set_clause} WHERE id=?", (*vals, row["id"]))
                conn2.commit()

                async with lock:
                    report["updated"] += 1
                    report["details"].append({
                        "id": row["id"], "title": row["title"], "type": row["type"],
                        "prefix": prefix,
                        "updated_fields": list(updates.keys()),
                    })
                    progress[0] += 1
                    if progress[0] % 50 == 0:
                        print(f"  {progress[0]}/{len(rows)}", flush=True)

        coros = [process(row) for row in rows]
        await asyncio.gather(*coros)

    conn2.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["failed_count"] = len(report["failed"])
    eligible = report["total"] - report["skipped_steam"]
    report["success_rate_pct"] = round(report["updated"] / max(eligible, 1) * 100, 1)

    rpath = os.path.join(REPORT_DIR, "metadata_raporu.json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== METADATA ENRICHMENT RAPORU ===")
    print(f"  Toplam: {report['total']}")
    print(f"  Güncellenen: {report['updated']}")
    print(f"  Atlanan (steam/game): {report['skipped_steam']}")
    print(f"  Başarısız: {report['failed_count']}")
    print(f"  Başarı oranı: {report['success_rate_pct']}%")
    print(f"  Tür dağılımı: {TYPE_COUNT}")
    print(f"  Rapor: {rpath}")


if __name__ == "__main__":
    asyncio.run(run())
