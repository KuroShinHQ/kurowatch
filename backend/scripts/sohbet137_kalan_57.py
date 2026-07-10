import asyncio, json, os, sqlite3, sys, re
from datetime import datetime, timezone
import httpx

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "memory", "kurowatch.db")
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "_kanit_sohbet137")
TMDB_KEY = "f04836fd27e727ace4233602dd71d47c"
TMDB_BASE = "https://api.themoviedb.org/3"
MAL_CLIENT_ID = "7bf9dbc0538aefb6eb465ca9ef04c8bb"
ANILIST_URL = "https://graphql.anilist.co"

ANILIST_SEARCH_Q = """
query ($search: String, $type: MediaType) {
  Page(search: $search, perPage: 5) {
    media(type: $type) {
      id
      title { romaji english native }
      episodes chapters
      format status
    }
  }
}
"""


async def search_tmdb(query, content_type, client):
    t = "movie" if content_type == "movie" else "tv"
    try:
        r = await client.get(f"{TMDB_BASE}/search/{t}",
            params={"api_key": TMDB_KEY, "query": query, "language": "tr-TR"},
            timeout=12)
        if r.status_code == 200:
            results = r.json().get("results", [])
            if results:
                return results[0]
    except Exception:
        pass
    return None


async def search_anilist(query, content_type, client):
    al_type = "ANIME" if content_type in ("anime", "series", "cartoon", "movie") else "MANGA"
    try:
        r = await client.post(ANILIST_URL, json={
            "query": ANILIST_SEARCH_Q,
            "variables": {"search": query, "type": al_type}
        }, timeout=12)
        if r.status_code == 200:
            media_list = r.json().get("data", {}).get("Page", {}).get("media", [])
            if media_list:
                m = media_list[0]
                title = m.get("title", {})
                best = title.get("english") or title.get("romaji") or title.get("native") or ""
                return {"id": m["id"], "title": best, "episodes": m.get("episodes"), "chapters": m.get("chapters"), "format": m.get("format")}
    except Exception:
        pass
    return None


async def get_tmdb_detail(tmdb_id, content_type, client):
    t = "movie" if content_type == "movie" else "tv"
    try:
        r = await client.get(f"{TMDB_BASE}/{t}/{tmdb_id}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"}, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


async def get_tmdb_season(tv_id, season_num, client):
    try:
        r = await client.get(f"{TMDB_BASE}/tv/{tv_id}/season/{season_num}",
            params={"api_key": TMDB_KEY, "language": "tr-TR"}, timeout=12)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def normalize_title(t):
    t = t.lower()
    t = re.sub(r'[\(\[].*?[\)\]]', '', t)
    t = re.sub(r's\d+|sezon\s*\d+|season\s*\d+', '', t, flags=re.I)
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def title_is_turkish(t):
    turkish_keywords = ['arkasokaklar', 'çocuklar', 'çokgüzel', 'kurtlarvadisi',
                         'dabbe', 'gladio', 'tetikçi', 'g.o.r.a', 'kral',
                         'öylebir', 'geçerzaman']
    nt = normalize_title(t).replace(' ', '')
    return any(kw in nt for kw in turkish_keywords)


async def sync_episodes_from_tmdb(cid, tmdb_id, content_type, conn, client):
    t = "movie" if content_type == "movie" else "tv"
    if content_type == "movie":
        detail = await get_tmdb_detail(tmdb_id, "movie", client)
        if detail:
            conn.execute("UPDATE content SET total_episodes=1, external_id=? WHERE id=?", (f"tmdb:{tmdb_id}", cid))
            conn.execute("INSERT INTO episode (content_id, season, number, title, is_watched, is_new) VALUES (?,1,1,'',0,1)", (cid,))
            conn.commit()
            return 1
    else:
        detail = await get_tmdb_detail(tmdb_id, content_type, client)
        if detail:
            seasons = detail.get("seasons", [])
            total_ep = 0
            added = 0
            for s in seasons:
                sn = s.get("season_number", 0)
                if sn == 0: continue
                total_ep += s.get("episode_count", 0)
                sd = await get_tmdb_season(tmdb_id, sn, client)
                if sd:
                    for ep in sd.get("episodes", []):
                        ep_num = ep.get("episode_number")
                        ep_title = (ep.get("name") or "").strip()
                        if ep_title == f"Bölüm {ep_num}":
                            ep_title = ""
                        conn.execute("INSERT INTO episode (content_id, season, number, title, is_watched, is_new) VALUES (?,?,?,?,0,1)",
                                     (cid, sn, ep_num, ep_title))
                        added += 1
            if added:
                conn.execute("UPDATE content SET total_episodes=?, external_id=? WHERE id=?", (total_ep, f"tmdb:{tmdb_id}", cid))
                conn.commit()
                return added
    return 0


async def sync_episodes_from_anilist(cid, al_id, content_type, total_ep, total_ch, conn, client):
    prefix = f"anilist:{al_id}"
    if total_ep and content_type in ("anime", "series", "cartoon", "movie"):
        count = 1 if content_type == "movie" else total_ep
        for n in range(1, count + 1):
            conn.execute("INSERT INTO episode (content_id, season, number, title, is_watched, is_new) VALUES (?,1,?,'',0,1)", (cid, n))
        conn.execute("UPDATE content SET total_episodes=?, external_id=? WHERE id=?", (total_ep, prefix, cid))
        conn.commit()
        return count
    elif total_ch and content_type in ("manga", "manhwa"):
        for n in range(1, total_ch + 1):
            conn.execute("INSERT INTO episode (content_id, season, number, title, is_watched, is_new) VALUES (?,1,?,'',0,1)", (cid, n))
        conn.execute("UPDATE content SET total_chapters=?, external_id=? WHERE id=?", (total_ch, prefix, cid))
        conn.commit()
        return total_ch
    return 0


async def run():
    os.makedirs(REPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    # Items without external_id AND no episodes (the 32 + some extra)
    all_rows = list(conn.execute(
        "SELECT id, title, type FROM content WHERE (external_id IS NULL OR external_id = '') AND "
        "NOT EXISTS (SELECT 1 FROM episode WHERE content_id=content.id) AND type != 'game' ORDER BY type, id"
    ))
    # Plus the 6 MAL failures that have external_id but no episodes
    mal_fails = list(conn.execute(
        "SELECT id, title, type, external_id FROM content WHERE "
        "NOT EXISTS (SELECT 1 FROM episode WHERE content_id=content.id) AND type != 'game' "
        "AND external_id IS NOT NULL AND external_id != '' ORDER BY id"
    ))
    all_items = [(r["id"], r["title"], r["type"], None) for r in all_rows]
    all_items += [(r["id"], r["title"], r["type"], r["external_id"]) for r in mal_fails]
    conn.close()

    print(f"Items to process: {len(all_items)} (no_eid={len(all_rows)}, mal_fails={len(mal_fails)})", flush=True)

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_items),
        "tmdb_found": 0,
        "anilist_found": 0,
        "episodes_added": 0,
        "not_found": 0,
        "turkish_skip": 0,
        "details": [],
    }

    conn2 = sqlite3.connect(DB_PATH, timeout=30)
    sem = asyncio.Semaphore(3)

    async with httpx.AsyncClient(timeout=15) as client:
        async def process(cid, title, ctype, old_eid):
            async with sem:
                info = {"id": cid, "title": title, "type": ctype, "old_external_id": old_eid}

                if title_is_turkish(title):
                    info["reason"] = "turkish content — no TMDB/AniList"
                    report["turkish_skip"] += 1
                    report["details"].append(info)
                    return

                # Step 1: Try TMDB
                search_terms = [title]
                if "(" in title:
                    base = title.split("(")[0].strip()
                    if base:
                        search_terms.append(base)
                if ":" in title:
                    base = title.split(":")[0].strip()
                    if base:
                        search_terms.append(base)
                if "Serisi" in title or "Serileri" in title:
                    base = re.sub(r'\s*Serisi\s*(Tüm.*)?$', '', title, flags=re.I).strip()
                    if base:
                        search_terms.append(base)

                tmdb_result = None
                best_term = None
                for term in search_terms:
                    res = await search_tmdb(term, ctype, client)
                    if res:
                        tmdb_result = res
                        best_term = term
                        break

                if tmdb_result:
                    tmdb_id = tmdb_result["id"]
                    info["tmdb_id"] = tmdb_id
                    info["search_term"] = best_term
                    added = await sync_episodes_from_tmdb(cid, tmdb_id, ctype, conn2, client)
                    if added:
                        report["tmdb_found"] += 1
                        report["episodes_added"] += added
                        info["source"] = "tmdb"
                        info["episodes_added"] = added
                        info["tmdb_title"] = tmdb_result.get("title") or tmdb_result.get("name", "")
                        print(f"  TMDB: {title} → tmdb:{tmdb_id} ({added} ep)", flush=True)
                        report["details"].append(info)
                        return
                    # TMDB found but no episodes synced (shouldn't happen)
                    info["reason"] = "tmdb found but no episodes"
                    report["details"].append(info)
                    return

                # Step 2: Try AniList
                for term in search_terms:
                    al = await search_anilist(term, ctype, client)
                    if al:
                        info["anilist_id"] = al["id"]
                        info["search_term"] = term
                        added = await sync_episodes_from_anilist(cid, al["id"], ctype, al.get("episodes"), al.get("chapters"), conn2, client)
                        if added:
                            report["anilist_found"] += 1
                            report["episodes_added"] += added
                            info["source"] = "anilist"
                            info["episodes_added"] = added
                            info["anilist_title"] = al["title"]
                            print(f"  AniList: {title} → anilist:{al['id']} ({added} ep)", flush=True)
                            report["details"].append(info)
                            return

                info["reason"] = "not found on TMDB or AniList"
                report["not_found"] += 1
                report["details"].append(info)
                print(f"  NOT FOUND: {title} ({ctype})", flush=True)

        for cid, title, ctype, old_eid in all_items:
            await process(cid, title, ctype, old_eid)

    conn2.close()

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["total_found"] = report["tmdb_found"] + report["anilist_found"]
    report["total_remaining"] = report["total"] - report["total_found"] - report["turkish_skip"]

    rpath = os.path.join(REPORT_DIR, "kalan_57_raporu.json")
    with open(rpath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n=== SOHBET-137 RAPORU ===")
    print(f"  Total: {report['total']}")
    print(f"  TMDB: {report['tmdb_found']}")
    print(f"  AniList: {report['anilist_found']}")
    print(f"  Episodes added: {report['episodes_added']}")
    print(f"  Not found: {report['not_found']}")
    print(f"  Turkish skip: {report['turkish_skip']}")
    print(f"  Remaining: {report['total_remaining']}")
    print(f"  Rapor: {rpath}")


if __name__ == "__main__":
    asyncio.run(run())
