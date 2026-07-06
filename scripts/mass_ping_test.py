"""
Mass episode URL test using url_ping.py.
Tests episode 1 URL for ALL content (anime, manga, manhwa).
Reports pass/fail per domain.
"""
import asyncio, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.tools.url_ping import http_ping

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory", "kurowatch.db")
import sqlite3

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Get episode 1 URL for all content (excluding game)
rows = conn.execute("""
    SELECT c.id, c.type, c.title, e.id as eid, e.url
    FROM content c
    JOIN episode e ON e.content_id = c.id AND e.number = 1 AND e.season = 1
    WHERE c.type IN ('anime', 'manga', 'manhwa')
    ORDER BY c.type, c.id
""").fetchall()

conn.close()

print(f"Testing {len(rows)} episode URLs...")
print()

results = {"OK": 0, "CHALLENGE": 0, "FAIL": 0}
by_type = {}
by_domain = {}
failures = []

async def test_one(row, sem):
    async with sem:
        if not row['url']:
            return
        result = await http_ping(row['url'])
        status = result.status
        domain = result.host

        if status == "OK":
            results["OK"] += 1
        elif status == "CHALLENGE":
            results["CHALLENGE"] += 1
        else:
            results["FAIL"] += 1
            failures.append((row['id'], row['type'], row['title'], domain, status))
        
        by_type[row['type']] = by_type.get(row['type'], {"OK": 0, "CHALLENGE": 0, "FAIL": 0})
        by_type[row['type']][status if status in ("OK","CHALLENGE") else "FAIL"] += 1
        
        by_domain[domain] = by_domain.get(domain, {"OK": 0, "CHALLENGE": 0, "FAIL": 0})
        by_domain[domain][status if status in ("OK","CHALLENGE") else "FAIL"] += 1

        # Progress
        done = sum(results.values())
        if done % 50 == 0:
            total = len(rows)
            print(f"  Progress: {done}/{total} ({done*100//total}%) — OK:{results['OK']} CHALLENGE:{results['CHALLENGE']} FAIL:{results['FAIL']}")

async def main():
    t0 = time.time()
    sem = asyncio.Semaphore(10)  # 10 concurrent
    
    tasks = [test_one(row, sem) for row in rows if row['url']]
    await asyncio.gather(*tasks)
    
    elapsed = time.time() - t0
    
    print(f"\n{'='*60}")
    print(f"RESULTS — {len(rows)} tested in {elapsed:.0f}s")
    print(f"{'='*60}")
    print(f"OK:         {results['OK']}")
    print(f"CHALLENGE:  {results['CHALLENGE']}")
    print(f"FAIL:       {results['FAIL']}")
    pass_rate = (results['OK'] + results['CHALLENGE']) / max(len(rows), 1) * 100
    print(f"PASS RATE:  {pass_rate:.1f}%")
    
    print(f"\n--- BY TYPE ---")
    for t, d in sorted(by_type.items()):
        total = sum(d.values())
        ok = d['OK'] + d['CHALLENGE']
        print(f"  {t}: {ok}/{total} ({ok*100//max(total,1)}%) — OK:{d['OK']} CH:{d['CHALLENGE']} FAIL:{d['FAIL']}")
    
    print(f"\n--- BY DOMAIN ---")
    for domain, d in sorted(by_domain.items(), key=lambda x: sum(x[1].values()), reverse=True):
        total = sum(d.values())
        ok = d['OK'] + d['CHALLENGE']
        if total >= 3:
            print(f"  {domain}: {ok}/{total} ({ok*100//max(total,1)}%) — OK:{d['OK']} CH:{d['CHALLENGE']} FAIL:{d['FAIL']}")
    
    if failures:
        print(f"\n--- FAILURES ({len(failures)}) ---")
        for cid, ctype, title, domain, status in failures:
            print(f"  #{cid} [{ctype}] {title[:50]} → {domain} ({status})")

asyncio.run(main())
