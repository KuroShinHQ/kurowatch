import asyncio
import sqlite3
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import httpx

DB = os.environ.get("KUROWATCH_DB_PATH", str(ROOT / "memory" / "kurowatch.db"))
CONCURRENCY = 20
TIMEOUT = 15.0


async def check_url(client, row):
    cid, title, ctype, url = row["id"], row["title"], row["type"], row["cover_url"]
    try:
        r = await client.head(url, follow_redirects=True, timeout=TIMEOUT)
        status = r.status_code
        ct = r.headers.get("content-type", "").lower()
        cl = int(r.headers.get("content-length", "0"))
        if status == 200 and "image" in ct and cl > 0:
            return ("OK", cid, title, ctype, url, f"{status} {ct} {cl}B")
        if status == 200 and cl > 0 and not ct:
            r2 = await client.get(url, follow_redirects=True, timeout=TIMEOUT)
            ct2 = r2.headers.get("content-type", "").lower()
            if "image" in ct2 and len(r2.content) > 0:
                return ("OK", cid, title, ctype, url, f"{status} {ct2} {len(r2.content)}B")
            return ("BAD_TYPE", cid, title, ctype, url, f"{status} {ct2} {len(r2.content)}B")
        if status == 200 and "image" not in ct:
            return ("BAD_TYPE", cid, title, ctype, url, f"{status} {ct} {cl}B")
        return ("BAD_STATUS", cid, title, ctype, url, f"{status} {ct} {cl}B")
    except httpx.TimeoutException:
        return ("TIMEOUT", cid, title, ctype, url, "timeout")
    except Exception as e:
        return ("ERROR", cid, title, ctype, url, str(e)[:80])


async def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT id, title, type, cover_url FROM content WHERE cover_url IS NOT NULL AND cover_url != '' ORDER BY id"
    ).fetchall()
    total = con.execute("SELECT count(*) FROM content").fetchone()[0]
    no_cover = con.execute(
        "SELECT count(*) FROM content WHERE cover_url IS NULL OR cover_url = ''"
    ).fetchone()[0]
    con.close()

    print(f"Total content: {total}")
    print(f"With cover_url: {len(rows)}")
    print(f"Without cover_url: {no_cover}")
    print(f"Checking {len(rows)} URLs (concurrency={CONCURRENCY})...\n")

    results = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async def bounded_check(client, row):
        async with sem:
            return await check_url(client, row)

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0 Safari/537.36"}
    ) as client:
        tasks = [bounded_check(client, r) for r in rows]
        done = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)
            done += 1
            if done % 50 == 0:
                print(f"  ...{done}/{len(rows)} checked")

    ok = [r for r in results if r[0] == "OK"]
    bad_status = [r for r in results if r[0] == "BAD_STATUS"]
    bad_type = [r for r in results if r[0] == "BAD_TYPE"]
    timeout = [r for r in results if r[0] == "TIMEOUT"]
    error = [r for r in results if r[0] == "ERROR"]

    print(f"\n{'='*60}")
    print(f"RESULTS: {len(ok)} OK / {len(bad_status)} BAD_STATUS / {len(bad_type)} BAD_TYPE / {len(timeout)} TIMEOUT / {len(error)} ERROR")
    print(f"{'='*60}")

    broken = bad_status + bad_type + timeout + error
    if broken:
        print(f"\n--- {len(broken)} BROKEN COVER URLS ---")
        by_type = {}
        for r in broken:
            ctype = r[3]
            by_type.setdefault(ctype, []).append(r)
        for ctype, items in sorted(by_type.items()):
            print(f"\n  [{ctype}] ({len(items)} broken):")
            for r in items[:20]:
                print(f"    #{r[1]} {r[2][:40]:40s} {r[0]:12s} {r[5][:40]}")
            if len(items) > 20:
                print(f"    ... and {len(items)-20} more")

        print(f"\n--- BROKEN URL LIST (for fix script) ---")
        for r in broken:
            print(f"ID={r[1]}|TYPE={r[0]}|URL={r[4]}")
    else:
        print("\nAll cover URLs are valid!")

    return broken


if __name__ == "__main__":
    broken = asyncio.run(main())
    print(f"\nTotal broken: {len(broken)}")
