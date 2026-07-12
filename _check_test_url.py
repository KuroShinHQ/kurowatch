import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else []
for item in items:
    title = item.get('title', '')
    if '3 idiot' in title.lower() or 'esaret' in title.lower():
        print(f"ID: {item['id']}, Title: {title}")
        for s in (item.get('sites') or []):
            print(f"  Site: {s.get('site_name','')} -> {s.get('site_url','')[:80]}")
        for e in (item.get('episodes') or [])[:1]:
            print(f"  Episode: {e.get('url','')[:80]}")
        print()
