"""
KuroWatch — URL Geçmişi İçe Aktarma
medya_kaldigim_yerler.md'den tüm manga/manhwa/anime URL'lerini parse eder,
AniList'ten metadata çeker ve KuroWatch DB'ye toplu ekler.
"""
import re, sys, time, json
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
import urllib.request

KW_API = "http://localhost:8099/api"

# ── URL Pattern'ları ─────────────────────────────────────────────────

# Her pattern: (regex, grup_sırası) → (slug, chapter/ep sayısı)
# ctype: "manga" | "anime" | "series" (western TV)

PATTERNS = [
    # ── MANGA / MANHWA ──────────────────────────────────────────────

    # mangaokutr.com/SLUG-bolum-N[/]
    (re.compile(r'mangaokutr\.com/(.+?)-bolum-(\d+)'), 'manga', 1, 2),
    # mangasehri.net/manga/SLUG/bolum-N/
    (re.compile(r'mangasehri\.net/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # manga-sehri.net/manga/SLUG/bolum-N/
    (re.compile(r'manga-sehri\.net/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # mangatr.net/manga/SLUG/bolum-N/
    (re.compile(r'mangatr\.net/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # mangatr.me/manga/SLUG/bolum-N/
    (re.compile(r'mangatr\.me/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # hayalistic.com.tr/manga/SLUG/bolum-N/
    (re.compile(r'hayalistic\.com\.tr/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # asurascans.com.tr/manga/SLUG/bolum-N/
    (re.compile(r'asurascans\.com\.tr/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # turkcemangaoku.com/manga/SLUG/bolum-N/
    (re.compile(r'turkcemangaoku\.com/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # mangagezgini.com/manga/SLUG/
    (re.compile(r'mangagezgini\.(?:com|dev)/manga/([^/?#]+)/'), 'manga', 1, None),
    # mangawow.com/manga/SLUG/bolum-N/
    (re.compile(r'mangawow\.(?:com|org)/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # ruyamanga.com/manga/SLUG/bolum-N/
    (re.compile(r'ruyamanga\.com/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # majorscans.com/SLUG-bolum-N/
    (re.compile(r'majorscans\.com/([^/?#]+)-bolum-(\d+)'), 'manga', 1, 2),
    # tempestfansub.com/SLUG-N/  (slug = all but last number)
    (re.compile(r'tempestfansub\.com/([^/?#]+)-(\d+)/?$'), 'manga', 1, 2),
    # merlintoon.com/seri/SLUG/bolum-N/
    (re.compile(r'merlintoon\.com/seri/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # golgebahcesi.com/SLUG-bolum-N[-*]/
    (re.compile(r'golgebahcesi\.com/([^/?#]+)-bolum-(\d+)'), 'manga', 1, 2),
    # mangatepesi.com/manga/SLUG/N-bolum/
    (re.compile(r'mangatepesi\.com/manga/([^/?#]+)/(\d+)-bolum'), 'manga', 1, 2),
    # merlinscans.com/manga/SLUG/bolum-N/
    (re.compile(r'merlinscans\.com/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # turkmanga.com.tr/manga/SLUG/bolum-N
    (re.compile(r'turkmanga\.com\.tr/manga/([^/?#]+)/bolum-(\d+)'), 'manga', 1, 2),
    # uzaymanga.com/SLUG-N/
    (re.compile(r'uzaymanga\.com/([^/?#]+)-(\d+)/?$'), 'manga', 1, 2),
    # mangabuddy.com/SLUG/chapter-N/
    (re.compile(r'mangabuddy\.com/([^/?#]+)/chapter-(\d+)'), 'manga', 1, 2),

    # ── ANİME ────────────────────────────────────────────────────────
    # tranimeizle.co/SLUG-N-bolum-izle
    (re.compile(r'tranimeizle\.(?:co|top)/([^/?#]+?)-(\d+)-bolum-izle'), 'anime', 1, 2),
    # tranimeizle.top/anime/SLUG-izle (seri sayfası, bölüm yok)
    (re.compile(r'tranimeizle\.top/anime/([^/?#]+)-izle'), 'anime', 1, None),
    # tranimaci.com/video/SLUG-N-bolum
    (re.compile(r'tranimaci\.com/video/([^/?#]+?)-(\d+)-bolum'), 'anime', 1, 2),
    # diziwatch.net/SLUG-N-sezon-M-bolum/
    (re.compile(r'diziwatch\.net/([^/?#]+?)-(\d+)-sezon-(\d+)-bolum'), 'anime', 1, 3),

    # ── BATI DİZİLERİ ─────────────────────────────────────────────
    # yabancidizi.pro/dizi/SLUG-izle-ID/sezon-S/bolum-E
    (re.compile(r'yabancidizi\.pro/dizi/([^/?#]+?)-izle-\d+/sezon-\d+/bolum-(\d+)'), 'series', 1, 2),
    # dizibox.so/SLUG-sezon-S-bolum-E-izle/
    (re.compile(r'dizibox\.so/([^/?#]+?)-sezon-\d+-bolum-(\d+)-izle'), 'series', 1, 2),
    # hdfilmcehennemi.nl/dizi/SLUG-izle-ID/sezon-S/bolum-E
    (re.compile(r'hdfilmcehennemi\.nl/dizi/([^/?#]+?)-izle-\d+/sezon-\d+/bolum-(\d+)'), 'series', 1, 2),
]

# Atlanacak domainler
SKIP_DOMAINS = {
    'play.google.com', 'pnw.perfectworld.com', 'www.instagram.com',
    'www.capcut.com', 'manga-tr.com'
}


def slug_to_title(slug: str) -> str:
    """magic-emperor → Magic Emperor"""
    # Sonundaki -oku1 / -2 gibi sufixleri sil
    slug = re.sub(r'[-_](oku\d?|v\d|tr|eng)$', '', slug)
    # türkçe özel suffix'leri de sil
    slug = re.sub(r'^\d+-|[-_]\d+$', '', slug)
    return ' '.join(w.capitalize() for w in slug.replace('-', ' ').replace('_', ' ').split())


def parse_md(path: str) -> dict:
    """MD dosyasından unique (slug → {title, ctype, max_chapter, urls}) çıkar"""
    text = Path(path).read_text(encoding='utf-8')
    # Tüm URL'leri bul
    urls = re.findall(r'https?://[^\s|)\]">]+', text)

    entries = defaultdict(lambda: {'ctype': None, 'max_ch': 0, 'urls': [], 'title': ''})

    for url in urls:
        url = url.rstrip('",')
        domain = urlparse(url).netloc.lstrip('www.')
        if any(s in domain for s in SKIP_DOMAINS):
            continue

        for pat, ctype, slug_grp, ch_grp in PATTERNS:
            m = pat.search(url)
            if not m:
                continue
            slug = m.group(slug_grp).rstrip('/')
            # mangagezgini slug içinde alt slug olabilir
            slug = slug.split('/')[0]
            chapter = int(m.group(ch_grp)) if ch_grp and m.group(ch_grp) else 0

            key = f"{ctype}:{slug}"
            e = entries[key]
            e['ctype'] = ctype
            if chapter > e['max_ch']:
                e['max_ch'] = chapter
            if url not in e['urls']:
                e['urls'].append(url)
            if not e['title']:
                e['title'] = slug_to_title(slug)
            break

    return entries


def api(method: str, path: str, body=None):
    url = f"{KW_API}/{path.lstrip('/')}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                  headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'error': str(e)}


def anilist_search(title: str, ctype: str) -> dict | None:
    """AniList'te ara → en iyi eşleşmeyi döndür"""
    if ctype == 'series':
        return None  # AniList'te western dizi yok
    al_type = 'ANIME' if ctype == 'anime' else 'MANGA'
    query = """
    query($search:String,$type:MediaType){
      Page(perPage:1){
        media(search:$search,type:$type,sort:SEARCH_MATCH){
          id title{english romaji} coverImage{large} episodes chapters
          status genres countryOfOrigin
        }
      }
    }"""
    payload = json.dumps({'query': query, 'variables': {'search': title, 'type': al_type}}).encode()
    req = urllib.request.Request(
        'https://graphql.anilist.co', data=payload,
        headers={'Content-Type': 'application/json'}, method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        items = data['data']['Page']['media']
        if not items:
            return None
        m = items[0]
        origin = m.get('countryOfOrigin', 'JP')
        if m['type'] == 'ANIME':
            ct = 'anime'
        elif origin == 'KR':
            ct = 'manhwa'
        else:
            ct = 'manga'
        title_en = (m['title'].get('english') or m['title'].get('romaji') or title)
        return {
            'external_id': str(m['id']),
            'title': title_en,
            'type': ct,
            'cover_url': (m.get('coverImage') or {}).get('large'),
            'total_episodes': m.get('episodes'),
            'total_chapters': m.get('chapters'),
            'genres': m.get('genres', []),
        }
    except Exception:
        return None


def main():
    md_path = "/mnt/c/Kuroshin/kuroshin-downloads/medya_kaldigim_yerler.md"
    if not Path(md_path).exists():
        print(f"HATA: {md_path} bulunamadı")
        sys.exit(1)

    print("🔍 URL'ler parse ediliyor...")
    entries = parse_md(md_path)
    print(f"✅ {len(entries)} unique içerik bulundu\n")

    # Mevcut DB'yi çek (duplicate önlemek için)
    existing = api('GET', '/content')
    if 'error' in existing:
        print(f"HATA: Backend'e erişilemiyor: {existing['error']}")
        sys.exit(1)
    existing_titles = {c['title'].lower() for c in existing}
    existing_ext = {c.get('external_id') for c in existing if c.get('external_id')}

    added = skipped = failed = 0

    for key, e in sorted(entries.items()):
        ctype = e['ctype']
        title = e['title']
        chapter = e['max_ch']
        url = e['urls'][-1] if e['urls'] else None  # en son okunan URL

        print(f"  [{ctype}] {title} (bölüm {chapter})", end=' → ')

        # AniList'te ara
        al = anilist_search(title, ctype)
        time.sleep(0.3)  # rate limit

        if al and al['external_id'] in existing_ext:
            print(f"ZATEN VAR (AniList {al['external_id']})")
            skipped += 1
            continue
        if not al and title.lower() in existing_titles:
            print("ZATEN VAR (başlık eşleşmesi)")
            skipped += 1
            continue

        # Content oluştur
        content_data = {
            'title': al['title'] if al else title,
            'type': al['type'] if al else ('manga' if ctype == 'manga' else ctype),
            'status': 'watching',
            'my_progress': chapter,
            'cover_url': al['cover_url'] if al else None,
            'external_id': al['external_id'] if al else None,
            'total_episodes': al.get('total_episodes') if al else None,
            'total_chapters': al.get('total_chapters') if al else None,
            'genres': al.get('genres', []) if al else [],
        }
        result = api('POST', '/content', content_data)

        if 'id' in result:
            new_id = result['id']
            print(f"✅ eklendi (ID:{new_id})" + (f" AniList:{al['external_id']}" if al else " [no AniList]"))

            # Site URL ekle
            if url:
                site_name = urlparse(url).netloc.lstrip('www.')
                api('POST', f'/content/{new_id}/sites', {
                    'site_name': site_name, 'site_url': url, 'is_primary': True
                })
            added += 1
        else:
            print(f"❌ HATA: {result.get('error', result)}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"✅ Eklendi:  {added}")
    print(f"⏭️  Atlandı: {skipped}")
    print(f"❌ Hatalı:  {failed}")


if __name__ == '__main__':
    main()
