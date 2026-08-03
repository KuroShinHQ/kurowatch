import asyncio, json, os, sqlite3, sys
from datetime import datetime, timezone
import httpx

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet136")
MAL_CLIENT_ID = "7bf9dbc0538aefb6eb465ca9ef04c8bb"
TMDB_KEY = "f04836fd27e727ace4233602dd71d47c"
MAL_FIELDS = "id,title,num_episodes,num_chapters,synopsis"
TMDB_BASE = "https://api.themoviedb.org/3"


async def fetch_mal(mal_id, content_type, client):
    endpoint = "anime" if content_type in ("anime", "series", "cartoon", "movie") else "manga"
    try:
        r = await client.get(
            f"https://api.myanimelist.net/v2/{endpoint}/{mal_id}",
            params={"fields": MAL_FIELDS},
            headers={"X-MAL-Client-ID": MAL_CLIENT_ID}, timeout=12)
        if r.status_code == 200:
            d = r.json()
            if endpoint == "anime":
                return {"total_episodes": d.get("num_episodes") or 0}
            else:
                return {"total_chapters": d.get("num_chapters") or 0}
    except Exception:
        return None


async def fetch_tmdb_detail(tmdb_id, content_type, client):
    tmdb_type = "movie" if content_type == "movie" else "tv"
    try:
        r = await client.get(f"{TMDB_BASE}/{tmdb_type}/{tmdb_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            if content_type == "movie":
                return {"total_episodes": 1}
            else:
                seasons = d.get("seasons") or []
                total_ep = sum(s.get("episode_count", 0) for s in seasons if s.get("season_number", 0) > 0)
                return {"total_episodes": total_ep if total_ep > 0 else None, "seasons": seasons}
    except Exception:
        return None


async def fetch_tmdb_season(tv_id, season_num, client):
    try:
        r = await client.get(f"{TMDB_BASE}/tv/{tv_id}/season/{season_num}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"}, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None


async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(
        "SELECT id, title, type, external_id, total_episodes, total_chapters "
        "FROM content c WHERE NOT EXISTS (SELECT 1 FROM episode e WHERE e.content_id=c.id) "
        "AND c.type != 'game' ORDER BY c.type, c.id"
    ))
    conn.close()

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "updated": 0,
        "no_external_id": 0,
        "no_tmdb_data": 0,
        "no_mal_data": 0,
        "episodes_added": 0,
        "failed": [],
        "details": [],
    }

    conn2 = sqlite3.connect(DB_PATH, timeout=30)
    sem = asyncio.Semaphore(5)
    progress = [0]

    async with httpx.AsyncClient(timeout=15) as client:
        async def process(row):
            cid = row["id"]
            ctype = row["type"]
            eid = row["external_id"]
            title = row["title"]
            added = 0

            async with sem:
                info = {"id": cid, "title": title, "type": ctype, "external_id": eid}

                if not eid:
                    report["no_external_id"] += 1
                    info["reason"] = "no external_id"
                    report["details"].append(info)
                    return

                prefix = eid.split(":", 1)[0] if ":" in eid else "mal"
                eid_val = eid.split(":", 1)[1] if ":" in eid else eid

                if prefix == "tmdb":
                    data = await fetch_tmdb_detail(eid_val, ctype, client)
                    if data and data.get("total_episodes"):
                        if ctype == "movie":
                            conn2.execute(
                                "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                "VALUES (?, 1, 1, '', 0, 1)", (cid,))
                            added = 1
                            # Update total_episodes if null
                            if not row["total_episodes"]:
                                conn2.execute("UPDATE content SET total_episodes=1 WHERE id=?", (cid,))
                        else:
                            seasons = data.get("seasons", [])
                            for s in seasons:
                                sn = s.get("season_number", 0)
                                if sn == 0:
                                    continue
                                season_data = await fetch_tmdb_season(eid_val, sn, client)
                                if season_data:
                                    for ep in season_data.get("episodes", []):
                                        ep_num = ep.get("episode_number")
                                        ep_title = (ep.get("name") or "").strip()
                                        if ep_title == f"Bölüm {ep_num}":
                                            ep_title = ""
                                        conn2.execute(
                                            "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                            "VALUES (?, ?, ?, ?, 0, 1)",
                                            (cid, sn, ep_num, ep_title))
                                        added += 1
                            # Update total_episodes if null
                            te = data.get("total_episodes")
                            if te and not row["total_episodes"]:
                                conn2.execute("UPDATE content SET total_episodes=? WHERE id=?", (te, cid))
                        info["source"] = "tmdb"
                    else:
                        report["no_tmdb_data"] += 1
                        info["reason"] = "tmdb no data"
                        report["details"].append(info)
                        return

                elif prefix in ("mal", "anilist"):
                    data = await fetch_mal(eid_val, ctype, client)
                    if data:
                        te = data.get("total_episodes")
                        tc = data.get("total_chapters")
                        if ctype == "movie" and te:
                            conn2.execute(
                                "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                "VALUES (?, 1, 1, '', 0, 1)", (cid,))
                            added = 1
                            if not row["total_episodes"]:
                                conn2.execute("UPDATE content SET total_episodes=1 WHERE id=?", (cid,))
                        elif ctype in ("anime", "series", "cartoon") and te:
                            for n in range(1, te + 1):
                                conn2.execute(
                                    "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                    "VALUES (?, 1, ?, '', 0, 1)", (cid, n))
                                added += 1
                            if not row["total_episodes"]:
                                conn2.execute("UPDATE content SET total_episodes=? WHERE id=?", (te, cid))
                        elif ctype in ("manga", "manhwa") and tc:
                            for n in range(1, tc + 1):
                                conn2.execute(
                                    "INSERT INTO episode (content_id, season, number, title, is_watched, is_new) "
                                    "VALUES (?, 1, ?, '', 0, 1)", (cid, n))
                                added += 1
                            if not row["total_chapters"]:
                                conn2.execute("UPDATE content SET total_chapters=? WHERE id=?", (tc, cid))
                        info["source"] = "mal"
                    else:
                        report["no_mal_data"] += 1
                        info["reason"] = "mal no data"
                        report["details"].append(info)
                        return

                if added:
                    conn2.commit()
                    report["updated"] += 1
                    report["episodes_added"] += added
                    info["episodes_added"] = added
                    info["episodes_from"] = prefix

                report["details"].append(info)
                progress[0] += 1
                if progress[0] % 10 == 0:
                    print(f"  {progress[0]}/{len(rows)}", flush=True)

        for row in rows:
            await process(row)

    conn2.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()

    rpath = os.path.join(REPORT_DIR, "kalan_52_raporu.json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== KALAN 52 EPISODE SYNC RAPORU ===")
    print(f"  Total: {report['total']}")
    print(f"  Updated (episode eklendi): {report['updated']}")
    print(f"  Episodes added: {report['episodes_added']}")
    print(f"  No external_id: {report['no_external_id']}")
    print(f"  No TMDB data: {report['no_tmdb_data']}")
    print(f"  No MAL data: {report['no_mal_data']}")
    print(f"  Rapor: {rpath}")


if __name__ == "__main__":
    asyncio.run(run())
