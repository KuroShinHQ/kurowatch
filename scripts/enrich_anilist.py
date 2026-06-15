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

    # Zenginleştirilecekler:
    # 1. external_id yok
    # 2. mal: prefix var (AniList ID'si bilinmiyor)
    # 3. type=manga ama AniList'ten manhwa çıkabilir → re-check
    need_enrich = [
        c for c in items
        if not c.get('external_id')
        or str(c.get('external_id', '')).startswith('mal:')
        or (c.get('type') == 'manga')  # manhwa tespiti için yeniden sorgula
    ]
    # game olanları çıkar
    need_enrich = [c for c in need_enrich if c.get('type') != 'game']

    print(f"Zenginleştirilecek: {len(need_enrich)} / {len(items)} içerik\n")

    ok = skipped = 0
    for c in need_enrich:
        cid = c['id']
        title = c['title']
        ctype = c['type']
        ext_id = c.get('external_id', '')
        has_mal = str(ext_id).startswith('mal:')
        has_anilist = ext_id and not has_mal

        print(f"  [{ctype}] {title}", end=' → ')

        # AniList ID varsa direkt detay çek, yoksa başlıkla ara
        if has_anilist:
            # Mevcut AniList ID'si var, sadece type check için detay çek
            try:
                al_id = str(ext_id)
                detail_url = f"/discover?q={urllib.request.quote(title)}&type={'anime' if ctype == 'anime' else 'manga'}"
                # Detay için discover (aynı ID'yi bulmak için)
                result = discover(title, ctype)
                if result and result.get('external_id') == al_id:
                    pass  # normal güncelleme akışı
                elif result and str(result.get('external_id', '')) == al_id:
                    pass
                else:
                    result = result  # farklı bulunsa bile devam
            except Exception:
                result = None
        else:
            result = discover(title, ctype)
        time.sleep(0.4)  # AniList rate limit

        if not result:
            print("bulunamadı")
            skipped += 1
            continue

        patch = {}
        al_type = result.get('type', ctype)

        # external_id yoksa veya MAL prefix ise AniList ID'sini yaz
        if result.get('external_id') and (not ext_id or has_mal):
            patch['external_id'] = result['external_id']

        # Tür düzeltmesi: AniList manhwa diyorsa manga → manhwa yap
        if al_type == 'manhwa' and ctype == 'manga':
            patch['type'] = 'manhwa'
            print(f"[MANHWA TESPİT] ", end='')

        if result.get('cover_url') and not c.get('cover_url'):
            patch['cover_url'] = result['cover_url']
        if result.get('genres'):
            patch['genres'] = result['genres']
        if result.get('total_episodes') and not c.get('total_episodes'):
            patch['total_episodes'] = result['total_episodes']
        if result.get('total_chapters') and not c.get('total_chapters'):
            patch['total_chapters'] = result['total_chapters']
        # NOT: Başlık patch edilmiyor — kullanıcının kendi başlığı korunur

        if not patch:
            print("değişiklik yok")
            skipped += 1
            continue

        r = api_patch(f'/content/{cid}', patch)
        if 'error' in r:
            print(f"HATA: {r['error']}")
        else:
            al_id_out = patch.get('external_id', ext_id or '?')
            new_type = patch.get('type', ctype)
            print(f"✅ [{new_type}] (AniList:{al_id_out})")
            ok += 1

    print(f"\n{'='*50}")
    print(f"✅ Zenginleştirildi/Güncellendi: {ok}")
    print(f"⏭️  Atlandı: {skipped}")

if __name__ == '__main__':
    main()
