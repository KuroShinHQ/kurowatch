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
  "check_on_startup": true
}
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
