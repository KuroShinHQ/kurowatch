"""KuroWatch API Endpoint Test Suite — Systematic test of all endpoints"""
import asyncio, json, httpx, sys, traceback

API = "http://localhost:8099"
results = {"pass": 0, "fail": 0, "errors": []}

async def test(name, method, path, expected_status=200, body=None, check_fn=None, timeout=10):
    global results
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as client:
            if method == "GET":
                r = await client.get(API + path)
            elif method == "POST":
                r = await client.post(API + path, json=body)
            elif method == "PATCH":
                r = await client.patch(API + path, json=body)
            elif method == "DELETE":
                r = await client.delete(API + path)
            else:
                raise ValueError(f"Unknown method: {method}")

            status_ok = r.status_code == expected_status
            if not status_ok:
                raise AssertionError(f"Status {r.status_code} (expected {expected_status}): {r.text[:200]}")

            if check_fn:
                try:
                    data = r.json() if r.text else {}
                    check_fn(data)
                except Exception as e:
                    raise AssertionError(f"Check failed: {e}")

            results["pass"] += 1
            print(f"  ✅ {method} {path} -> {r.status_code}")
    except Exception as e:
        results["fail"] += 1
        msg = f"  ❌ {method} {path} -> {e}"
        results["errors"].append(msg)
        print(msg)

async def main():
    print("=" * 60)
    print("KUROWATCH API ENDPOINT TEST SUITE")
    print("=" * 60)

    # ── GRUP 1: Content endpoints ──
    print("\n--- GRUP 1: Content API ---")

    # T-01: GET /api/content - list all content
    content_ids = []
    def check_content_list(data):
        nonlocal content_ids
        assert isinstance(data, list), "Expected list"
        assert len(data) > 0, "Expected non-empty list"
        content_ids = [c["id"] for c in data[:5]]
        print(f"       Total content: {len(data)}, sample IDs: {content_ids}")
    await test("T-01", "GET", "/api/content", check_fn=check_content_list)

    # T-02: GET /api/content?type=anime
    await test("T-02", "GET", "/api/content?type=anime", check_fn=lambda d: (
        assert_(all(c["type"] == "anime" for c in d), "All must be anime"))
    )

    # T-03: GET /api/content?type=manga
    await test("T-03", "GET", "/api/content?type=manga", check_fn=lambda d: (
        assert_(all(c["type"] == "manga" for c in d), "All must be manga"))
    )

    # T-04: GET /api/content?type=manhwa
    await test("T-04", "GET", "/api/content?type=manhwa", check_fn=lambda d: (
        assert_(all(c["type"] == "manhwa" for c in d), "All must be manhwa"))
    )

    # T-05: GET /api/content?status=watching
    await test("T-05", "GET", "/api/content?status=watching", check_fn=lambda d: (
        assert_(all(c["status"] == "watching" for c in d), "All must be watching"))
    )

    # T-06: GET /api/content/{id} - single item
    if content_ids:
        cid = content_ids[0]
        await test("T-06", "GET", f"/api/content/{cid}", check_fn=lambda d: (
            assert_(d.get("id") == cid, f"ID mismatch")
        ))

    # T-07: GET /api/content/{id}/episodes
    if content_ids:
        await test("T-07", "GET", f"/api/content/{content_ids[0]}/episodes")

    # T-08: GET /api/content/{id}/seasons
    if content_ids:
        await test("T-08", "GET", f"/api/content/{content_ids[0]}/seasons")

    # T-09: GET /api/content/{id}/anilist
    # Find a content with external_id
    async with httpx.AsyncClient() as client:
        r = await client.get(API + "/api/content", timeout=10)
        items = r.json()
    anilist_item = next((c for c in items if c.get("external_id")), None)
    if anilist_item:
        await test("T-09", "GET", f"/api/content/{anilist_item['id']}/anilist")

    # T-10: PATCH /api/content/{id} (score update)
    if content_ids:
        await test("T-10", "PATCH", f"/api/content/{content_ids[0]}", body={"my_score": 9})

    # ── GRUP 2: Search & Discover ──
    print("\n--- GRUP 2: Search & Discover ---")
    await test("T-11", "GET", "/api/content?q=sword", check_fn=lambda d: (
        assert_(len(d) > 0, "Search should return results")
    ))
    await test("T-12", "GET", "/api/discover?genre=Action", check_fn=lambda d: (
        assert_(isinstance(d, list), "Discover should return list")
    ))
    await test("T-13", "GET", "/api/discover?genre=Action&q=sword")

    # ── GRUP 3: Updates ──
    print("\n--- GRUP 3: Updates ---")
    await test("T-14", "GET", "/api/updates", check_fn=lambda d: (
        assert_(isinstance(d, list), "Updates should be list")
    ))
    # T-15: check-updates long-running (external API calls), extend timeout to 120s
    await test("T-15", "POST", "/api/check-updates", timeout=120)
    # T-16: valid progress endpoint
    await test("T-16", "POST", f"/api/content/{content_ids[0]}/progress" if content_ids else "/api/content/1/progress", body={"progress": 1})

    # ── GRUP 4: Tags ──
    print("\n--- GRUP 4: Tags ---")
    await test("T-17", "GET", "/api/tags", check_fn=lambda d: (
        assert_(isinstance(d, list), "Tags should be list")
    ))
    # Use unique tag name to avoid 409 conflict
    import time as _t
    unique_tag = f"Test Tag {int(_t.time())}"
    await test("T-18", "POST", "/api/tags", body={"name": unique_tag, "color": "#00d4ff"}, expected_status=201)
    await test("T-19", "DELETE", "/api/tags/0", expected_status=404)

    # ── GRUP 5: Settings & Export ──
    print("\n--- GRUP 5: Settings & Export ---")
    await test("T-20", "GET", "/api/settings")
    await test("T-21", "POST", "/api/settings", body={"default_quality": "1080p"})
    await test("T-22", "GET", "/api/export")
    await test("T-23", "POST", "/api/settings", body={"default_quality": "720p"})

    # ── GRUP 6: Sites ──
    print("\n--- GRUP 6: Sites ---")
    if content_ids:
        await test("T-24a", "POST", f"/api/content/{content_ids[0]}/sites",
                   body={"site_name": "Test Site", "site_url": "https://example.com"},
                   expected_status=201)
        await test("T-24b", "GET", f"/api/content/{content_ids[0]}/episodes")

    # ── GRUP 7: Download endpoints (light) ──
    print("\n--- GRUP 7: Download ---")
    await test("T-25", "GET", "/api/download/queue", check_fn=lambda d: (
        assert_(isinstance(d, (list, dict)), "Queue should be list/dict")
    ))
    await test("T-26", "GET", "/api/download/storage")

    # ── GRUP 8: Sync/Import ──
    print("\n--- GRUP 8: Sync ---")
    # Import expects {"contents": [...]} format
    test_import = {"contents": [{"title": "Test Anime", "type": "anime", "my_score": 7}]}
    await test("T-27", "POST", "/api/import", body=test_import, expected_status=200)

    # ── GRUP 9: Export ──
    print("\n--- GRUP 9: Export ---")
    await test("T-28", "GET", "/api/export")

    # ── GRUP 10: Push ──
    print("\n--- GRUP 10: Push ---")
    await test("T-29", "GET", "/api/push/vapid-public-key")

    # ── GRUP 11: Progress endpoint ──
    print("\n--- GRUP 11: Progress ---")
    if content_ids:
        await test("T-30", "POST", f"/api/content/{content_ids[0]}/progress", body={"progress": 1}, expected_status=200)
        await test("T-31", "PATCH", f"/api/content/{content_ids[0]}", body={"my_score": 5})

    # ── GRUP 12: Cover upload endpoint check ──
    print("\n--- GRUP 12: Cover ---")
    if content_ids:
        await test("T-32", "POST", f"/api/content/{content_ids[0]}/cover", expected_status=422)  # No file = 422

    # ── SUMMARY ──
    print("\n" + "=" * 60)
    print(f"RESULTS: {results['pass']} PASS / {results['fail']} FAIL")
    print("=" * 60)
    if results["errors"]:
        print("\nFAILURES:")
        for e in results["errors"]:
            print(e)

    return results["fail"] == 0

def assert_(cond, msg):
    if not cond:
        raise AssertionError(msg)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
