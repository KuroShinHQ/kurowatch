import asyncio, json, os, sqlite3, sys
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


async def fetch_mal(mal_id, content_type, client):
    endpoint = "anime" if content_type in ("anime", "series", "cartoon", "movie") else "manga"
    try:
        r = await client.get(
            f"{MAL_BASE}/{endpoint}/{mal_id}",
            params={"fields": MAL_FIELDS},
            headers={"X-MAL-Client-ID": MAL_CLIENT_ID}, timeout=12)
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
    except Exception:
        return None


async def fetch_tmdb(tmdb_id, content_type, client):
    tmdb_type = TMDB_MAP.get(content_type, "tv")
    try:
        r = await client.get(f"{TMDB_BASE}/{tmdb_type}/{tmdb_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            result = {}
            genres = [g["name"] for g in (d.get("genres") or [])]
            if genres: result["genres"] = genres
            syn = (d.get("overview") or "").strip()
            if syn: result["synopsis"] = syn
            if content_type == "movie":
                date = d.get("release_date", "")
                if date and len(date) >= 4:
                    try: result["release_year"] = int(date[:4])
                    except ValueError: pass
                if d.get("runtime"): result["runtime_minutes"] = d["runtime"]
            else:
                date = d.get("first_air_date", "")
                if date and len(date) >= 4:
                    try: result["release_year"] = int(date[:4])
                    except ValueError: pass
                seasons = d.get("seasons") or []
                total_ep = sum(s.get("episode_count", 0) for s in seasons if s.get("season_number", 0) > 0)
                if total_ep > 0: result["total_episodes"] = total_ep
                runtimes = d.get("episode_run_time") or []
                if runtimes: result["runtime_minutes"] = runtimes[0]
            vote = d.get("vote_average")
            if vote: result["external_score"] = round(vote / 2, 1)
            return result if result else None
    except Exception:
        return None


async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    # Only items with NULL genres (not enriched) and have external_id
    rows = list(conn.execute(
        "SELECT id, title, type, external_id FROM content "
        "WHERE (genres IS NULL OR genres = 'null' OR total_episodes IS NULL OR total_chapters IS NULL) "
        "AND external_id IS NOT NULL AND external_id != '' ORDER BY id"
    ))
    conn.close()
    print(f"Items to re-process: {len(rows)}", flush=True)

    updated = 0
    failed = 0
    dp = 0

    async with httpx.AsyncClient(timeout=15) as client, asyncio.Semaphore(15) as sem:
        async def process(row):
            nonlocal dp
            eid = row["external_id"]
            prefix = eid.split(":", 1)[0] if ":" in eid else "mal"
            eid_val = eid.split(":", 1)[1] if ":" in eid else eid
            updates = None
            if prefix == "tmdb":
                updates = await fetch_tmdb(eid_val, row["type"], client)
            elif prefix in ("mal", "anilist"):
                updates = await fetch_mal(eid_val, row["type"], client)

            if updates:
                conn2 = sqlite3.connect(DB_PATH, timeout=30)
                fields, vals = [], []
                for col, val in updates.items():
                    if val is None or val == "":
                        continue
                    if col == "genres": val = json.dumps(val, ensure_ascii=False)
                    fields.append(col)
                    vals.append(val)
                if fields:
                    conn2.execute(f"UPDATE content SET {', '.join(f+ '=?' for f in fields)} WHERE id=?", (*vals, row["id"]))
                    conn2.commit()
                conn2.close()
                dp += 1
                return True
            return False

        results = await asyncio.gather(*[process(r) for r in rows])
        updated = sum(1 for r in results if r)
        failed = sum(1 for r in results if not r)

    print(f"Done: {updated} updated, {failed} failed", flush=True)

    report = {"reprocessed_at": datetime.now(timezone.utc).isoformat(), "total": len(rows), "updated": updated, "failed": failed}
    rpath = os.path.join(REPORT_DIR, "reprocess_raporu.json")
    with open(rpath, "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"Report: {rpath}")


if __name__ == "__main__":
    asyncio.run(run())
