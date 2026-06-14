# KuroWatch — Feature Map & Mimari Diyagram

> Bu dosya KuroWatch'un tüm özelliklerinin envanteri.
> Bir özellik silinirse veya kaybolursa → buradan bulunur.
> Her yeni özellik eklendikçe bu dosya güncellenir.

---

## 🗺️ Ekran & Özellik Haritası

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        KUROWATCH APP SHELL                             ║
║                    (index.html — tek SPA sayfası)                      ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ║
║  │  🏠 HOME    │  │  🔍 SEARCH  │  │  🔔 UPDATES │  │  📊 STATS   │  ║
║  │  (ana sayfa)│  │  (arama)    │  │  (bildirim) │  │  (istatistik│  ║
║  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  ║
║         │                │                 │                │          ║
║  ┌──────▼──────────────────────────────────────────────────▼──────┐   ║
║  │                    ⚙️ SETTINGS (ayarlar)                       │   ║
║  └────────────────────────────────────────────────────────────────┘   ║
║                                                                        ║
║  ┌────────────────────────────────────────────────────────────────┐   ║
║  │               📋 DETAIL (içerik detay — overlay)               │   ║
║  └────────────────────────────────────────────────────────────────┘   ║
║                                                                        ║
║  ┌────────────────────────────────────────────────────────────────┐   ║
║  │               ➕ ADD MODAL (ekleme formu — overlay)             │   ║
║  └────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 Ekran Bazlı Özellik Listesi

### 1. 🏠 HOME — Ana Sayfa
```
┌─────────────────────────────────────────────────────┐
│ HOME SCREEN                                         │
│ Dosya: frontend/index.html #home-screen             │
│        frontend/app.js → renderHome()               │
│        backend/routers/content.py GET /api/content  │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Filter Chips (yatay kaydır)                     │
│     - Tümü / 🎬Anime / 📖Manga / 📱Manhwa / 🎮Oyun │
│     - İzliyor / Tamamlandı / Askıda / ...           │
│     → GET /api/content?type=anime&status=watching   │
│                                                     │
│ [B] Poster Grid                                     │
│     - 2 sütun (mobil) / 3 (tablet) / 5 (PC)        │
│     - Varsayılan sıra: puan azalan                  │
│     - Kartlar: 2:3 dikey poster                     │
│                                                     │
│ [C] Content Card (her kart)                         │
│     - Kapak resmi (lazy load, error fallback)       │
│     - Sol tip renk şeridi (4px)                     │
│     - Sağ üst: tip ikon badge (🎬📖📱🎮)            │
│     - Sol üst: update badge "+N SiteName" (koşullu) │
│     - Border glow (yeni bölüm varsa)                │
│     - Alt overlay: başlık + ★puan + progress bar    │
│     - Hover: scale(1.03) + haptic.snap()            │
│     - Tıklama → DETAIL ekranı aç                   │
│                                                     │
│ [D] Boş Durum                                       │
│     - Hiç içerik yoksa: ikon + "Ekle" butonu        │
│                                                     │
│ [E] Sıralama                                        │
│     - Varsayılan: puan azalan                       │
│     - (gelecek: sıralama menüsü)                    │
└─────────────────────────────────────────────────────┘
```

### 2. 🔍 SEARCH — Arama
```
┌─────────────────────────────────────────────────────┐
│ SEARCH SCREEN                                       │
│ Dosya: frontend/index.html #search-screen           │
│        frontend/app.js → renderSearch()             │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Arama Kutusu (üstte sabit)                      │
│     - Placeholder: "Search title..."                │
│     - Focus: cyan border, haptic.light()            │
│                                                     │
│ [B] Sekme 1: KÜTÜPHANEMi                           │
│     → GET /api/content?q=...                        │
│     - Filtre: tip + durum chip'leri                 │
│     - Sonuç: aynı poster grid                       │
│                                                     │
│ [C] Sekme 2: KEŞFET                                 │
│     → backend/scraper/anilist.py search()           │
│     → backend/scraper/igdb.py search()              │
│     - Tür chip'leri (AniList genres)                │
│     - Sonuç: liste (küçük poster + başlık + yıl)    │
│     - "Ekle +" butonu → ADD MODAL açar              │
│     - Tür seçince: GET /api/discover?genre=action   │
└─────────────────────────────────────────────────────┘
```

### 3. ➕ ADD MODAL — İçerik Ekleme
```
┌─────────────────────────────────────────────────────┐
│ ADD MODAL (bottom sheet / centered modal)           │
│ Dosya: frontend/index.html #add-modal               │
│        frontend/app.js → openAddModal()             │
│        backend/routers/content.py POST /api/content │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Adım 1: API Arama                               │
│     - "Search title..." canlı arama                 │
│     - AniList / IGDB API'den sonuçlar               │
│     - Seçince form otomatik dolar                   │
│     - "Manuel Ekle" link'i (API bulamazsa)          │
│                                                     │
│ [B] Adım 2: Form                                    │
│     - Başlık (text, İngilizce)                      │
│     - Tip: [Anime][Manga][Manhwa][Game]             │
│     - Durum: dropdown (6 seçenek)                   │
│     - Puan: slider 0–10, adım 0.1 (canlı değer)    │
│     - Kapak URL: opsiyonel override                 │
│     - Siteler: tekrarlı satır [ad][url][☆][✕]      │
│       "+ Site Ekle" butonu                          │
│     - Oyun için: % ilerleme (opsiyonel)             │
│     - Notlar: textarea + spoiler toggle             │
│                                                     │
│ [C] Kaydet                                          │
│     → POST /api/content (metadata + sites)          │
│     → haptic.heavy() + success animasyonu           │
│     → Ana sayfaya yönlendir                         │
└─────────────────────────────────────────────────────┘
```

### 4. 📋 DETAIL — İçerik Detay
```
┌─────────────────────────────────────────────────────┐
│ DETAIL SCREEN (full screen overlay)                 │
│ Dosya: frontend/index.html #detail-screen           │
│        frontend/app.js → openDetail(id)             │
│        backend/routers/content.py GET /api/content/{id}│
│        backend/routers/episodes.py                  │
│        backend/routers/sites.py                     │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Hero Kapak                                      │
│     - 40vh yükseklik, full width                    │
│     - Geri ← butonu (floating)                      │
│     - Düzenle ✏️ butonu (floating)                  │
│                                                     │
│ [B] İçerik Bilgisi                                  │
│     - Başlık (bold, büyük)                          │
│     - Tip badge + Durum badge                       │
│     - ★ interaktif yıldız (10 yarım yıldız)         │
│       → PATCH /api/content/{id} {score: x}         │
│     - "8.5 / 10" sayısal gösterim                   │
│                                                     │
│ [C] İlerleme                                        │
│     - "Episode 87 / 139" büyük progress bar         │
│     - "Sonraki Bölümü İşaretle ✓" butonu            │
│       → PATCH /api/content/{id} {my_progress: +1}  │
│       → haptic.medium()                             │
│     - Hızlı slider: "87. bölüme kadar izledim"      │
│       → toplu güncelleme                            │
│                                                     │
│ [D] Sekmeler                                        │
│                                                     │
│  SEKMEi: BÖLÜMLER                                   │
│     - Bölüm listesi (scroll)                        │
│     - Her satır: no + başlık + ✓ checkbox           │
│     - İzlendi: muted + ✓ / İzlenmedi: normal        │
│     → PATCH /api/episodes/{id}/watch               │
│     → haptic.medium()                               │
│                                                     │
│  SEKME: SİTELER                                     │
│     - Her satır: favicon + ad + son EP + "Aç →"    │
│     - Birincil site: ★ işareti                      │
│     - Farklı EP sayısı: vurgulu satır               │
│     → Tıklama: window.open(site.url)               │
│                                                     │
│  SEKME: NOTLAR                                      │
│     - Yorum textarea                                │
│     - "Spoiler İçeriyor" toggle                     │
│     - Spoiler açıkken not bulanık → "Göster" butonu │
│     → PATCH /api/content/{id} {note, is_spoiler}   │
└─────────────────────────────────────────────────────┘
```

### 5. 🔔 UPDATES — Güncellemeler
```
┌─────────────────────────────────────────────────────┐
│ UPDATES SCREEN                                      │
│ Dosya: frontend/index.html #updates-screen          │
│        frontend/app.js → renderUpdates()            │
│        backend/routers/episodes.py GET /api/updates │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Header                                          │
│     - "Güncellemeler" başlık                        │
│     - "Şimdi Kontrol Et ↻" butonu                  │
│       → POST /api/check-updates                     │
│       → loading spinner                             │
│                                                     │
│ [B] Güncelleme Listesi (yeniden eskiye)             │
│     - Her satır: küçük kapak + başlık               │
│       + "EP 1150 gogoanime'de" + "2 saat önce"      │
│     - Okunmamış: sol cyan border + parlak bg        │
│     - Okunmuş: muted                                │
│     - Tıklama → DETAIL ekranı                       │
│     → PATCH /api/updates/{id}/read                 │
│                                                     │
│ [C] Boş Durum                                       │
│     - "Henüz güncelleme yok. Kontrol Et ↻"          │
└─────────────────────────────────────────────────────┘
```

### 6. 📊 STATS — İstatistik
```
┌─────────────────────────────────────────────────────┐
│ STATS SCREEN                                        │
│ Dosya: frontend/index.html #stats-screen            │
│        frontend/app.js → renderStats()              │
│        backend/routers/tracking.py GET /api/stats   │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Özet Kartları (yatay 3'lü)                      │
│     - "Toplam: 847 saat" (tüm tipler)               │
│     - "Kütüphane: 143 içerik"                       │
│     - "Ort. Puan: 8.3"                              │
│                                                     │
│ [B] Tip Dağılımı (donut chart — CSS/SVG)            │
│     - Anime / Manga / Manhwa / Oyun saat oranı      │
│                                                     │
│ [C] Durum Dağılımı (bar chart — CSS)                │
│     - İzliyor / Tamamlandı / Askıda / ...           │
│                                                     │
│ [D] Puan Dağılımı (histogram — CSS)                 │
│     - 1-10 arası kaç tane her skordan              │
│                                                     │
│ [E] En Çok Tür (tag cloud)                          │
│     - Puan × içerik sayısı büyüklüğü               │
└─────────────────────────────────────────────────────┘
```

### 7. ⚙️ SETTINGS — Ayarlar
```
┌─────────────────────────────────────────────────────┐
│ SETTINGS SCREEN                                     │
│ Dosya: frontend/index.html #settings-screen         │
│        frontend/app.js → renderSettings()           │
│        backend/routers/sync.py                      │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Senkronizasyon                                  │
│     - "Kütüphaneyi Dışa Aktar" → GET /api/export   │
│       (kurowatch_backup.json indirir)               │
│     - "Kütüphaneyi İçe Aktar" → file picker        │
│       → POST /api/import                            │
│       → Çakışma varsa: conflict modal               │
│                                                     │
│ [B] API Kimlik Bilgileri                            │
│     - IGDB Client ID (input)                        │
│     - IGDB Client Secret (input, masked)            │
│     - "Kaydet" → POST /api/settings                │
│                                                     │
│ [C] Varsayılan Süreler (dakika)                     │
│     - Anime bölümü: [24] dk                         │
│     - Manga chapter: [5] dk                         │
│     - Manhwa chapter: [3] dk                        │
│     - Oyun oturumu: [60] dk                         │
│     → POST /api/settings                           │
│                                                     │
│ [D] Kontrol Zamanlaması                             │
│     - "Açılışta güncelleme kontrol et" toggle       │
│                                                     │
│ [E] Hakkında                                        │
│     - "KuroWatch v1.0.0"                            │
└─────────────────────────────────────────────────────┘
```

### 8. ⚡ IMPORT CONFLICT MODAL
```
┌─────────────────────────────────────────────────────┐
│ CONFLICT MODAL (import sırasında)                   │
│ Dosya: frontend/index.html #conflict-modal          │
│        frontend/app.js → showConflicts(items)       │
├─────────────────────────────────────────────────────┤
│ ÖZELLİKLER:                                         │
│                                                     │
│ [A] Başlık: "N çakışma bulundu"                     │
│                                                     │
│ [B] Çakışma Listesi                                 │
│     Her satır:                                      │
│     - İçerik adı                                    │
│     - "Benimki (3 gün önce)" vs "Import (dün)"      │
│     - [Benimkini Koru] [İmportu Kullan] butonları  │
│                                                     │
│ [C] "Tümünü Uygula" → POST /api/import/resolve     │
└─────────────────────────────────────────────────────┘
```

---

## 🔄 Veri Akışı Diyagramı

```
FRONTEND (app.js)              BACKEND (FastAPI :8099)        DIŞ API
─────────────────              ──────────────────────         ────────
                               
Home render ──────────────→ GET /api/content ──────────────→ [SQLite]
                               ↓
Card tıkla ───────────────→ GET /api/content/{id}
                            GET /api/content/{id}/episodes
                            GET /api/content/{id}/sites ──→ [SQLite]

Bölüm ✓ ─────────────────→ PATCH /api/episodes/{id}/watch → [SQLite]

"Ekle" arama ─────────────→ GET /api/search?q=... ─────────→ AniList API
                                                   ─────────→ IGDB API
"Ekle" kaydet ────────────→ POST /api/content ─────────────→ [SQLite]

"Kontrol Et" ─────────────→ POST /api/check-updates
                               ↓ her içerik için:
                               AniList (son bölüm?) ────────→ AniList API
                               IGDB (yeni patch?) ──────────→ IGDB API
                               Scraper (fallback) ──────────→ site URL
                               Fark varsa → updates tablosuna yaz
                               Browser push → navigator.serviceWorker

Export ───────────────────→ GET /api/export ────────────────→ JSON dosya
Import ───────────────────→ POST /api/import ───────────────→ [SQLite]
                               çakışma → frontend conflict modal

Settings kaydet ──────────→ POST /api/settings ─────────────→ config.json
```

---

## 📁 Dosya → Özellik Eşleştirmesi

```
frontend/
  index.html
    #home-screen      → HOME özellikleri [A][B][C][D][E]
    #search-screen    → SEARCH özellikleri [A][B][C]
    #detail-screen    → DETAIL özellikleri [A][B][C][D]
    #updates-screen   → UPDATES özellikleri [A][B][C]
    #stats-screen     → STATS özellikleri [A][B][C][D][E]
    #settings-screen  → SETTINGS özellikleri [A][B][C][D][E]
    #add-modal        → ADD MODAL özellikleri [A][B][C]
    #conflict-modal   → CONFLICT MODAL özellikleri [A][B][C]

  style.css
    :root             → Renk paleti (--kw-* değişkenler)
    .card             → Content Card stili
    .nav-*            → Navigasyon (mobile bottom / desktop sidebar)
    .skeleton         → Skeleton loader shimmer
    .badge-*          → Tip + güncelleme badge'leri
    .progress-bar     → İlerleme çubuğu
    @media            → Responsive breakpoints

  app.js
    haptic.js         → Web Vibration API (6 eylem)
    nav.js            → Sayfa geçişleri
    api.js            → fetch('/api/...') wrapper'lar
    renderHome()      → HOME
    renderSearch()    → SEARCH
    openDetail(id)    → DETAIL
    renderUpdates()   → UPDATES
    renderStats()     → STATS
    renderSettings()  → SETTINGS
    openAddModal()    → ADD MODAL

  manifest.json       → PWA (name, colors, icons)
  sw.js               → Service Worker (cache app shell)

backend/
  main.py             → FastAPI app, startup check-updates
  database.py         → SQLite engine + session
  models.py           → Content, Site, Episode, Tag, Update, Config
  routers/
    content.py        → /api/content CRUD + /api/search
    episodes.py       → /api/episodes + /api/check-updates + /api/updates
    sites.py          → /api/sites
    tags.py           → /api/tags
    tracking.py       → /api/stats + süre hesabı
    sync.py           → /api/export + /api/import + /api/import/resolve
    settings.py       → /api/settings (config.json read/write)
  scraper/
    anilist.py        → AniList GraphQL (arama + son bölüm)
    mal.py            → MAL API (fallback)
    igdb.py           → IGDB (oyun arama + patch kontrol)
    chapter_check.py  → Site scraper (fallback, kullanıcı URL'leri)
  config.json         → IGDB creds + varsayılan süreler (.gitignore'da)
```

---

## 🎯 Stitch AI Panel Planı

### Araştırma Bulgusu
- Stitch 2.0 (Mart 2026): **aynı anda max 5 ekran** üretiyor
- 5 ekran = 1 generation sayılıyor (350/ay hakkın var)
- Standard mod (Gemini Flash): ideation için
- Experimental mod (Gemini Pro): final polish için (50/ay)

### Bizim Planımız (7 ekran → 2 batch)

**BATCH 1 — Ana Akış (Standard mod):**
```
1. HOME     → poster grid + filter chips + content card
2. DETAIL   → hero kapak + bilgi + sekmeler (bölüm/site/not)
3. SEARCH   → arama + 2 sekme (kütüphane/keşfet)
4. UPDATES  → güncelleme listesi
5. STATS    → özet kartlar + donut + bar chart
```

**BATCH 2 — Yardımcı Ekranlar (Experimental mod):**
```
1. ADD MODAL    → bottom sheet + form + API arama
2. SETTINGS     → listeli ayarlar sayfası
3. CONFLICT MODAL → import çakışma çözümü
```

### Stitch'e Verme Stratejisi
```
Adım 1: BATCH 1 promptu ver (DESIGN.md "Stitch AI Final Prompt" bölümü)
        Standard mod → 5 ekran birden üret

Adım 2: Çıktıyı incele → beğenilmeyen kısımları yeniden prompt'la düzelt
        (Canvas üzerinde annotation ekle, AI regenerate eder)

Adım 3: BATCH 2 → Add Modal + Settings + Conflict Modal
        Experimental mod (daha kaliteli)

Adım 4: HTML/CSS export al → frontend/ klasörüne koy
        Post-Stitch checklist uygula (DESIGN.md'de var)
```

---

## ✅ Özellik Tamamlanma Durumu

```
FRONTEND (Stitch sonrası):
[ ] HOME — poster grid
[ ] HOME — filter chips
[ ] HOME — content card (tip şerit, badge, glow, progress)
[ ] HOME — boş durum
[ ] SEARCH — kütüphanem sekmesi
[ ] SEARCH — keşfet sekmesi (tür chip'leri)
[ ] DETAIL — hero kapak + bilgi
[ ] DETAIL — ★ interaktif puan
[ ] DETAIL — progress slider + "sonraki bölüm" butonu
[ ] DETAIL — bölümler sekmesi
[ ] DETAIL — siteler sekmesi
[ ] DETAIL — notlar + spoiler toggle
[ ] UPDATES — liste + okundu/okunmadı
[ ] UPDATES — "Şimdi Kontrol Et" butonu
[ ] STATS — özet kartlar
[ ] STATS — donut/bar chart (CSS/SVG)
[ ] SETTINGS — export/import
[ ] SETTINGS — API credentials
[ ] SETTINGS — varsayılan süreler
[ ] ADD MODAL — API arama
[ ] ADD MODAL — form (site tekrarlı satır)
[ ] CONFLICT MODAL — çakışma çözümü
[ ] NAV — mobil alt bar
[ ] NAV — PC sol sidebar
[ ] HAPTIC — 6 eylem eşleştirme
[ ] PWA — manifest.json
[ ] PWA — sw.js service worker
[ ] ANIMASYON — spring curve library
[ ] SKELETON — shimmer loader

BACKEND:
[ ] database.py — SQLite async engine
[ ] models.py — 6 ORM model
[ ] routers/content.py — CRUD
[ ] routers/episodes.py — bölüm + güncelleme
[ ] routers/sites.py — site yönetimi
[ ] routers/tags.py — etiket yönetimi
[ ] routers/tracking.py — istatistik
[ ] routers/sync.py — export/import/conflict
[ ] routers/settings.py — config
[ ] scraper/anilist.py — GraphQL
[ ] scraper/mal.py — OAuth fallback
[ ] scraper/igdb.py — Twitch auth
[ ] scraper/chapter_check.py — genel scraper
```
