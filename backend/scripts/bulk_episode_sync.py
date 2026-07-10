import asyncio
import json
import os
import sqlite3
import time
from datetime import datetime, timezone

import httpx

ANILIST_URL = "https://graphql.anilist.co"
TMDB_BASE = "https://api.themoviedb.org/3"
MDX_BASE = "https://api.mangadex.org"

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet135")

TMDB_KEY = "f04836fd27e727ace4233602dd71d47c"
MAL_CLIENT_ID = "7bf9dbc0538aefb6eb465ca9ef04c8bb"

ANILIST_EP_Q = """
query ($idMal: Int, $type: MediaType) {
  Media(idMal: $idMal, type: $type) {
    id
    title { romaji english }
    episodes
    chapters
    streamingEpisodes { title url }
  }
}
"""


def parse_external_id(eid):
    if not eid:
        return None, None
    parts = eid.split(":", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "anilist", parts[0]


async def fetch_tmdb_tv_detail(tv_id, client):
    try:
        r = await client.get(
            f"{TMDB_BASE}/tv/{tv_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


async def fetch_tmdb_tv_season(tv_id, season_num, client):
    try:
        r = await client.get(
            f"{TMDB_BASE}/tv/{tv_id}/season/{season_num}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


async def fetch_tmdb_movie_detail(movie_id, client):
    try:
        r = await client.get(
            f"{TMDB_BASE}/movie/{movie_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"},
            timeout=15,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


async def fetch_anilist_by_mal(mal_id, media_type, client):
    vars_ = {"idMal": int(mal_id), "type": media_type}
    try:
        r = await client.post(ANILIST_URL, json={"query": ANILIST_EP_Q, "variables": vars_}, timeout=15)
        if r.status_code == 429:
            retry_after = int(r.headers.get("retry-after", 60))
            await asyncio.sleep(retry_after + 1)
            r = await client.post(ANILIST_URL, json={"query": ANILIST_EP_Q, "variables": vars_}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("data", {}).get("Media")
    except Exception:
        pass
    return None


async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, title, type, external_id FROM content ORDER BY id").fetchall()

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "updated": 0,
        "skipped": 0,
        "episodes_added": 0,
        "failed": [],
        "details": [],
    }

    sem = asyncio.Semaphore(5)

    async with httpx.AsyncClient(timeout=15) as client:

        async def process(row):
            cid = row["id"]
            title = row["title"]
            ctype = row["type"]
            eid = row["external_id"]
            prefix, eid_val = parse_external_id(eid)

            if ctype == "game":
                report["skipped"] += 1
                return

            existing = conn.execute(
                "SELECT COUNT(*) as cnt FROM episode WHERE content_id=?", (cid,)
            ).fetchone()["cnt"]

            if ctype in ("manga", "manhwa"):
                if existing > 0:
                    report["skipped"] += 1
                    return

            async with sem:
                info = {"id": cid, "title": title, "type": ctype, "prefix": prefix}

                if prefix == "tmdb" and eid_val and ctype in ("anime", "series", "cartoon", "movie"):
                    if ctype == "movie":
                        detail = await fetch_tmdb_movie_detail(eid_val, client)
                        if detail and existing == 0:
                            runtime = detail.get("runtime") or 0
                            year = (detail.get("release_date") or "")[:4]
                            conn.execute("UPDATE content SET runtime_minutes=?, release_year=? WHERE id=?",
                                         (runtime if runtime else None,
                                          int(year) if year and year.isdigit() else None,
                                          cid))
                            conn.commit()
                            info["movie_metadata"] = True
                            report["updated"] += 1
                    else:
                        detail = await fetch_tmdb_tv_detail(eid_val, client)
                        if detail:
                            seasons = detail.get("seasons") or []
                            added_count = 0
                            for s in seasons:
                                sn = s.get("season_number", 0)
                                if sn == 0:
                                    continue
                                season_data = await fetch_tmdb_tv_season(eid_val, sn, client)
                                if season_data:
                                    existing_nums = set()
                                    if existing > 0:
                                        existing_rows = conn.execute(
                                            "SELECT number FROM episode WHERE content_id=? AND season=?",
                                            (cid, sn)
                                        ).fetchall()
                                        existing_nums = {r["number"] for r in existing_rows}

                                    for ep in season_data.get("episodes", []):
                                        ep_num = ep.get("episode_number")
                                        ep_title = (ep.get("name") or "").strip()
                                        if ep_title == f"Bölüm {ep_num}":
                                            ep_title = ""
                                        if ep_num and ep_num not in existing_nums:
                                            conn.execute(
                                                "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                                "VALUES (?, ?, ?, ?, 0, 1)",
                                                (cid, sn, ep_num, ep_title),
                                            )
                                            added_count += 1
                                            existing_nums.add(ep_num)

                            if added_count:
                                conn.commit()
                                report["episodes_added"] += added_count
                                report["updated"] += 1
                                info["tmdb_seasons"] = len(seasons)
                                info["episodes_added"] = added_count

                            total_ep = sum(
                                s.get("episode_count", 0) for s in seasons if s.get("season_number", 0) > 0
                            )
                            if total_ep > 0:
                                existing_total = conn.execute(
                                    "SELECT total_episodes FROM content WHERE id=?", (cid,)
                                ).fetchone()["total_episodes"]
                                if not existing_total:
                                    conn.execute("UPDATE content SET total_episodes=? WHERE id=?", (total_ep, cid))
                                    conn.commit()
                                    info["total_updated"] = total_ep

                elif prefix == "mal" and eid_val:
                    if existing > 0:
                        report["skipped"] += 1
                        return
                    media_type = "ANIME" if ctype in ("anime", "series", "cartoon", "movie") else "MANGA"
                    media = await fetch_anilist_by_mal(eid_val, media_type, client)
                    if media:
                        al_id = media.get("id")
                        streaming = media.get("streamingEpisodes") or []
                        total_ep = media.get("episodes") or media.get("chapters")
                        added_count = 0

                        if total_ep:
                            existing_total = conn.execute(
                                "SELECT total_episodes, total_chapters FROM content WHERE id=?", (cid,)
                            ).fetchone()
                            need_ep = ctype in ("anime", "series", "cartoon") and not existing_total["total_episodes"]
                            need_ch = ctype in ("manga", "manhwa") and not existing_total["total_chapters"]
                            if need_ep:
                                conn.execute("UPDATE content SET total_episodes=? WHERE id=?", (total_ep, cid))
                            if need_ch:
                                conn.execute("UPDATE content SET total_chapters=? WHERE id=?", (total_ep, cid))
                            conn.commit()

                        if streaming:
                            existing_nums = set()
                            if existing > 0:
                                existing_rows = conn.execute(
                                    "SELECT number FROM episode WHERE content_id=?", (cid,)
                                ).fetchall()
                                existing_nums = {r["number"] for r in existing_rows}
                            for idx, s in enumerate(streaming):
                                ep_num = idx + 1
                                if ep_num not in existing_nums:
                                    ep_url = s.get("url", "")
                                    conn.execute(
                                        "INSERT INTO episode (content_id, season, number, title, url, is_watched, is_new) "
                                        "VALUES (?, 1, ?, ?, ?, 0, 1)",
                                        (cid, ep_num, (s.get("title") or "")[:200], ep_url),
                                    )
                                    added_count += 1
                                    existing_nums.add(ep_num)
                        elif total_ep and existing == 0:
                            existing_nums = set()
                            for ep_num in range(1, total_ep + 1):
                                conn.execute(
                                    "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                    "VALUES (?, 1, ?, '', 0, 1)",
                                    (cid, ep_num),
                                )
                                added_count += 1

                        if added_count:
                            conn.commit()
                            report["episodes_added"] += added_count
                            report["updated"] += 1
                            info["anilist_id"] = al_id
                            info["episodes_added"] = added_count
                    else:
                        report["failed"].append({"id": cid, "title": title, "reason": "AniList returned no data"})
                        return

                info["existing_eps_before"] = existing
                report["details"].append(info)
                await asyncio.sleep(0.3)

        for i, row in enumerate(rows):
            await process(row)
            if (i + 1) % 50 == 0:
                print(f"  processed {i+1}/{len(rows)}")

    conn.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["failed_count"] = len(report["failed"])
    report["success_count"] = report["updated"]
    report["skipped_count"] = report["skipped"]

    rpath = os.path.join(REPORT_DIR, "episode_sync_raporu.json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== EPISODE SYNC RAPORU ===")
    print(f"  Toplam: {report['total']}")
    print(f"  Güncellenen: {report['updated']}")
    print(f"  Atlanan (zaten var/game): {report['skipped_count']}")
    print(f"  Eklenen episode: {report['episodes_added']}")
    print(f"  Başarısız: {report['failed_count']}")
    print(f"  Rapor: {rpath}")


if __name__ == "__main__":
    asyncio.run(run())
