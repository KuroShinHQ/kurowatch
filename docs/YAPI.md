# KuroWatch — Yapı ve Gereksinimler

## Proje Amacı
Kişisel **anime / manga / manhwa / oyun** takip uygulaması. 4 içerik tipini tek yerden yönet. Birden fazla siteyi izler, yeni bölüm/güncelleme gelince bildirim verir, kişisel puan/süre/etiket takibi yapar.

---

## 🔬 Araştırma Bulguları (14 Haz 2026)

### Mevcut Tracker Uygulamalarının Sorunları (MAL / AniList / Alternatifler)
Kullanıcıların şikayet ettiği konular — KuroWatch bunları çözecek:

| Şikayet | MAL/AniList'te Durum | KuroWatch Çözümü |
|---|---|---|
| Eski/çirkin UI | MAL özellikle | Modern dark grid UI |
| Çoklu site takibi yok | Yok | Her içeriğe N site eklenir |
| Offline çalışmıyor | Yok | PWA + service worker cache |
| Cross-device sync | Import yok | JSON export/import |
| Oyun takibi yok | Yok | IGDB ile 4. tip |
| Push bildirim yok | Kısmi | PWA Web Push |
| Manhwa desteği zayıf | Yok | Ayrı tip ve API |
| Scraper/custom site | Yok | Kullanıcı site URL girer |

### Kaçırılan Özellikler — Gelecek Fazlar İçin Not
Araştırmada kullanıcıların istediği ama yaygın uygulamalarda olmayan özellikler:

```
FAZA SONRASI (backlog):
- Episode countdown: "One Piece 1151 — 3 gün 4 saat sonra" (AniList nextAiringEpisode)
- Haftalık yayın takvimi görünümü (hangi gün ne çıkıyor)
- MAL/AniList import: mevcut listeni aktar (migration için)
- Öneri motoru: "bunu beğendiysen bunu dene" (AniList recommendations)
- Topluluk özelliği: arkadaş listesi (kapsam dışı - single user)
```

### Claude Code Çalışma Protokolü (Araştırma)
Claude Code'da kullanıcıların yaşadığı sorunlar ve KuroWatch için önlemler:

| Sorun | Önlem |
|---|---|
| Uzun sohbette context kaybı | Her modül bitince DEVAM.md güncelle + commit + yeni sohbet |
| Rate limit hızlı tükeniyor | Büyük değişiklik = ayrı sohbet, küçük değişiklik = aynı sohbet |
| Atomic commit atlanıyor | Her router/model tamamlanınca commit, yarım bırakma |
| N+1 query hatası | SQLAlchemy `selectinload` zorunlu (CLAUDE.md'de var) |
| Async/sync karışımı | Her endpoint `async def`, her DB çağrısı `await` (tip kontrolü ile) |
| Import döngüsü | models.py hiçbir router import etmez |

---

### İçerik Tipleri
| Tip | API Kaynağı | Badge |
|---|---|---|
| Anime | AniList → MAL fallback | 🎬 |
| Manga | AniList → scraper fallback | 📖 |
| Manhwa | AniList → scraper fallback | 📱 |
| Oyun | IGDB (Twitch) | 🎮 |

---

## 📺 Takip Edilen Siteler

Her içerik için birden fazla site eklenebilir. Birincil site (is_primary=true) tıklandığında açılır; diğerleri alternatif olarak listelenir.

### Anime İzleme Siteleri
<!-- Buraya izlediğin anime sitelerini ekle -->
| Site Adı | URL | Notlar |
|---|---|---|
|  |  |  |

### Manga / Manhwa Okuma Siteleri
<!-- Buraya okuduğun manga/manhwa sitelerini ekle -->
| Site Adı | URL | Notlar |
|---|---|---|
|  |  |  |

### Yeni Bölüm Kontrolü — Scraper Önceliği
```
1. AniList API     → resmi veri (anime için en güvenilir)
2. MAL API         → alternatif metadata
3. chapter_check.py scraper → API'de yoksa bu siteleri tara:
   - (kullanıcı site URL'lerini ayarlardan girer — genel scraper altyapısı)
```

---

## 🧠 Backend Kararları (Soru-Cevap Netleşti — 14 Haz 2026)

### Metadata ve Ekle
- Yeni içerik: AniList/IGDB API önce, bulamazsa manuel form
- Başlık: İngilizce (AniList `title.english`)
- Kapak: API'den gelir, kullanıcı URL ile override edebilir (dosya yükleme YOK — sync sorun)

### Güncelleme Kontrolü
- Uygulama açılışında otomatik kontrol (FastAPI startup event)
- Manuel "Yenile" butonu (Updates sayfasında → `POST /api/check-updates`)
- APScheduler arka plan: YOK — startup event + manuel buton yeterli (single user)

### Bildirimler
- Tarayıcı push (PWA Web Push API)
- Uygulama içi: Updates sayfası listesi + kart badge
- Telegram: YOK

### Site Sistemi
- Her içerik için N site (kullanıcı manuel girer: isim + URL + is_primary)
- Her site: `latest_episode` veya `latest_chapter` alanı (scraper günceller)
- Kart badge: yeni bölüm olan site otomatik açılır; yeni yoksa birincil site
- Detay Sites tab: her site → site adı + en son bölüm + "Open →"

### İlerleme Takibi
- `my_progress` (int): kaçıncı bölüm/chapter'a kadar izledim/okudum
- Süre hesabı: `my_progress × default_duration` (config'den)
- Oyunlar: `status` (6 seçenek) + `my_progress_pct` (0-100, opsiyonel)

### Bölüm İşaretleme (ikisi aynı `my_progress`'i günceller)
- Slider: "EP 87'ye kadar izledim" → toplu güncelleme
- Tek tek: her bölüm checkbox → `my_progress` otomatik güncellenir

### Durum Etiketleri
```python
STATUS = ["watching", "completed", "on_hold", "dropped", "planning", "rewatching"]
```

### Etiket Sistemi
- `tag_type = 'api'`: AniList genres (Action, Romance, Isekai...)
- `tag_type = 'user'`: kullanıcının kendi etiketleri
- ContentTag: many-to-many

### Keşfet Arama
- AniList GraphQL: `media(search: "...", genre_in: [...])`
  - **Manhwa ayrımı:** AniList'te manhwa = `type: MANGA, countryOfOrigin: KR`
  - Anime: `type: ANIME` | Manga: `type: MANGA, countryOfOrigin: JP` | Manhwa: `type: MANGA, countryOfOrigin: KR`
  - **Rate limit: 90 req/dakika** → check-updates'te her istek arasına 0.7s delay ekle
  - **⚠️ Manga nextChapter yok:** `nextAiringEpisode` sadece anime. Manga/manhwa güncelleme tespiti:
    `API.chapters` > `DB.total_chapters` → yeni bölüm var (AniList günlük günceller, yeterli)
- IGDB: `search "..."; fields name,cover.image_id,genres.name,rating;`
  - ⚠️ Cover URL: `https://images.igdb.com/igdb/image/upload/t_cover_big/{image_id}.jpg`
  - Token: `POST https://id.twitch.tv/oauth2/token?client_id=X&client_secret=Y&grant_type=client_credentials`
  - **Token ömrü: ~60 gün** → config.json'a `igdb_token` + `igdb_token_expires_at` sakla, expire olunca refresh
- Tür öneri: AniList genre listesi → click → top results
- **MangaDex (FAZ-2 scraper):** `GET https://api.mangadex.org/manga?title=X` → id bul →
  `GET https://api.mangadex.org/manga/{id}/feed?limit=1&order[chapter]=desc` → son chapter

### Import / Export
- Format: JSON (`{ contents: [...], sites: [...], tags: [...], ... }`)
- Çakışma: aynı `external_id` + farklı `updated_at` → kullanıcıya listele
- Her çakışan öğe için: "Benimki" vs "Import" seçimi

### Config (backend/config.json — gitignore'da)
```json
{
  "igdb_client_id": "",
  "igdb_client_secret": "",
  "igdb_token": "",
  "igdb_token_expires_at": 0,
  "vapid_public_key": "",
  "vapid_private_key": "",
  "duration_anime_ep": 24,
  "duration_manga_ch": 5,
  "duration_manhwa_ch": 3,
  "duration_game_session": 60,
  "check_on_startup": true,
  "default_quality": "720p",
  "max_concurrent_downloads": 2,
  "auto_delete_after_watch": false,
  "daisy_chain_trigger_pct": 80
}
```
- `default_quality`: Global kalite ayarı — tüm indirmeler bu kalitede yapılır
- `max_concurrent_downloads`: Aynı anda max kaç indirme (1/2/3)
- `auto_delete_after_watch`: true → modal yok, otomatik sil | false → "Dosyayı Sil?" modal
- `daisy_chain_trigger_pct`: Bölümün yüzde kaçında N+1 indirme başlatılır (varsayılan %80)
```
- `igdb_token` + `igdb_token_expires_at`: startup'ta kontrol et, expire olduysa Twitch'ten refresh
- `vapid_*`: ilk çalıştırmada `py_vapid` ile otomatik üret, config'e yaz

### Notlar
- `note_text`: plain text
- `note_is_spoiler`: boolean → detail'de bulanık, "Göster" butonu

### i18n (TR/EN Çoklu Dil — KRİTİK, hardcode olmayacak)
```
Yaklaşım: data-i18n HTML attribute + JSON locale dosyaları
  - frontend/locales/tr.json  → {"home": "Ana Sayfa", "add": "Ekle", ...}
  - frontend/locales/en.json  → {"home": "Home", "add": "Add", ...}
  - Varsayılan: TR (localStorage'a kayıtlı)
  - Service worker her iki locale dosyasını cache'ler (offline çalışır)

i18n.js (~40 satır, CDN yok):
  const LOCALES = {};
  let LANG = localStorage.getItem('kw_lang') || 'tr';

  async function loadLocale(lang) {
    if (!LOCALES[lang]) LOCALES[lang] = await fetch(`/locales/${lang}.json`).then(r=>r.json());
    LANG = lang;
    localStorage.setItem('kw_lang', lang);
    applyTranslations();
  }
  function t(key) { return LOCALES[LANG]?.[key] ?? key; }
  function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
    });
  }

HTML kullanımı:
  <button data-i18n="add_content">Ekle</button>  ← otomatik çevrilir

Settings UI: <select id="lang-select"><option value="tr">Türkçe</option><option value="en">English</option></select>
```

### FastAPI Static File + Service Worker Kurulumu
```python
# main.py — SIRA ÖNEMLİ!
app.include_router(content_router, prefix="/api")  # API route'ları ÖNCE
app.include_router(episodes_router, prefix="/api")
# ... diğer router'lar ...
# SON OLARAK static files (catch-all — /api ile çakışmaz)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
```
- `sw.js` → `frontend/sw.js` konumunda → `/sw.js` URL'i → scope = `/` (tüm uygulama)
- Service worker `/api/*` isteklerini network-first yakalar, static dosyaları cache-first

### Web Push (PWA Bildirimleri)
- Kütüphane: `pywebpush` + `py-vapid`
- VAPID key üretimi (ilk çalıştırmada otomatik):
  ```python
  from py_vapid import Vapid
  v = Vapid()
  v.generate_keys()
  # config.json'a kaydet: private_key, public_key
  ```
- `vapid_claims = {"sub": "mailto:local@kurowatch.app"}` (local app için dummy email OK)
- Push subscription: frontend `pushManager.subscribe({applicationServerKey: vapidPublicKey})`
  → subscription JSON → `POST /api/push/subscribe` → config/db'ye kaydet
- Yeni bölüm tespitinde: `webpush(subscription, json.dumps(payload), vapid_private_key=..., vapid_claims=...)`

---

## Klasör Yapısı
```
kurowatch/
├── backend/
│   ├── main.py              ← FastAPI app, CORS, startup (check-updates on_startup)
│   ├── database.py          ← SQLite + SQLAlchemy async engine (aiosqlite)
│   ├── models.py            ← ORM: Content, Site, Episode, Update, Tag, ContentTag
│   ├── routers/
│   │   ├── content.py       ← /api/content CRUD + /api/discover
│   │   ├── episodes.py      ← /api/episodes + /api/check-updates + /api/updates
│   │   ├── sites.py         ← /api/sites
│   │   ├── tags.py          ← /api/tags
│   │   ├── sync.py          ← /api/export + /api/import + /api/import/resolve
│   │   └── settings.py      ← /api/settings GET/POST (config.json)
│   ├── scraper/
│   │   ├── anilist.py       ← AniList GraphQL (anime/manga/manhwa + countryOfOrigin)
│   │   ├── mal.py           ← MAL OAuth2 PKCE fallback (localhost redirect)
│   │   ├── igdb.py          ← IGDB Twitch auth + cover URL fix
│   │   └── chapter_check.py ← Regex heuristik scraper (MVP)
│   └── requirements.txt
├── frontend/               ← Stitch AI çıktısı buraya gelecek
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/
│   ├── DEVAM.md             ← Handoff (her commit sonrası güncelle)
│   └── YAPI.md              ← Bu dosya
└── memory/
    └── kurowatch.db         ← SQLite veritabanı (.gitignore'da)
```

## Veri Modeli
```
Content (içerik)
  id, title, type (anime/manga/manhwa/game), cover_url
  external_id (AniList/IGDB id — nullable)
  status (watching/completed/on_hold/dropped/planning/rewatching)
  total_episodes, total_chapters
  my_progress (int — kaçıncı bölüme kadar)
  my_progress_pct (int 0-100 — oyunlar için, nullable)
  my_score (REAL, nullable — 0.0–10.0, null = puan verilmemiş)
  note_text (text, nullable)
  note_is_spoiler (bool, default false)
  added_at, updated_at

Site (izleme/okuma siteleri)
  id, content_id (FK), site_name, site_url
  is_primary (bool)
  latest_known_ep (int, nullable)  ← scraper günceller

Episode (bölüm listesi — API/scraper'dan dolan)
  id, content_id (FK)
  number (int), title (text, nullable), url (text, nullable)
  is_watched (bool, default false), watched_at (datetime, nullable)
  is_new (bool, default false — badge için)

Update (yeni bölüm bildirimleri)
  id, content_id (FK)
  episode_number (int), site_name (text)
  detected_at (datetime), is_read (bool, default false)

Tag (etiket)
  id, name, tag_type ('api' | 'user'), color (text, nullable)

ContentTag (many-to-many)
  content_id, tag_id

# TrackingSession → MVP KAPSAMI DIŞI
# Süre hesabı: my_progress × config.duration_* (tahmini)
# İleride eklenebilir (FAZ-2+)
```

## API Endpoints (planlanan)
```
# İçerik CRUD
GET    /api/content               ← liste (filtre: type, status, tag, q)
POST   /api/content               ← yeni içerik ekle
GET    /api/content/{id}          ← detay + siteler + bölümler
PATCH  /api/content/{id}          ← güncelle (puan, not, status, my_progress)
DELETE /api/content/{id}          ← sil

# Site
POST   /api/content/{id}/sites    ← site ekle
DELETE /api/sites/{id}            ← site sil

# Bölümler
GET    /api/content/{id}/episodes ← bölüm listesi
PATCH  /api/episodes/{id}/watch   ← izlendi/okundu işaretle

# Güncelleme bildirimleri
GET    /api/updates               ← tüm güncellemeler (yeniden eskiye)
PATCH  /api/updates/{id}/read     ← okundu işaretle
POST   /api/check-updates         ← manuel tara (tüm içerikler)

# Etiket
GET    /api/tags                  ← tüm etiketler
POST   /api/tags                  ← yeni etiket

# Keşfet (dış API proxy)
GET    /api/discover?q=X&type=anime        ← AniList/IGDB arama
GET    /api/discover?genre=action&type=anime ← tür bazlı öneri

# Sync
GET    /api/export                ← tüm veri JSON indir
POST   /api/import                ← JSON yükle (çakışmaları tespit et, liste döndür)
POST   /api/import/resolve        ← çakışma kararlarını uygula

# Ayarlar
GET    /api/settings              ← config.json oku
POST   /api/settings              ← config.json yaz (IGDB creds + süreler)

# TrackingSession → MVP DIŞI (removed)
```

## Sync Protokolü (PC ↔ Mobil)
- Her kayıt `updated_at` timestamp taşır
- Export: tek JSON dosyası (tüm tablolar)
- Import: `updated_at` karşılaştır → daha yeni olan kazanır (last-write-wins)
- Çakışma olmaz: tek kullanıcı

## Yeni Bölüm Tespiti
1. **AniList API** → resmi bölüm sayısı çek (`episodes` / `chapters` field)
2. **MAL API** → fallback (AniList bulamazsa)
3. **chapter_check.py scraper** → API'de yoksa kullanıcının eklediği site URL'sini tara
   - **Strateji A (MVP):** Regex tabanlı heuristik — sayfada `Episode 1150`, `Chapter 445` kalıplarını ara
   - **Strateji B (Gelecek):** MangaDex resmi API (ücretsiz, auth yok) ilk desteklenen site
4. Fark varsa → `Update` tablosuna kayıt yaz + `Episode.is_new=True`, badge güncelle
5. APScheduler: YOK — startup event + manuel "Kontrol Et" butonu yeterli

## Kuroshin.bat Entegrasyonu
- `[6] KuroWatch` → backend başlat (`uvicorn backend.main:app --port 8099`)
- `[7] KuroWatch Stop` → taskkill

---

## 🎬 FAZ-3: KuroWatch Player — İndirici + Netflix Deneyimi

> **Kapsam:** Takip edilen sitelerdeki bölümleri/chapter'ları indir →
> uygulama içi oynat/oku → Netflix mekanizmaları → izle-sil döngüsü.
> **Bağımlılık:** FAZ-1 (tracker) tamamlandıktan sonra başlanır.

---

### 3.1 İndirici Altyapısı

**Araçlar (araştırıldı — 14 Haz 2026):**

| Tür | Araç | Kapsam |
|---|---|---|
| Anime video | `yt-dlp` | 1000+ site, aktif geliştirme, Python subprocess |
| Manga chapter | `gallery-dl` | MangaDex, Asura, Flame, 200+ site, Python subprocess |
| Manga (MangaDex özel) | `mangadex-downloader` (PyPI) | Resmi API + yüksek kalite |

**Kurulum:**
```
pip install yt-dlp gallery-dl mangadex-downloader
```

---

### 3.1-A Site Uyumluluk Analizi (Araştırıldı — 14 Haz 2026)

#### ANİME SİTELERİ

**Crunchyroll** (`crunchyroll.com`)
```
Durum: yt-dlp resmi extractor VAR (crunchyroll.py)
Ücretsiz içerik: ✅ Çalışıyor
Premium DRM içerik: ❌ ÇALIŞMIYOR — DRM korumalı (Widevine)
TR altyazı: yt-dlp --write-subs --sub-lang tr,en (varsa çalışır)
Sonuç: Ücretsiz bölümler için yt-dlp yeterli; premium = DRM duvarı
```

**DiziWatch / TrAnimeİzle** (`diziwatch.net`, `tranimeizle.co/.top`)
```
Durum: yt-dlp'de RESMİ extractor YOK
Alternatif: CloudStream (Android app) Türkçe repo var
  → keyiflerolsun/Kekik-cloudstream (GitHub)
  → DiziWatch + TrAnimeİzle extension'ları aktif (2025-2026)
Strateji: yt-dlp generic extractor dene:
  1. Sayfa HTML'inde embed player iframe yakala (vidmoly, streamtape, vb.)
  2. yt-dlp bu embed siteleri destekliyor → iframe URL'ini doğrudan ver
  3. --add-headers "Referer: https://diziwatch.net" gerekebilir
  4. m3u8 stream otomatik tespit (HLS support aktif yt-dlp'de)
Referans: HiAnime için pratikpatel8982/yt-dlp-hianime → custom extractor örneği
```

**TrAnimacı** (`tranimaci.com`)
```
Durum: yt-dlp'de extractor yok — generic + embed yakalaması dene
Strateji: DiziWatch ile aynı yaklaşım
```

#### DİZİ / FİLM SİTELERİ

**Dizibox / YabancıDizi / HDFilmCehennemi**
```
Durum: yt-dlp'de RESMİ extractor YOK
Strateji: Bu siteler embed player kullanır (vidmoly, doodstream, streamtape, filemoon…)
  → yt-dlp bu embed sitelerin ÇOĞUNU destekler
  → Adım 1: Site sayfasından embed iframe URL'ini parse et
  → Adım 2: Bu URL'i yt-dlp'ye ver → video iner
  → Fallback: m3u8 URL'ini DevTools'tan bul → doğrudan yt-dlp'ye ver
```

#### MANGA / MANHWA SİTELERİ

**Madara WordPress Temalı Siteler** (MangaOkuTR, MangaGezgini, MangaŞehri, MangaTR, RüyaManga, TurkceMangaOku, MerlinScans, GölgeBahçesi, MangaWow…)
```
TÜM Bu siteler Madara WordPress teması kullanıyor (araştırma doğruladı).

AJAX Endpoint (tüm Madara siteleri için geçerli):
  POST https://{site}/wp-admin/admin-ajax.php
  Body: action=manga_get_chapter_img_list&chapter_id={chapter_id}
  Response: JSON → { "status": "true", "html": "<div><img src='...'/>..." }
  → HTML parse ile resim URL'leri çıkarılır

Alternatif (bazı Madara sürümlerinde):
  GET https://{site}/manga/{slug}/chapter-{n}/
  → Sayfa HTML'inde data-src= attribute'larına bak (lazy load)

Referans uygulamalar:
  TUVIMEN/wordpress-madara-scraper (GitHub bash script)
  ThuGie/Ultimate-Manga-Scraper--Madara-Enhancements

gallery-dl Madara desteği: Kısmi (bazı siteler için rule var, Türkçe siteler için muhtemelen yok)
Karar: admin-ajax.php Python implementation daha güvenilir
```

**MangaDex** (`mangadex.org`)
```
Durum: gallery-dl ✅ + mangadex-downloader ✅ + resmi API ✅
Tercih: mangadex-downloader (PyPI) — en stabil
```

**AsuraScans TR** (`asurascans.com.tr`)
```
gallery-dl'de Asura Scans desteği var (EN sürümü için)
TR domain için: Madara AJAX dene önce
```

#### AKTİF İNDİRME STRATEJİSİ (Lord Direktifi)

```
ANİME — Daisy Chain:
  Bölüm N oynarken → N+1 indirmeyi kuyruğa ekle (arka plan)
  N+1 başlayınca → N+2 kuyruğa ekle
  Uygulama: download_manager.py → video player "timeupdate" eventi
    → kalan 5dk kala N+1 indirme başlatılır

MANGA — Preload:
  Chapter N okunurken → N+1 indir (arka plan)
  N+1 açılınca → N+2 başlar

"HEPSİNİ İNDİR":
  Seri detay sayfasında "📥 Tümünü İndir [720p]" butonu
  → Tüm bölümleri sıraya ekle, seçili kalitede
  → download_manager kuyruk yönetir (max 2 eşzamanlı)

OTO-SİL:
  İzlendi/okundu → "Dosyayı Sil?" modal
  VEYA auto_delete=True → otomatik sil
  Settings: toplam disk kullanımı göster + "Tümünü Temizle"
```

**Klasör yapısı (downloads/ — .gitignore'da):**
```
downloads/
├── anime/
│   └── {content_id}/
│       └── ep_{number}/
│           ├── video.mp4       ← veya .mkv (yt-dlp format)
│           └── subs.vtt        ← subtitle (yt-dlp --write-subs)
└── manga/
    └── {content_id}/
        └── ch_{number}/
            ├── 001.jpg
            ├── 002.jpg
            └── ...
```

**Backend download engine:**
```python
# backend/downloader/stream_finder.py  ← YENİ (embed URL çıkarma katmanı)
import re
from curl_cffi import requests as cf_requests

EMBED_HOSTS = ["vidmoly", "streamtape", "doodstream", "filemoon", "sibnet"]

async def find_embed_url(page_url: str, referer: str = None) -> str | None:
    headers = {"Referer": referer or page_url, "User-Agent": "Mozilla/5.0"}
    r = cf_requests.get(page_url, headers=headers, impersonate="chrome131")
    iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']+)["\']', r.text, re.I)
    for src in iframes:
        if any(h in src for h in EMBED_HOSTS):
            return src
    return None  # → generic yt-dlp dene

# backend/downloader/anime.py
import subprocess, asyncio

QUALITY_MAP = {"360p": 360, "720p": 720, "1080p": 1080, "best": None}

async def download_episode(content_id, ep_num, url, quality="720p"):
    # BUG FIX: quality string → sayı (yt-dlp height integer ister)
    h = QUALITY_MAP.get(quality)
    if h:
        fmt = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/bestvideo+bestaudio/best"
    else:
        fmt = "bestvideo+bestaudio/best"
    out_dir = f"downloads/anime/{content_id}/ep_{ep_num}/"
    cmd = [
        "yt-dlp", url,
        "-f", fmt,
        "--write-subs", "--sub-lang", "tr,en",
        "--embed-subs",
        "-o", f"{out_dir}video.%(ext)s",
        "--newline",  # progress her satırda (WS parse için)
    ]
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    return proc  # WebSocket'e % ilerleme gönderilir

# backend/downloader/manga.py  — ARAÇ KARAR TABLOSU:
# MangaDex        → mangadex-downloader (resmi API, en stabil)
# TR Madara site  → admin-ajax.php Python impl (gallery-dl Madara desteği kısmi)
# Diğer siteler   → gallery-dl dene, fail → admin-ajax.php
async def download_chapter(content_id, ch_num, url, source="madara"):
    out_dir = f"downloads/manga/{content_id}/ch_{ch_num}/"
    if source == "mangadex":
        cmd = ["mangadex-downloader", url, "--output", out_dir]
    elif source == "gallery-dl":
        cmd = ["gallery-dl", url, "-d", out_dir]
    else:  # source == "madara" (varsayılan TR siteler)
        # admin-ajax.php implementasyonu — aşağıda
        return await _download_madara_chapter(url, out_dir)
    proc = await asyncio.create_subprocess_exec(*cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    return proc

async def _download_madara_chapter(chapter_url: str, out_dir: str):
    # Madara WordPress AJAX endpoint (tüm TR manga siteleri)
    # POST /wp-admin/admin-ajax.php action=manga_get_chapter_img_list&chapter_id={id}
    # Response: {"status":"true","html":"<div><img src='...'/>..."}
    # → HTML parse → resim URL listesi → asyncio.gather ile paralel indir
    pass  # FAZ-3 implementasyonunda doldurulacak
```

**Download manager — kuyruk + WebSocket progress:**
```python
# backend/downloader/manager.py
# Max 2 eşzamanlı download (config.json: "max_concurrent_downloads": 2)
# Her download: id, content_id, ep_num, status (queued/downloading/done/error), progress_%
# WS: ws://localhost:8099/ws/download → {"id": X, "progress": 75, "status": "downloading"}
# BUG FIX: 9099 değil, 8099 (KuroWatch backend portu)
```

---

### 3.2 Download Veri Modeli (FAZ-3 ek tabloları)

```
Download (indirme kuyruğu)
  id, content_id (FK), episode_number
  type ('anime' | 'manga')
  status ('queued' | 'downloading' | 'done' | 'error' | 'deleted')
  progress_pct (int 0-100)
  file_path (text)        ← ininen dosya konumu
  file_size_mb (float)
  quality (text)          ← '360p', '720p', '1080p', 'best' (global config'den gelir)
  trigger ('user' | 'daisy_chain' | 'batch')  ← YENİ: kim başlattı?
    user        → kullanıcı manuel "İndir" dedi
    daisy_chain → bölüm N oynarken N+1 otomatik eklendi
    batch       → "Hepsini İndir" ile eklendi
  auto_delete (bool)      ← global config'den override edilebilir
  queued_at, started_at, finished_at

IntroTimestamp (Netflix intro/outro skip için)
  id, content_id (FK), episode_number
  intro_start (float, saniye), intro_end (float, saniye)
  outro_start (float, saniye, nullable)
  detection_method ('manual' | 'chromaprint' | 'fixed')
  auto_skip (bool)        ← bu bölüm için otomatik atla
```

---

### 3.3 FAZ-3 API Endpoints

```
# İndirici
POST   /api/download              ← yeni indirme kuyruğa ekle
GET    /api/download              ← kuyruk durumu listesi
DELETE /api/download/{id}         ← iptal / sil
POST   /api/download/{id}/retry   ← hata sonrası yeniden dene
WS     /ws/download               ← gerçek zamanlı % ilerleme

# Oynatıcı
GET    /api/player/{content_id}/{ep_num} ← video dosya bilgisi + IntroTimestamp
POST   /api/player/{content_id}/{ep_num}/intro ← intro timestamp kaydet/güncelle
DELETE /api/download/{id}/file    ← dosyayı diskten sil (izledikten sonra)

# Okuyucu
GET    /api/reader/{content_id}/{ch_num} ← chapter görsel listesi (sıralı)
```

---

### 3.4 Netflix Mekanizmaları (Araştırıldı)

**Auto-next episode:**
```javascript
// player.js — video timeupdate event
video.addEventListener('timeupdate', () => {
  const remaining = video.duration - video.currentTime;
  if (remaining <= 30 && !nextOverlayShown) {
    showNextEpisodeOverlay();  // "Sonraki Bölüm" overlay
    nextOverlayShown = true;
  }
  if (remaining <= 10) {
    startCountdown(10, () => playNextEpisode());  // 10sn geri sayım + color wipe
  }
});

// Color wipe: CSS animation, "Next Episode" butonunda dolum efekti
// Kullanıcı tıklarsa → anında geçiş; iptal → clearTimeout
```

**Intro / Outro Skip:**
```javascript
// Timestamp DB'den yüklenir: { intro_start: 8.0, intro_end: 92.0, auto_skip: true }
video.addEventListener('timeupdate', () => {
  if (introTs && video.currentTime >= introTs.intro_start
      && video.currentTime < introTs.intro_end) {
    if (autoSkipEnabled || introTs.auto_skip) {
      video.currentTime = introTs.intro_end;  // otomatik atla
    } else {
      showSkipButton('intro');  // "⏩ İntroyu Atla" butonu göster
    }
  }
  // Outro için aynı mantık
});
```

**İzin sistemi (Settings + per-series):**
```
Global: config.json → "auto_skip_intro": false, "auto_skip_outro": false
Per-series: IntroTimestamp.auto_skip → bölüm bazlı override
UI: Settings > Oynatıcı > "İntroyu Otomatik Atla" toggle
    + Detail > Oynatıcı ayarları > "Bu seri için otomatik atla"
```

**Geri sayım animasyonu:**
```css
/* "Sonraki Bölüm" butonunda soldan sağa dolum */
.next-btn::after {
  content: '';
  position: absolute; inset: 0;
  background: rgba(0,212,255,0.3);
  animation: fillRight 10s linear forwards;
}
@keyframes fillRight {
  from { clip-path: inset(0 100% 0 0); }
  to   { clip-path: inset(0 0% 0 0); }
}
```

---

### 3.5 Intro Tespit Yöntemleri

| Yöntem | Karmaşıklık | Doğruluk | Karar |
|---|---|---|---|
| **Manuel (MVP)** | Düşük | %100 (kullanıcı girer) | ✅ MVP |
| **Sabit skip (ör: ilk 90sn)** | Sıfır | Düşük (her seri farklı) | ❌ Kullanma |
| **Chromaprint audio fingerprint** | Yüksek | Yüksek (%90+) | FAZ-4 |
| **FFmpeg black frame detect** | Orta | Orta | FAZ-4 |
| **AI vision (Gemini/Claude)** | Yüksek + ücretli | Çok yüksek | Yok |

**MVP Akışı:**
1. Bölüm oynatılır, kullanıcı "İntro başlıyor" → `[Başlangıç işaretle]` butonuna basar
2. "İntro bitiyor" → `[Bitiş işaretle]` → timestamp DB'ye kaydedilir
3. Aynı seri sonraki bölümde: "Bu bölüm için aynı timestamp dene?" → Evet → oto-uygula

---

### 3.6 Manga / Manhwa Okuyucu

**Okuma modları:**
```
Webtoon (dikey scroll)  — manhwa için (uzun şerit)
Sayfa bazlı (tek/çift) — manga için (soldan sağa)
Tam ekran              — immersive mod
```

**Klavye / swipe:**
```
→ veya D          → sonraki sayfa
← veya A          → önceki sayfa
Space             → sonraki sayfa
F                 → tam ekran toggle
Ctrl+→            → sonraki chapter
Mobil swipe left  → sonraki sayfa
```

**Auto-next chapter:**
Son sayfada: "Sonraki Bölüm: Ch. {n+1}" overlay →
5sn geri sayım → otomatik yükle (auto_next_chapter toggle)

**Görüntü sunucu:**
```python
# backend/routers/reader.py
@router.get("/api/reader/{content_id}/{ch_num}")
async def get_chapter_images(content_id, ch_num):
    path = f"downloads/manga/{content_id}/ch_{ch_num}/"
    images = sorted(Path(path).glob("*.jpg"))
    # /api/reader/files/{path} → static file serve
    return {"images": [f"/api/reader/files/{img}" for img in images]}
```

---

### 3.7 Kalite Seçimi ve İzle-Sil Döngüsü

**Kalite seçenekleri (anime):**
```
360p  → mobil veri tasarrufu (~200MB/ep)
720p  → standart (~700MB/ep)
1080p → tam HD (~1.5GB/ep)
best  → en iyi mevcut kalite (yt-dlp default)
```

**İzle-Sil döngüsü:**
```
İndir → İzle → Bölüm bitti → "Dosyayı Sil?" modal
  [Sil ve Devam]  → dosya silinir, progress +1
  [Tut]           → dosya kalır, sonra Settings > Downloads'tan sil
  Auto: Download.auto_delete=True → izlendi işaretlenince otomatik sil
```

**Disk yönetimi:**
- Settings > İndirilenler → toplam disk kullanımı göster
- "Tümünü Temizle" butonu
- Per-series download listesi (inip inmediği, boyutu)

---

### 3.8 FAZ-3 Klasör Yapısı Güncellemesi

```
kurowatch/
├── backend/
│   ├── downloader/
│   │   ├── __init__.py
│   │   ├── stream_finder.py ← YENİ: embed iframe URL çıkarma (curl_cffi)
│   │   │                       → DiziWatch/TrAnimeİzle/Dizibox için
│   │   │                       → vidmoly/streamtape/doodstream iframe parse
│   │   ├── anime.py         ← yt-dlp async wrapper (QUALITY_MAP fix dahil)
│   │   ├── manga.py         ← madara admin-ajax.php + mangadex-downloader + gallery-dl
│   │   └── manager.py       ← kuyruk + WS progress (max 2 eşzamanlı, daisy chain)
│   └── routers/
│       ├── download.py      ← /api/download + /ws/download (port 8099)
│       ├── player.py        ← /api/player (video bilgi + intro timestamps)
│       └── reader.py        ← /api/reader (chapter görseller + static serve)
├── frontend/
│   ├── player.html          ← video player (HTML5 <video> + custom controls)
│   ├── player.js            ← auto-next + intro skip + geri sayım + daisy chain trigger
│   ├── reader.html          ← manga/manhwa okuyucu
│   └── reader.js            ← sayfa navigasyon + webtoon scroll + auto-next ch.
└── downloads/               ← .gitignore'da
    ├── anime/
    └── manga/
```

### 3.9 Kalite Seçimi — Netflix Modeli

```
Global Ayar (config.json: "default_quality": "720p"):
  → Tüm yeni indirmeler bu kaliteyi kullanır
  → Settings > İndirici > Kalite dropdown: 360p / 720p / 1080p / En İyi

yt-dlp format string (QUALITY_MAP):
  "360p"  → bestvideo[height<=360]+bestaudio/best[height<=360]/bestvideo+bestaudio/best
  "720p"  → bestvideo[height<=720]+bestaudio/best[height<=720]/bestvideo+bestaudio/best
  "1080p" → bestvideo[height<=1080]+bestaudio/best[height<=1080]/bestvideo+bestaudio/best
  "best"  → bestvideo+bestaudio/best

NOT: Sabit kalite yoksa (site 720p sunmuyorsa) → bir alt kalite otomatik seçilir.
ffmpeg gerekli (video+audio merge için).

Crunchyroll Premium Uyarısı:
  Premium içerik → DRM (Widevine) → yt-dlp indiremez
  Kullanıcı Crunchyroll sitesi eklerse → indirme butonu yerine "🔒 DRM — Tarayıcıda Aç"
  Sadece ücretsiz bölümler için "İndir" butonu göster
```

### 3.10 Oto-Sil Mantığı (Düzeltildi)

```
config.json: "auto_delete_after_watch": false

false (varsayılan):
  Bölüm bitti → "Dosyayı Sil? [Sil ve Devam] [Tut]" modal
  → Kullanıcı kararı verir

true:
  Bölüm bitti + is_watched = true → otomatik sil (modal yok)
  → Settings'te toggle: "İzledikten Sonra Otomatik Sil"

Her iki durumda:
  Settings > İndirilenler → toplam disk kullanımı (MB/GB)
  Per-seri indirme listesi + "Tümünü Temizle" butonu
  Completed seriler → "Seriyi Temizle" toplu sil seçeneği
```

---

### 3.9 FAZ Haritası (güncellendi)

```
FAZ-1 (MVP)     → Tracker: içerik ekle/takip et, Updates, Stats, i18n
FAZ-2           → MAL OAuth, IGDB/Oyun, MangaDex scraper
FAZ-3           → Player/Downloader: yt-dlp + gallery-dl + Netflix mekanizmaları
FAZ-4           → Chromaprint otomatik intro tespiti, öneri algoritması
```
