"""
AniList Zenginleştirme — external_id'si olmayan içerikleri
KuroWatch backend'in /api/discover endpoint'i üzerinden AniList'e arar
ve cover_url, genres, external_id, total_episodes/chapters günceller.
"""
import json, re, sys, time
import urllib.request

KW = "http://localhost:8099/api"

_SEASON_RE = [
    re.compile(r'\s*\([Ss]\d+(?:-[Ss]\d+)?\)'),           # (S2), (S2-S3)
    re.compile(r'\s*\(\d+(?:st|nd|rd|th)\s+[Ss]eason\)'),  # (2nd Season)
    re.compile(r'\s*\([Ss]eason\s+\d+\)'),                  # (Season 2)
    re.compile(r'\s*Part\s+\d+$', re.IGNORECASE),           # Part 2
]


def _strip_extras(title: str) -> str:
    """'KonoSuba (S3)' → 'KonoSuba'  |  'The Revenant (Diriliş)' → 'The Revenant'"""
    t = title
    for p in _SEASON_RE:
        t = p.sub('', t)
    t = re.sub(r'\s*\([^)]{4,30}\)$', '', t)  # Parantez içi Türkçe çeviri
    return t.strip()

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

def _discover_one(title: str, al_type: str) -> "dict | None":
    encoded = urllib.request.quote(title)
    try:
        results = api_get(f"/discover?q={encoded}&type={al_type}")
        if results and isinstance(results, list):
            return results[0]
    except Exception:
        pass
    return None


def discover(title: str, ctype: str) -> "dict | None":
    al_type = 'anime' if ctype == 'anime' else 'manga'

    # 1. Normal arama
    r = _discover_one(title, al_type)
    if r:
        return r

    # 2. Sezon marker / Türkçe çeviri temizlenmiş başlık ile tekrar dene
    clean = _strip_extras(title)
    if clean and clean != title:
        time.sleep(0.2)
        r = _discover_one(clean, al_type)
        if r:
            return r

    # 3. Manhwa fallback (manga için)
    if ctype == 'manga':
        r = _discover_one(clean or title, 'manhwa')
        if r:
            return r

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
