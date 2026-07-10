import asyncio, json, os, sqlite3, re
from datetime import datetime, timezone
import httpx

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet138")
TMDB_KEY = "f04836fd27e727ace4233602dd71d47c"
TMDB_BASE = "https://api.themoviedb.org/3"
MAL_CLIENT_ID = "7bf9dbc0538aefb6eb465ca9ef04c8bb"

COVERABLE_TYPES = ("movie", "series", "cartoon", "anime")

async def fetch_tmdb_cover(tmdb_id, content_type, client):
    t = "movie" if content_type == "movie" else "tv"
    try:
        r = await client.get(f"{TMDB_BASE}/{t}/{tmdb_id}",
            params={"api_key": TMDB_KEY}, timeout=12)
        if r.status_code == 200:
            d = r.json()
            poster = d.get("poster_path")
            if poster:
                return f"https://image.tmdb.org/t/p/w500{poster}"
    except Exception:
        pass
    return None

async def search_tmdb_poster(title, content_type, client):
    t = "movie" if content_type == "movie" else "tv"
    clean = re.sub(r"\s*Serisi.*$|\s*\(.*?\)|\s*S\d+", "", title, flags=re.I).strip()
    try:
        r = await client.get(f"{TMDB_BASE}/search/{t}",
            params={"api_key": TMDB_KEY, "query": clean, "language": "tr-TR"}, timeout=10)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results and results[0].get("poster_path"):
                return f"https://image.tmdb.org/t/p/w500{results[0]['poster_path']}"
    except Exception:
        pass
    return None

async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute(
        "SELECT id, title, type, external_id, cover_url FROM content "
        "WHERE type IN ('movie','series','cartoon','anime') ORDER BY type, id"
    ))
    conn.close()
    print(f"Total coverable: {len(rows)}", flush=True)

    updated = 0
    skipped_ok = 0
    no_tmdb = 0
    details = []

    async with httpx.AsyncClient(timeout=15) as client, asyncio.Semaphore(5) as sem:
        async def process(row):
            nonlocal updated, skipped_ok, no_tmdb
            cid, title, ctype, eid, current_cover = row["id"], row["title"], row["type"], row["external_id"], row["cover_url"]
            info = {"id": cid, "title": title, "type": ctype}

            if not eid:
                # Try TMDB search by title
                poster = await search_tmdb_poster(title, ctype, client)
                if poster:
                    conn2 = sqlite3.connect(DB_PATH, timeout=30)
                    conn2.execute("UPDATE content SET cover_url=? WHERE id=?", (poster, cid))
                    conn2.commit()
                    conn2.close()
                    updated += 1
                    info["new_cover"] = poster
                    info["source"] = "tmdb_search"
                    print(f"  TMDB SEARCH: {title} → cover updated", flush=True)
                else:
                    no_tmdb += 1
                    info["reason"] = "no tmdb match"
                details.append(info)
                return

            prefix = eid.split(":", 1)[0] if ":" in eid else "mal"
            eid_val = eid.split(":", 1)[1] if ":" in eid else eid

            if prefix == "tmdb":
                poster = await fetch_tmdb_cover(eid_val, ctype, client)
                if poster and poster != current_cover:
                    conn2 = sqlite3.connect(DB_PATH, timeout=30)
                    conn2.execute("UPDATE content SET cover_url=? WHERE id=?", (poster, cid))
                    conn2.commit()
                    conn2.close()
                    updated += 1
                    info["new_cover"] = poster
                    info["source"] = "tmdb"
                    print(f"  TMDB: {title} → cover updated", flush=True)
                else:
                    skipped_ok += 1
                    info["reason"] = "same or no poster"
                details.append(info)

            elif prefix == "mal":
                poster = await search_tmdb_poster(title, ctype, client)
                if poster and poster != current_cover:
                    conn2 = sqlite3.connect(DB_PATH, timeout=30)
                    conn2.execute("UPDATE content SET cover_url=? WHERE id=?", (poster, cid))
                    conn2.commit()
                    conn2.close()
                    updated += 1
                    info["new_cover"] = poster
                    info["source"] = "tmdb_search"
                    print(f"  TMDB: {title} (mal:) → cover updated", flush=True)
                else:
                    skipped_ok += 1
                    info["reason"] = "no better cover"
                details.append(info)

        for row in rows:
            await process(row)

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total": len(rows),
        "updated": updated,
        "skipped_ok": skipped_ok,
        "no_tmdb": no_tmdb,
        "details": details,
    }
    rpath = os.path.join(REPORT_DIR, "cover_raporu.json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== COVER FIX RAPORU ===")
    print(f"  Total: {report['total']}")
    print(f"  Updated: {report['updated']}")
    print(f"  Already OK: {report['skipped_ok']}")
    print(f"  No TMDB match: {report['no_tmdb']}")
    print(f"  Rapor: {rpath}")

if __name__ == "__main__":
    asyncio.run(run())
