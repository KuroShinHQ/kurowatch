"""
AniList Zenginleştirme — external_id'si olmayan içerikleri
KuroWatch backend'in /api/discover endpoint'i üzerinden AniList'e arar
ve cover_url, genres, external_id, total_episodes/chapters günceller.
"""
import json, sys, time
import urllib.request

KW = "http://localhost:8099/api"

def api_get(path):
    req = urllib.request.Request(f"{KW}/{path.lstrip('/')}", method='GET')
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def api_patch(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{KW}/{path.lstrip('/')}", data=data,
                                  method='PATCH', headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}

def discover(title: str, ctype: str) -> dict | None:
    # KuroWatch /api/discover → AniList search
    al_type = 'anime' if ctype == 'anime' else 'manga'
    encoded = urllib.request.quote(title)
    try:
        results = api_get(f"/discover?q={encoded}&type={al_type}")
        if results and isinstance(results, list) and len(results) > 0:
            return results[0]
        # manhwa fallback
        if ctype == 'manga':
            results2 = api_get(f"/discover?q={encoded}&type=manhwa")
            if results2 and isinstance(results2, list) and len(results2) > 0:
                return results2[0]
    except Exception:
        pass
    return None

def main():
    items = api_get('/content')
    need_enrich = [c for c in items if not c.get('external_id')]
    print(f"Zenginleştirilecek: {len(need_enrich)} / {len(items)} içerik\n")

    ok = skipped = 0
    for c in need_enrich:
        cid = c['id']
        title = c['title']
        ctype = c['type']

        print(f"  [{ctype}] {title}", end=' → ')
        result = discover(title, ctype)
        time.sleep(0.4)  # AniList rate limit

        if not result:
            print("bulunamadı")
            skipped += 1
            continue

        patch = {}
        if result.get('external_id'):
            patch['external_id'] = result['external_id']
        if result.get('cover_url') and not c.get('cover_url'):
            patch['cover_url'] = result['cover_url']
        if result.get('genres'):
            patch['genres'] = result['genres']
        if result.get('total_episodes') and not c.get('total_episodes'):
            patch['total_episodes'] = result['total_episodes']
        if result.get('total_chapters') and not c.get('total_chapters'):
            patch['total_chapters'] = result['total_chapters']
        # Başlığı AniList'ten al (daha düzgün format)
        if result.get('title') and result['title'] != title:
            patch['title'] = result['title']

        if not patch:
            print("değişiklik yok")
            skipped += 1
            continue

        r = api_patch(f'/content/{cid}', patch)
        if 'error' in r:
            print(f"HATA: {r['error']}")
        else:
            al_id = patch.get('external_id', '?')
            new_title = patch.get('title', title)
            print(f"✅ {new_title} (AniList:{al_id})")
            ok += 1

    print(f"\n{'='*50}")
    print(f"✅ Zenginleştirildi: {ok}")
    print(f"⏭️  Atlandı: {skipped}")

if __name__ == '__main__':
    main()
