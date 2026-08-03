import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else []
print(f"Total items: {len(items)}")
for i in items[:10]:
    eplen = len(i.get("episodes") or [])
    print(f"  ID={i['id']:4d} title='{i['title'][:30]}' ep_count={eplen}")
