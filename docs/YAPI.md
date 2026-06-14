# KuroWatch — Yapı ve Gereksinimler

## Proje Amacı
Kişisel anime/manga/manhwa takip uygulaması. Birden fazla siteyi izler, yeni bölüm gelince bildirim verir, kişisel puan/süre/etiket takibi yapar.

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
   - (sen ekleyeceksin)
```

---

## Klasör Yapısı
```
kurowatch/
├── backend/
│   ├── main.py              ← FastAPI app, CORS, startup
│   ├── database.py          ← SQLite + SQLAlchemy async engine
│   ├── models.py            ← ORM modelleri (Content, Site, Episode, Rating, Tag)
│   ├── routers/
│   │   ├── content.py       ← /api/content CRUD (anime/manga ekle/sil/güncelle)
│   │   ├── tracking.py      ← /api/track (süre, puan, kişisel not)
│   │   ├── sites.py         ← /api/sites (hangi sitelerde takip)
│   │   ├── tags.py          ← /api/tags (etiket/kategori yönetimi)
│   │   ├── episodes.py      ← /api/episodes (bölüm listesi, yeni bölüm flag)
│   │   └── sync.py          ← /api/export + /api/import (JSON dosya sync)
│   ├── scraper/
│   │   ├── anilist.py       ← AniList GraphQL API (anime metadata)
│   │   ├── mal.py           ← MyAnimeList API (alternatif)
│   │   └── chapter_check.py ← Site scraper (yeni bölüm kontrolü)
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
  id, title, type (anime/manga/manhwa), cover_url
  status (watching/reading/paused/dropped/completed)
  total_episodes, total_chapters
  my_score (1-10), my_note (text)
  added_at, updated_at

Site (izleme/okuma siteleri)
  id, content_id (FK), site_name, site_url
  is_primary (ana site mi)
  latest_known_episode/chapter

Episode (bölüm takip)
  id, content_id (FK), site_id (FK)
  number, title, url
  is_watched/read, watched_at
  is_new (flag — badge için)

Tag (etiket)
  id, name, color

ContentTag (many-to-many)
  content_id, tag_id

TrackingSession (süre takip)
  id, content_id, episode_id
  started_at, ended_at, duration_minutes
```

## API Endpoints (planlanan)
```
GET    /api/content          ← liste (filtre: type, status, tag)
POST   /api/content          ← yeni içerik ekle
GET    /api/content/{id}     ← detay + siteler + bölümler
PATCH  /api/content/{id}     ← güncelle (puan, not, status)
DELETE /api/content/{id}     ← sil

POST   /api/content/{id}/sites    ← site ekle
DELETE /api/sites/{id}            ← site sil

GET    /api/content/{id}/episodes ← bölüm listesi
PATCH  /api/episodes/{id}/read    ← okundu/izlendi işaretle

POST   /api/track/start      ← süre başlat
POST   /api/track/stop       ← süre durdur

GET    /api/tags             ← tüm etiketler
POST   /api/tags             ← yeni etiket

GET    /api/export           ← tüm veri JSON indir
POST   /api/import           ← JSON yükle (merge: son değişiklik kazanır)

GET    /api/check-updates    ← tüm takip edilen içerikleri tara (yeni bölüm?)
```

## Sync Protokolü (PC ↔ Mobil)
- Her kayıt `updated_at` timestamp taşır
- Export: tek JSON dosyası (tüm tablolar)
- Import: `updated_at` karşılaştır → daha yeni olan kazanır (last-write-wins)
- Çakışma olmaz: tek kullanıcı

## Yeni Bölüm Tespiti
1. **AniList API** → resmi bölüm sayısı çek
2. **MAL API** → fallback
3. **chapter_check.py scraper** → API bulamazsa site scraping
4. Fark varsa → `is_new=True`, badge sayısı güncelle
5. APScheduler ile her X saatte otomatik kontrol

## Kuroshin.bat Entegrasyonu
- `[6] KuroWatch` → backend başlat (`uvicorn backend.main:app --port 8099`)
- `[7] KuroWatch Stop` → taskkill
