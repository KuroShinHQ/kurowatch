"""Quick API test for download endpoint."""
import httpx, json

API = "http://localhost:8099"
c = httpx.Client(timeout=30)

# Test 1: Health check
r = c.get(f"{API}/api/content?limit=1")
print(f"Health: {r.status_code} ({len(r.json())} items)")

# Test 2: Download start
r = c.post(f"{API}/api/download/start", json={
    "content_id": 287,
    "content_title": "Dexter",
    "media_type": "series",
    "episode_number": 1,
    "url": "https://www.setfilmizle.uk/bolum/dexter-1-sezon-1-bolum/",
})
print(f"Download start: {r.status_code}")
print(f"  Response: {json.dumps(r.json(), indent=2)[:500]}")

# Test 3: Download queue
r = c.get(f"{API}/api/download/queue")
print(f"\nQueue: {r.status_code}")
print(f"  Jobs: {json.dumps(r.json(), indent=2)[:500]}")

# Test 4: FitGirl search
r = c.get(f"{API}/api/game/128/fitgirl/search?q=Cult+of+the+Lamb")
print(f"\nFitGirl search: {r.status_code}")
if r.status_code == 200:
    print(f"  Results: {len(r.json())}")
    if r.json():
        print(f"  First: {json.dumps(r.json()[0], indent=2)[:300]}")
else:
    print(f"  Error: {r.text[:200]}")

c.close()
