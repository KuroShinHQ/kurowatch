"""Deep investigation of Nano Machine sync issues"""
import httpx

api = httpx.Client(base_url="http://localhost:8099", timeout=30)

# Get Nano Machine details
r = api.get("/api/content/18")
c = r.json()
print(f"Title: {c.get('title')}")
print(f"Type: {c.get('type')}")
print(f"Total chapters: {c.get('total_chapters')}")
print(f"External ID: {c.get('external_id')}")
print(f"Anilist ID: {c.get('anilist_id')}")
print(f"Sites:")
for s in (c.get("sites") or []):
    print(f"  name={s.get('site_name')} url={s.get('site_url')} primary={s.get('is_primary')}")

# Get episodes
r2 = api.get("/api/content/18/episodes")
eps = r2.json()
print(f"\nTotal episodes: {len(eps)}")
# Check first 3 and last 3
for ep in eps[:5]:
    print(f"  Ep {ep['number']}: url={ep.get('url')} watched={ep.get('is_watched')}")
print("  ...")
for ep in eps[-3:]:
    print(f"  Ep {ep['number']}: url={ep.get('url')} watched={ep.get('is_watched')}")

# Check if any episodes have non-ragnarscans URLs
from collections import Counter
domains = Counter()
for ep in eps:
    url = ep.get("url") or ""
    if "ragnarscans" in url:
        domains["ragnarscans.com"] += 1
    elif "mangagezgini" in url:
        domains["mangagezgini.com"] += 1
    elif "mangasehri" in url:
        domains["mangasehri.net"] += 1
    elif url:
        domains["other"] += 1
    else:
        domains["none"] += 1
print(f"\nURL domain distribution: {dict(domains)}")
