import json, sys, urllib.request

data = json.loads(urllib.request.urlopen("http://localhost:8099/api/content").read())

types = {}
statuses = {}
has_sites = has_episodes = has_cover = has_anilist = 0

for x in data:
    t = x.get("type", "?")
    s = x.get("status", "?")
    types[t] = types.get(t, 0) + 1
    statuses[s] = statuses.get(s, 0) + 1
    if x.get("sites"): has_sites += 1
    if x.get("episodes"): has_episodes += 1
    if x.get("cover_url"): has_cover += 1
    if x.get("external_id"): has_anilist += 1

print("=== GENEL ===")
print("Toplam:", len(data))
print("Tipler:", types)
print("Durumlar:", statuses)
print()
print("=== VERİ DOLULUK ===")
print(f"Sites var: {has_sites}/{len(data)}")
print(f"Episodes var: {has_episodes}/{len(data)}")
print(f"Cover var: {has_cover}/{len(data)}")
print(f"AniList ID var: {has_anilist}/{len(data)}")

print()
print("=== ANIME ===")
for a in [x for x in data if x["type"] == "anime"][:10]:
    sites = [s.get("site_url","") for s in a.get("sites",[])]
    print(f"  [{a['id']}] {a['title']}")
    print(f"       status={a['status']} | anilist_id={a.get('external_id','YOK')} | eps={len(a.get('episodes',[]))} | sites={sites[:2]}")

print()
print("=== MANHWA ===")
manhwa_list = [x for x in data if x["type"] == "manhwa"]
print(f"  Toplam manhwa: {len(manhwa_list)}")
for m in manhwa_list[:5]:
    sites = [s.get("site_url","") for s in m.get("sites",[])]
    print(f"  [{m['id']}] {m['title']} | sites={sites[:2]}")

print()
print("=== GAME ===")
for g in [x for x in data if x["type"] == "game"]:
    print(f"  [{g['id']}] {g['title']} | status={g['status']} | eps={len(g.get('episodes',[]))}")

print()
print("=== EPISODES VAR OLANLAR ===")
eps_list = [x for x in data if x.get("episodes")]
print(f"  Toplam episode'lu içerik: {len(eps_list)}")
for x in eps_list[:5]:
    ep = x["episodes"][0]
    print(f"  [{x['id']}] {x['title']} ({x['type']}) - {len(x['episodes'])} episode")
    print(f"       ilk ep keys: {list(ep.keys())}")
