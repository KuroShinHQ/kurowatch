import sys, json
d = json.load(sys.stdin)
print(f"ID: {d.get('id')}, Title: {d.get('title')}")
for e in (d.get('episodes') or []):
    print(f"  Episode URL: {e.get('url','')[:80]}")
