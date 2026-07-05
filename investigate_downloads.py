"""Investigate Nano Machine and Black Butler issues"""
import httpx

api = httpx.Client(base_url="http://localhost:8099", timeout=30)

print("=== NANO MACHINE ===")
r = api.get("/api/content?q=Nano%20Machine&limit=5")
for item in r.json():
    cid = item["id"]
    print(f"  ID={cid}, Title={item.get('title')}, Type={item.get('type')}")
    for s in (item.get("sites") or []):
        print(f"    Site: {s.get('site_name')} -> {s.get('site_url')}")
    r2 = api.get(f"/api/content/{cid}/episodes")
    if r2.status_code == 200:
        eps = r2.json()
        print(f"  Episodes: {len(eps)}")
        if eps:
            print(f"  First ep: number={eps[0].get('number')} url={eps[0].get('url')}")
    print()

print("=== BLACK BUTLER ===")
r = api.get("/api/content?q=Black%20Butler&limit=5")
for item in r.json():
    cid = item["id"]
    print(f"  ID={cid}, Title={item.get('title')}, Type={item.get('type')}")
    for s in (item.get("sites") or []):
        print(f"    Site: {s.get('site_name')} -> {s.get('site_url')}")
    r2 = api.get(f"/api/content/{cid}/episodes")
    if r2.status_code == 200:
        eps = r2.json()
        print(f"  Episodes: {len(eps)}")
        if eps:
            print(f"  First ep: number={eps[0].get('number')} url={eps[0].get('url')}")
    print()
