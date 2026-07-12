import sys, json
data = json.load(sys.stdin)
for item in data if isinstance(data, list) else []:
    title = item.get('title', '')
    if 'esaret' in title.lower() or 'yuruyen' in title.lower() or 'up izle' in title.lower() or '3 aptal' in title.lower():
        print(f"ID: {item['id']}, Title: {title}")
        for e in (item.get('episodes') or []):
            print(f"  URL: {e.get('url','')[:80]}")
        print()
