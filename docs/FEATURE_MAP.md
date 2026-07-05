# KuroWatch — Feature Map & Mimari Diyagram

> Bu dosya KuroWatch'un tüm özelliklerinin envanteri.
> Bir özellik silinirse veya kaybolursa → buradan bulunur.
> Her yeni özellik eklendikçe bu dosya güncellenir.

---

## 🗺️ Ekran & Özellik Haritası

> Son güncelleme: 22 Haz 2026 — mevcut index.html kodu ile uyumlu

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                      KUROWATCH APP SHELL (index.html)                      ║
║              Mobil: Bottom Nav (6 öğe)  |  PC: Sol Sidebar                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       ║
║  │🏠 HOME   │ │🔍 SEARCH │ │➕ EKLE   │ │🔔 UPDATES│ │📥 İNDİR  │       ║
║  │(ana sayfa│ │(kütüphane│ │(add modal│ │(bildirim)│ │(downloads│       ║
║  │ + filtre)│ │+ keşfet) │ │ açar)    │ │          │ │ ekranı)  │       ║
║  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       ║
║                                                                            ║
║  ┌────────────────────────────────────────────────────────────────────┐   ║
║  │  ⚙️ SETTINGS — Stats kısayolu, Arşiv kısayolu, Export/Import,    │   ║
║  │     API (IGDB/MAL), Etiketler, İndirme ayarları, PWA, Push,      │   ║
║  │     Cookies (CF bypass), Hakkında                                 │   ║
║  └────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
║  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ║
║  │ 📋 DETAIL (ekran)  │  │ 📦 ARCHIVE (ekran) │  │ 📊 STATS (ekran)  │  ║
║  │ settings'ten erişim│  │ settings → arşiv   │  │ settings kısayolu │  ║
║  └────────────────────┘  └────────────────────┘  └────────────────────┘  ║
║                                                                            ║
║  MODALLER: ADD (bottom sheet) | EDIT (bottom sheet) | CONFLICT (centered) ║
║            COVER DEBUGGER (centered) | VIDEO PLAYER | MANGA READER        ║
║  OVERLAY:  READ OVERLAY (iframe fullscreen)                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 📋 Ekran Bazlı Özellik Listesi

### 1. 🏠 HOME — Ana Sayfa
```
┌─────────────────────────────────────────────────────┐
│ HOME SCREEN                                         │
│ id: #screen-home                                    │
│ app.js → renderHome()                               │
│ API: GET /api/content?type=X&status=Y&q=Z           │
├─────────────────────────────────────────────────────┤
│ [A] Sayfa İçi Arama Kutusu (#home-search-input)     │
│     - placeholder: "Kütüphanende ara..."            │
│     - Yazarken anlık filtre (debounce)              │
│     - Üst kısımda, filtre chip'lerinin üzerinde     │
│                                                     │
│ [B] Filter Chips — Tür (satır 1, yatay kaydır)     │
│     - [TÜM TÜRLER] [ANİME] [MANGA] [MANHWA] [OYUN] │
│     → GET /api/content?type=anime                   │
│                                                     │
│ [C] Filter Chips — Durum (satır 2, yatay kaydır)   │
│     - [TÜMÜ] [İZLİYOR] [TAMAMLANDI] [BEKLEMEDE]    │
│     → GET /api/content?status=watching              │
│                                                     │
│ [D] Poster Grid (#home-library-grid)                │
│     - 2 sütun (mobil) / 4 (md) / 5 (xl PC)         │
│     - aspect-[2/3] dikey poster kartlar             │
│                                                     │
│ [E] Content Card (her kart)                         │
│     - Kapak bg-image (initials fallback)            │
│     - Sol tip renk şeridi (tip rengiyle)            │
│     - Sağ üst: tip badge (TYPE_COLOR)               │
│     - Sol üst: update badge "+N Site" (koşullu)     │
│     - Alt gradient overlay: başlık + puan + bar     │
│     - Hover: scale(1.02) + border cyan              │
│     - Tıklama → openDetail(id)                      │
│                                                     │
│ [F] Boş Durum                                       │
│     - İçerik yok → ikon + mesaj                     │
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
│ ADD MODAL (bottom sheet — 85vh)                     │
│ id: #modal-add  |  açılır: data-modal-open          │
│ app.js → openAddModal(), addSave()                  │
│ API: POST /api/content                              │
├─────────────────────────────────────────────────────┤
│ ADIM 1 (#add-step-1) — AniList/IGDB Arama          │
│   Tip seçici: 🎬Anime 📖Manga 📱Manhwa 🎮Oyun       │
│   Arama kutusu (#add-step1-search-input)            │
│   Sonuç listesi: kapak + başlık + yıl + tip badge   │
│   [Ekle +] buton → Adım 2'ye geç, form dolar        │
│   "Bulamadın mı? Manuel ekle →" → Adım 2 (boş)     │
│                                                     │
│ ADIM 2 (#add-step-2) — Form                         │
│   ← Geri (Adım 1'e), ✕ Kapat                       │
│   Başlık (text)                                     │
│   Tür: [🎬Anime][📖Manga][📱Manhwa][🎮Oyun]         │
│   Durum: dropdown (İzliyor/Tamamlandı/Planlı/Bırak) │
│   Puan: yıldız rating (★ × 10, tamsayı 1-10)        │
│   Kapak URL: opsiyonel text input                   │
│   Gizli alanlar: genres, external_id,               │
│                  total_episodes, total_chapters      │
│   Notlar: textarea                                  │
│                                                     │
│ [Kütüphaneye Ekle] → POST /api/content              │
└─────────────────────────────────────────────────────┘
```

### 4. 📋 DETAIL — İçerik Detay
```
┌─────────────────────────────────────────────────────┐
│ DETAIL SCREEN (tam ekran, slide-up geçiş)           │
│ id: #screen-detail                                  │
│ app.js → openDetail(id)                             │
│ API: GET /api/content/{id}, /episodes, /sites       │
├─────────────────────────────────────────────────────┤
│ [A] Hero Kapak (353px yükseklik)                    │
│     #detail-cover-bg (bg-cover bg-center)           │
│     ← Geri (#detail-cover-bg → data-nav=screen-home)│
│     📤 Cover Yükle butonu (label → file input)      │
│     ✏️ Düzenle (#detail-edit-btn → modal-edit açar) │
│     Tip badge + Durum badge                         │
│     Başlık (#detail-title)                          │
│                                                     │
│ [B] Yıldız Puan (#detail-rating-container)          │
│     10 adet ★ ikon (Material Symbols, tıklanabilir) │
│     "#X / 10" sayısal gösterim (#detail-score-text) │
│     → PATCH /api/content/{id} {my_score: x}        │
│                                                     │
│ [C] İlerleme Kutusu                                 │
│     #detail-progress-current / #detail-progress-total│
│     Tıklanabilir sayı → quick-edit popup açılır     │
│     Quick-edit: [−] [input] [+] [Kaydet]            │
│     % gösterge (#detail-progress-pct)               │
│     Progress bar (#detail-progress-bar)             │
│     Slider (#detail-progress-slider, 0–max)         │
│                                                     │
│ [D] "Sonraki Bölümü İşaretle" butonu (#detail-mark-btn)│
│     → PATCH /api/content/{id} {my_progress: +1}    │
│                                                     │
│ [E] Özet / Synopsis (gizlenebilir)                  │
│     #detail-synopsis-section (display:none default) │
│     Next airing banner + özet paragraph             │
│     "Devamını Gör" toggle                           │
│                                                     │
│ [F] Genres satırı (#detail-genres-row)              │
│     AniList'ten gelen türler (hidden → JS ile açılır)│
│                                                     │
│ [G] Etiketler satırı (#detail-tags-row)             │
│     Kullanıcının oluşturduğu tag'ler                │
│                                                     │
│ [H] Sekmeler (sticky)                               │
│   [Bölümler] [Siteler] [Notlar]                     │
│   onclick: detailSwitchTab()                        │
│                                                     │
│  SEKME: BÖLÜMLER (#detail-tab-episodes)             │
│     Bölüm listesi (virtual scroll, uzun seriler)    │
│     Her satır: no + başlık + ✓ checkbox + İndir btn │
│     → PATCH /api/episodes/{id}/watch               │
│                                                     │
│  SEKME: SİTELER (#detail-tab-sites)                 │
│     Her satır: ikon + ad + "Aç →" butonu            │
│     + Site ekle formu                               │
│                                                     │
│  SEKME: NOTLAR (#detail-tab-notes)                  │
│     Kişisel Notlar textarea (#detail-notes-area)    │
│     "Spoiler Gizle" toggle (#detail-spoiler-toggle) │
│     Blur overlay + "SPOILER GİZLİ" badge            │
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
│        frontend/app.js → renderStats() GET /api/content (JS hesaplama) │
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
│ id: #screen-settings                                │
│ app.js → renderSettings()                           │
│ API: GET/POST /api/settings, /api/export, /api/import│
├─────────────────────────────────────────────────────┤
│ [A] Kısayollar                                      │
│     "İstatistiklerimi Gör" → screen-stats           │
│     "Arşiv" → screen-archive                        │
│                                                     │
│ [B] Veri Bölümü                                     │
│     "Dışa Aktar (JSON)" → GET /api/export           │
│     "İçe Aktar" → modal-conflict açar               │
│                  → POST /api/import                 │
│     "Türleri AniList'ten Güncelle"                  │
│       (#settings-genres-patch-btn)                  │
│     "Cover'ları AniList'ten Zenginleştir"           │
│       (#settings-enrich-covers-btn)                 │
│     "Cover Debugger" → modal-cover-debug açar       │
│       (#settings-cover-debug-btn)                   │
│                                                     │
│ [C] API Kimlik Bilgileri                            │
│     IGDB Client ID + Secret → "Token Yenile"        │
│     MAL Client ID + Secret → "Kaydet"               │
│     MAL OAuth: "MAL'a Bağlan" / "Listemi İçe Aktar"│
│       / "Bağlantıyı Kes" (duruma göre görünür)      │
│     → GET /api/settings, POST /api/settings         │
│                                                     │
│ [D] Etiketler (#tag-list-settings)                  │
│     "Yeni" butonu → #tag-create-form açılır         │
│     Tag oluştur: ad + renk seç (6 renk) + Oluştur   │
│     Mevcut tag'ler: listele + sil                   │
│     → GET/POST /api/tags                            │
│                                                     │
│ [E] İndirme Ayarları (FAZ-3)                        │
│     "Otomatik Sil" toggle (N-1 bölüm sil)          │
│     Manuel kalite: [480p] [720p] [1080p]            │
│     Otomatik (daisy-chain) kalite: ayrı seçenek     │
│     → config.json                                   │
│                                                     │
│ [F] PWA Yükle (koşullu — beforeinstallprompt var)   │
│     #pwa-install-section (hidden → JS açar)         │
│     "Uygulamayı Yükle" → install_mobile ikonu       │
│                                                     │
│ [G] Push Bildirimleri                               │
│     Toggle (#push-toggle-btn)                       │
│     Durum satırı + "Test Bildirimi Gönder"          │
│     → /api/subscribe, /api/push/test                │
│                                                     │
│ [H] Site Cookies (CF bypass)                        │
│     Açıklama: "Get cookies.txt LOCALLY" ext.        │
│     Site seç: [tranimeizle / turkanime / diziwatch  │
│                / Genel]                             │
│     "cookies.txt Yükle" (file input .txt)           │
│     "CAPTCHA ile Cookie Al (Otomatik)"              │
│       (#captcha-browser-btn) → nodriver bypass      │
│     Durum kutusu (#captcha-status-box)              │
│                                                     │
│ [I] Hakkında                                        │
│     "KuroWatch v0.3.0" (#settings-version)          │
│     "Güncelle" butonu (#settings-update-btn)        │
└─────────────────────────────────────────────────────┘
```

### 8. 📦 ARCHIVE — Arşiv
```
┌─────────────────────────────────────────────────────┐
│ ARCHIVE SCREEN                                      │
│ id: #screen-archive                                 │
│ Erişim: Settings → Arşiv                           │
│ API: GET /api/content?status=archived               │
├─────────────────────────────────────────────────────┤
│ [A] Header (sticky)                                 │
│     ← Geri (data-nav=screen-home)                  │
│     "Arşiv" başlık + içerik sayısı badge            │
│                                                     │
│ [B] Arşiv Listesi (#archive-list)                   │
│     Her satır (56px): küçük kapak + başlık + tip badge│
│     "X gün önce arşivlendi" alt başlık             │
│     "Geri Al" butonu → PATCH geri yükle            │
└─────────────────────────────────────────────────────┘
```

### 9. 📥 DOWNLOADS — İndirmeler
```
┌─────────────────────────────────────────────────────┐
│ DOWNLOADS SCREEN                                    │
│ id: #screen-downloads                               │
│ Nav: Bottom nav 5. ikon (download ikonu)            │
│ API: GET /api/download/queue, WS /api/download/ws   │
├─────────────────────────────────────────────────────┤
│ [A] Header                                          │
│     "İndirmeler" + depolama göstergesi              │
│     (#downloads-storage)                            │
│                                                     │
│ [B] Yardım Kutusu                                   │
│     "İçerik detayından → Bölümler → İndir"          │
│                                                     │
│ [C] İndirme Listesi (#downloads-list)               │
│     Her job: başlık + ilerleme bar + % + durum      │
│     Tamamlanan: "▶ Oynat" butonu → video player     │
│     Hatalı: "Tekrar Dene" butonu                    │
│     Boş: emoji + "Henüz indirme yok"                │
│                                                     │
│ [D] Floating Progress (#download-float)             │
│     Sağ alt (bottom:80px, right:12px), fixed        │
│     İndirme devam ederken görünür: ikon + % bar     │
└─────────────────────────────────────────────────────┘
```

### 10. ✏️ EDIT MODAL — İçerik Düzenleme
```
┌─────────────────────────────────────────────────────┐
│ EDIT MODAL (bottom sheet — 80vh)                    │
│ id: #modal-edit  |  açılır: detail-edit-btn         │
│ API: PATCH /api/content/{id}, DELETE /api/content/{id}│
├─────────────────────────────────────────────────────┤
│ Başlık (orijinal) + Türkçe Başlık alanları          │
│ Tür seçici: [🎬Anime][📖Manga][📱Manhwa][🎮Oyun]    │
│ Durum dropdown (İzliyor/Tamamlandı/Planlı/Bırakıldı)│
│ Puan: range slider 0–10 adım 1 + canlı "X / 10"     │
│ Notlar: textarea                                    │
│ Tehlikeli bölge: "Kütüphaneden Sil" (kırmızı btn)   │
│   → DELETE /api/content/{id}                        │
│ [Kaydet] → PATCH /api/content/{id}                  │
└─────────────────────────────────────────────────────┘
```

### 11. ⚡ IMPORT CONFLICT MODAL
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
FRONTEND (app.js / player.js)  BACKEND (FastAPI :8099)        DIŞ API
─────────────────────────────  ──────────────────────         ────────

Home render ──────────────→ GET /api/content ──────────────→ [SQLite]
Card tıkla ───────────────→ GET /api/content/{id}
                            GET /api/content/{id}/episodes ─→ [SQLite]
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
Settings kaydet ──────────→ POST /api/settings ─────────────→ config.json

── FAZ-3 İndirici & Player (15 Haz) ──────────────────────────────────

▶ Oynat (İndir buton) ────→ POST /api/download/start ──────→ yt-dlp
WS progress push ─────────→ WS  /api/download/ws           (ilerleme %)
▶ Oynat (done job) ───────→ GET /api/download/serve/{id}   (range stream)
Altyazı yükle (C tuşu) ──→ GET /api/download/subtitles/{id} (.vtt dosya)
Silme (🗑 buton) ─────────→ DELETE /api/download/{id}      (dosya sil)
Depolama ─────────────────→ GET /api/download/storage      (bytes)
Manga sayfaları ──────────→ GET /api/download/pages/{id}
                            GET /api/download/page/{id}/{i} (tek sayfa)

── FAZ-5 Manga Çevirisi (15 Haz) ──────────────────────────────────────

GPU bilgisi ──────────────→ GET /api/system/gpu                  → nvidia-smi
Çeviri başlat ────────────→ POST /api/translate/{id}/{ep}        → manga_translator subprocess
Çeviri durumu ────────────→ GET  /api/translate/{id}/{ep}
Çeviri progress ──────────→ WS   /api/translate/ws               → sayfa sayfa %
Çevrilmiş sayfa listesi ──→ GET  /api/translate/pages/{id}/{ep}
Çevrilmiş sayfa ──────────→ GET  /api/translate/page/{id}/{ep}/{i}
Sil ──────────────────────→ DELETE /api/translate/{id}/{ep}      (dosyaları siler)
Dil toggle (reader) ──────  _translate.showTranslated/Original() → _reader._render()

── FAZ-4 Chromaprint + FFmpeg Outro (15 Haz) ──────────────────────────

İntro analiz ─────────────→ POST /api/analyze/intro/{id}    → fpcalc → [SQLite]
İntro zamanı ─────────────→ GET  /api/analyze/intro/{id}/{ep}
Skip Intro (player tick) ── video.currentTime karşılaştır → butonu göster
Outro analiz ─────────────→ POST /api/analyze/outro/{id}    → ffmpeg blackdetect → [SQLite]
Outro zamanı ─────────────→ GET  /api/analyze/outro/{id}/{ep}
Skip Outro (player tick) ── video.currentTime >= outro_start → butonu göster
```

## 🎬 Video Player Modal Diyagramı (FAZ-3 — 15 Haz)

```
┌─────────────────────────────────────────────────────────────────────┐
│ MODAL-PLAYER (#modal-player)  z-index:200                           │
│ Normal: fixed inset-0 bg-black flex-col                             │
│ Mini:   fixed bottom-1rem right-1rem 320×200 rounded-xl             │
│ Theater: header opacity:0, hover → görünür                          │
├─────────────────────────────────────────────────────────────────────┤
│ HEADER (#player-header)  transition-all 0.3s                        │
│ [← Geri]  [═══ Başlık (truncate) ═══]  [CC][Blur][🎭][PiP][⊓][⛶] │
│            #player-title                  ↑   ↑   ↑   ↑   ↑   ↑  │
│                                          CC Ambi Th  PiP Mini Full │
├─────────────────────────────────────────────────────────────────────┤
│ VIDEO WRAP (#player-video-wrap)  flex-1 relative                    │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ <canvas id="ambient-canvas">  z:0  blur(40px) saturate(1.8)    │ │
│ │ <video id="player-video">     z:1  controls                    │ │
│ │   <source id="player-source">                                  │ │
│ │   <track id="subtitle-track" kind="subtitles" srclang="tr">    │ │
│ │                                                                 │ │
│ │  [⏭ İntroyu Atla]         [Sonraki bölüm ████░░ 7s  İptal]   │ │
│ │  #skip-intro-btn          #autonext-overlay                    │ │
│ │  bottom-16 right-6        bottom-16 left-6                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘

KLAVYE KISAYOLLARI (playerOpen=true):
  Space/K → play/pause    F → fullscreen    T → theater
  I → PiP                 M → mini          A → ambient
  C → CC/subtitle         ← /J → -10sn     → /L → +10sn
  [ → hız -0.25x          ] → hız +0.25x   0-9 → seek %
  Esc → kapat

MANGA READER HEADER (FAZ-3 — 15 Haz):
  [✕]  [═══ Başlık ═══]  [↕ Webtoon / 📄 Sayfa]  [⛶ Fullscreen]
  Swipe: touchend dx>50px → prev/next (sayfa modunda)
  Klavye: F → fullscreen, ←↑ → prev, →↓ → next, Esc → kapat
  Auto-next: son sayfa (sayfa modu) → 5sn overlay → bölüm kapat
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
    content.py       → renderStats() JS hesaplama (GET /api/content)
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

### Araştırma Bulgusu (14 Haz 2026 — güncel)
- **2026 I/O güncellemesi:** Stitch artık **streaming agent** — prompt yazarken canvas gerçek zamanlı render oluyor
- Tek prompt → 5 ekrana kadar bağlantılı çıktı = **1 generation**
- Canvas'ta manuel düzeltme (AI çağırmadan) = **generation SAYMAZ**
- Edit mode + yeni prompt (büyük revizyon) = 1 daha harcar
- Generation sistemi artık aylık cap değil, gün sonu sıfırlanan **kredi bazlı**

### Bizim Planımız (8 ekran → 2 batch, 2 generation)

**BATCH 1 — Ana Akış (Standard mod) → 1 generation:**
```
1. HOME     → poster grid + filter chips + content card
2. DETAIL   → hero kapak + bilgi + sekmeler (bölüm/site/not)
3. SEARCH   → arama + 2 sekme (kütüphane/keşfet)
4. UPDATES  → güncelleme listesi
5. STATS    → özet kartlar + donut + bar chart
```

**BATCH 2 — Yardımcı Ekranlar (Experimental mod) → 1 generation:**
```
1. ADD MODAL      → bottom sheet + form + API arama
2. SETTINGS       → listeli ayarlar sayfası
3. CONFLICT MODAL → import çakışma çözümü
```

### Stitch'e Verme Stratejisi (güncel)
```
Adım 1: DESIGN.md "Stitch AI Final Prompt" bölümünü TEK SEFERDE ver
        Standard mod → 5 ekran birden üret (1 generation)

Adım 2: Çıktıyı incele
        ✅ Beğenildi → canvas'ta manuel düzelt (renk/metin/spacing) → generation SIFIR
        ❌ Büyük sorun → edit mode + üstüne kısa prompt → 1 generation daha harcar

Adım 3: BATCH 2 → ayrı session, Add Modal + Settings + Conflict Modal
        Experimental mod (daha kaliteli çıktı)

Adım 4: HTML/CSS export al → frontend/ klasörüne koy
        Post-Stitch checklist uygula (DESIGN.md'de var)
```

> FAZ-3 player + reader ekranları Stitch'e VERİLMEYECEK.
> Bunlar JS-ağır ekranlar (video kontroller, ambient glow canvas, virtual scroll) →
> Stitch çıktısı yine de sıfırdan yazılacaktı. Direkt Claude ile kodlanacak.

---

## 🔍 Stitch Çıktısı Analizi (14 Haz 2026)

### Kritik Sorunlar — Frontend Build Öncesi Çözülmeli

```
❌ 1. CDN BAĞIMLILIĞI — OFFLINE KILLER
   cdn.tailwindcss.com → Tailwind CSS CDN
   fonts.googleapis.com → Material Symbols Outlined
   → App internet olmadan TAMAMEN ölür (PWA amacına aykırı)
   → FIX: Tailwind kaldır, vanilla CSS yaz | Material Symbols → SVG ikonlar

❌ 2. 9 AYRI HTML DOSYASI — SPA DEĞİL
   Her ekran ayrı dosya → sayfa yenilenerek geçiş (app hissi yok)
   → FIX: Tek index.html, her ekran <section id="screen-X" class="screen hidden">
   → app.js showScreen('home') ile CSS toggle

❌ 3. RENK TUTARSIZLIĞI (Material token drift)
   Home bg: #0d0d1a | Add Content bg: #0e1417 (FARKLI!)
   Her ekran bağımsız generate → Material Design token değerleri kaydı
   → FIX: Tüm ekranlarda :root değişkenleri zorla, inline renk yok

❌ 4. MATERIAL DESIGN TOKEN İSİMLERİ
   surface-container-high, on-tertiary, on-surface-variant, on-primary-container...
   Tailwind config'de string, CSS variable değil
   → FIX: Tek :root { --kw-bg: #0d0d1a; --kw-card: #1a1a2e; ... } bloğu

❌ 5. JAVASCRIPT YOK
   Tüm butonlar statik HTML, click handler yok
   → FIX: app.js — navigasyon + event listener + mock data
```

### Stitch Dosya Konumları
```
C:\Kuroshin\kuroshin-downloads\stitch_kurowatch_media_tracker\
  kurowatch_home_refined\code.html       → HOME   (227KB, Tailwind inline)
  content_detail_refined\code.html       → DETAIL
  search_discover_refined\code.html      → SEARCH
  updates_refined\code.html             → UPDATES
  library_stats_refined\code.html       → STATS
  add_content_overlay\code.html          → ADD MODAL
  archive\code.html                      → ARCHIVE
  import_conflict_modal\code.html        → CONFLICT MODAL
  ⚠️ SETTINGS ekranı ayrı dosya değil — kurowatch_home_refined içinde gömülü
```

---

## 📋 Frontend Build Checklist (Backend Öncesi)

### Faz A — Birleştirme + CDN Temizliği
```
[ ] frontend/index.html oluştur
    [ ] 9 ekranı <section id="screen-*"> olarak ekle
    [ ] Tailwind CDN kaldır → vanilla CSS'e geç
    [ ] Google Fonts CDN kaldır → SVG ikonlar (local)
    [ ] Tek <style> bloğu: :root { --kw-* } değişkenleri
    [ ] Tüm renkleri #0d0d1a / #1a1a2e / #16213e / #00d4ff ile eşle
    [ ] manifest.json referansı ekle
```

### Faz B — Navigasyon + Etkileşim
```
[ ] frontend/app.js — navigasyon motoru
    [ ] showScreen(id) → active section toggle + URL hash
    [ ] Bottom nav tıklama → screen geçişi
    [ ] Back button / Android geri tuşu → popstate event
    [ ] Modal aç/kapat (Add, Conflict, Complete)
    [ ] Bottom sheet swipe-to-dismiss (touch events)
    [ ] Mock data — API olmadan ekranlar dolsun:
        5 örnek içerik (Solo Leveling / Jujutsu Kaisen / Spy×Family...)
        5 örnek güncelleme
        Stats mock sayıları
```

### Faz C — Debug Logger (KuroLog)
```
[ ] frontend/debug-logger.js
    [ ] Click interceptor: document.addEventListener('click', ..., true)
    [ ] Fetch interceptor: window.fetch = patchedFetch
    [ ] Error handler: window.onerror + unhandledrejection
    [ ] localStorage kayıt (son 100 event)
    [ ] Overlay panel:
        - ?kurodev=1 URL param veya logo triple-tap ile aç/kapat
        - Sağ alt köşe, yarı saydam, zIndex 9999
        - Son 15 event listesi (tip=renk: click=mavi, fetch=cyan, error=kırmızı, nav=mor)
        - Timestamp (saniye önce)
        - "Clear" butonu
    [ ] Button click → element.id / aria-label / textContent logla
    [ ] Fetch → URL + method + status + süre (ms) logla
    [ ] Nav → from/to screen logla
```

### Faz D — UX Eksiklikleri (Araştırma Bulguları)
```
[ ] Back button / Android back gesture
    history.pushState her screen geçişinde
    window.addEventListener('popstate') → önceki ekrana dön
    Modal açıksa → modal kapat (app'ten çıkma değil!)

[ ] Loading state — "butona bastım ama hiçbir şey olmadı" sorunu
    Her async buton: click → disabled + spinner → done → re-enable
    Skeleton loader: kart yüklenirken shimmer animasyon

[ ] Error state — backend down / network offline
    fetch fail → inline error banner (kırmızı, 4sn, dismiss)
    navigator.onLine = false → sticky "Çevrimdışı" banner

[ ] Pull-to-refresh — Updates + Home ekranı
    touchstart → touchmove → %60 aşınca → refresh trigger + spinner

[ ] Swipe-to-dismiss — Bottom sheet (Add Modal)
    touchstart Y → touchmove → 120px aşınca → kapan animasyonu

[ ] Virtual scroll — Detail > Episodes sekmesi
    1000+ bölüm DOM'a eklenmez → sadece görünür 20 satır render
    IntersectionObserver veya basit scroll handler ile

[ ] Empty state — tüm ekranlarda:
    Home: kütüphane boş → göz ikonu + "İlk içeriğini ekle"
    Updates: güncelleme yok → "Henüz güncelleme yok"
    Search: sonuç yok → "Bulunamadı"
    Archive: boş → "Arşiv boş"

[ ] Complete Modal — seri bitti:
    Son bölüm izlenince → "🎉 Tamamlandı! Puan ver:"
    Durum otomatik Tamamlandı → puan seçtir → kaydet
```

---

## 🚀 FAZ-V7 — Ultra-Precision Frontend Revizyon (23 Haz 2026 sohbet-77)

> Stitch v7 HTML'leri mevcut KuroWatch SPA'sına entegre etme. Kaynak dizin:
> `C:\Kuroshin\kuroshin-downloads\stitch_kurowatch_netflix_tasar_m_rehberi\`

### v7 Ekran Envanteri & Entegrasyon Durumu

```
┌─────────────────────────────────────────────────────────────────────┐
│ #  EKRAN                STITCH KAYNAK                  SATIR DURUM │
├─────────────────────────────────────────────────────────────────────┤
│ 1  HOME v7              kurowatch_home_solo_leveling_sim  337  [ ]  │
│ 2  SEARCH v7            kurowatch_search_filter_v7_master 383  [ ]  │
│    SEARCH Filtre Hybrid kurowatch_arama_filtreleme_v7_*   —    [ ]  │
│ 3  DETAIL v7            kurowatch_detail_solo_leveling_*  361  [ ]  │
│ 4  PLAYER v7 Gold       kurowatch_video_oynat_c_v7_gold*  250  [ ]  │
│    Player Altyazı/Ses   kurowatch_video_oynat_c_altyaz*   —    [ ]  │
│    Player Bölüm         kurowatch_video_oynat_c_b_l_m*    —    [ ]  │
│    Player Kalite        kurowatch_video_oynat_c_kalite*   —    [ ]  │
│ 5  MANGA READER v7      kurowatch_manga_okuyucu_v7_master 311  [ ]  │
│    Kuro Translate v7    kurowatch_kuro_translate_v7_master —   [ ]  │
│    Smart Clean Sim      kurowatch_kuro_translate_v7_*_sim  —   [ ]  │
│    Çeviri Ayarları      kurowatch_eviri_ayarlar_v7_*       —   [ ]  │
│ 6  UPDATES v7           kurowatch_updates_v7_master_*     315  [ ]  │
│ 7  DOWNLOADS v7         kurowatch_downloads_v7_master_*   386  [ ]  │
│ 8  STATS v7             kurowatch_stats_v7_master         438  [ ]  │
│ 9  SETTINGS v7          kurowatch_settings_v7_final_*     583  [ ]  │
└─────────────────────────────────────────────────────────────────────┘
```

### v7 API Şemaları (kurowatch_teknik_api_spesifikasyonu_coder_ready.md)

```
HOME:    GET /api/home/hero + /api/home/sections + /api/user/continue-watching
DETAIL:  GET /api/series/:id/metadata + /episodes + /characters
PLAYER:  GET /api/v7/player/init/:episode_id (stream+markers+assets)
         POST /api/v7/player/sync (heartbeat 30sn)
         POST /api/v7/analytics/event (skip_intro vb.)
READER:  GET /api/v7/reader/chapter/:id
         POST /api/v7/translate/vision (OCR + overlay)
         POST /api/v7/reader/sync (last_page heartbeat)
SETTINGS: PATCH /api/user/settings
          POST /api/proxy/validate-key (AniList/MAL/IGDB/DeepL)
DL/UPD:  POST /api/download/queue + GET /api/user/notifications
```

### v7 Design Tokens (tüm ekranlarda zorunlu)

```css
/* v7 renk anayasası — inline renk YASAK */
--v7-bg:        #0d0d1a    /* sayfa zemini */
--v7-surface:   #0e1417    /* kart/panel zemini */
--v7-card:      #1a1a2e    /* içerik kartı */
--v7-raised:    #16213e    /* modal/overlay */
--v7-input:     #1c1d37    /* form input */
--v7-cyan:      #00d4ff    /* Electric Cyan — primary */
--v7-cyan-dim:  rgba(0,212,255,0.1)   /* cyan bg */
--v7-cyan-brd:  rgba(0,212,255,0.3)   /* cyan border */
--v7-text:      #e1e0ff    /* birincil metin */
--v7-muted:     #9090b0    /* ikincil metin */
--v7-border:    rgba(255,255,255,0.05)/* çizgiler */

/* v7 animasyon kuralı */
transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); /* spring */
active:scale-[0.95]   /* her tıklanabilir element */
hover:scale-[1.02]    /* kart hover */
hover:scale-[1.18]    /* büyük kart hover */

/* v7 spacing kuralı — 4'ün katları */
gap: 8px | 12px | 16px | 24px | 32px | 48px  ONLY
```

### v7 Kritik Sorunlar (Stitch çıktılarından bilinenlr)

```
❌ CDN BAĞIMLILIĞI — Her HTML'de tailwindcss.com + fonts.googleapis.com CDN
   FIX: tailwindcss.exe ile local build → tailwind.css?v=7
   FIX: Google Fonts → local font veya system font stack

❌ AYRI HTML DOSYALARI — SPA değil, her biri bağımsız
   FIX: index.html içinde <section id="screen-*"> olarak entegre et

❌ RENK DRIFT — Her ekran bağımsız generate → token kayması
   FIX: :root v7 token sistemi, inline renk SIFIRLA

❌ JS YOK — Tüm butonlar statik
   FIX: app.js event handler'lar + v7 logic

❌ MATERIAL TOKEN İSİMLERİ — surface-container-high vb. Tailwind'e özgü string
   FIX: --v7-* CSS değişkenleri ile replace
```

### v7 Entegrasyon Adımları (sıralı)

```
1. FAZ-V7-0: CSS Token kur + tailwind local build       [ ]
2. FAZ-V7-1: HOME ekranı replace                        [ ]
3. FAZ-V7-2: SEARCH + filtre paneli                     [ ]
4. FAZ-V7-3: DETAIL + karakter galerisi                 [ ]
5. FAZ-V7-4: VIDEO PLAYER + 3 overlay                  [ ]
6. FAZ-V7-5: MANGA READER + Kuro Translate              [ ]
7. FAZ-V7-6: UPDATES v7                                 [ ]
8. FAZ-V7-7: DOWNLOADS v7                               [ ]
9. FAZ-V7-8: STATS v7                                   [ ]
10. FAZ-V7-9: SETTINGS v7 + API key form'ları           [ ]
11. FAZ-V7-10: app.js tüm event wiring                  [ ]
12. FAZ-V7-11: Iron Inquisitor kalite testi             [ ]
```

---

## ✅ Özellik Tamamlanma Durumu

> Son güncelleme: 23 Haz 2026 (sohbet-77)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-1 (MVP) — TRACKER ✅ TAMAMLANDI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FRONTEND:
[x] HOME — poster grid + filter chips (tip/durum/genre)
[x] HOME — content card (kapak, badge, glow, progress bar)
[x] HOME — boş durum
[x] SEARCH — kütüphanem sekmesi (q= filtre)
[x] SEARCH — keşfet sekmesi (AniList/IGDB + genre chip)
[x] DETAIL — hero kapak + bilgi paneli
[x] DETAIL — ★ interaktif yıldız puan (PATCH my_score)
[x] DETAIL — progress bar + "Sonraki Bölüm" butonu
[x] DETAIL — cover_url → bg-image + initials fallback (sohbet-39)
[x] DETAIL — ✏️ Edit Modal → başlık/tip/durum/puan/not düzenle + sil (sohbet-39)
[x] DETAIL — "8.5 / 10" sayısal puan gösterimi (sohbet-39)
[x] DETAIL — bölümler sekmesi (URL varsa İndir butonu)
[x] DETAIL — siteler sekmesi
[x] DETAIL — notlar + spoiler toggle
[x] UPDATES — liste + "Şimdi Kontrol Et"
[x] STATS — özet kartlar + donut + bar chart (CSS/SVG)
[x] SETTINGS — export/import + arşiv
[x] SETTINGS — Web Push bildirim toggle + Test butonu
[x] SETTINGS — varsayılan süreler + kalite + auto-delete
[x] ADD MODAL — AniList arama + form + site satırları
[x] CONFLICT MODAL — çakışma çözümü
[x] NAV — mobil alt bar + PC sol sidebar
[x] i18n — i18n.js + locales/tr.json + locales/en.json
[x] PWA — manifest.json + sw.js + icon-192/512 + push

BACKEND:
[x] database.py — SQLite async engine (aiosqlite)
[x] models.py — Content, Site, Episode, Update, Tag, ContentTag
[x] routers/content.py — /api/content CRUD + /api/discover
[x] routers/episodes.py — /api/episodes + /api/check-updates + /api/updates
[x] routers/sites.py, tags.py, sync.py, settings.py
[x] scraper/anilist.py — GraphQL (anime/manga/manhwa)
[x] scraper/mal.py, igdb.py, mangadex.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-2 — PLATFORM GENİŞLEME ✅ TAMAMLANDI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] scraper/mal.py — MAL OAuth2 PKCE
[x] scraper/igdb.py — IGDB Twitch auth
[x] scraper/mangadex.py — MangaDex API
[x] Content external_id PATCH (AniList ID atama)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-3 — PLAYER / DOWNLOADER ✅ TAMAMLANDI (15 Haz)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANİME İNDİRİCİ:
[x] downloader/anime.py — yt-dlp async subprocess, ilerleme % parse
[x] downloader/manga.py — MangaDex API + gallery-dl (Madara)
[x] downloader/manager.py — kuyruk max 2 eşzamanlı, WS push, daisy-chain
[x] routers/download.py — /start /queue /storage /serve /pages /page + WS
[x] İndirmeler ekranı — nav badge, job kartları, ilerleme çubuğu
[x] Daisy-chain — %50'de N+1 bölüm otomatik kuyruğa alınır
[x] İzle-sil — DELETE /api/download/{id} (dosya siler)
[x] Canlı test: YouTube 465KB 8sn PASS ✅

VIDEO PLAYER:
[x] HTML5 <video> + modal overlay
[x] Skip Intro butonu (#skip-intro-btn, FAZ-4 ile entegre)
[x] Ambient Mode — canvas blur arkaplana video yansıtır (A tuşu)
[x] Theater Mode — header auto-hide, immersive izleme (T tuşu)
[x] Picture-in-Picture (I tuşu, requestPictureInPicture)
[x] Mini Player — sağ alt köşe 320×200 (M tuşu)
[x] Klavye seti: Space/K (pause) / F (fullscreen) / T (theater) / I (PiP) / M (mini) / A (ambient) / C (CC) / ←→/J/L (±10sn) / [/] (hız) / 0-9 (seek %)
[x] Auto-next episode (30sn kala overlay + 10sn geri sayım)
[x] Altyazı: VTT subtitle track (yt-dlp --write-sub tr/en)
[x] Backend: GET /api/download/subtitles/{job_id}

MANGA READER:
[x] Webtoon modu (dikey scroll)
[x] Sayfa modu (tek sayfa, ←→ nav)
[x] Klavye: Esc/ArrowLeft/ArrowRight/F
[x] Swipe (mobil touch events — sayfa modunda)
[x] Auto-next chapter (son sayfa → 5sn → sonraki)
[x] Tam ekran toggle (F tuşu / reader-fullscreen-btn)

FAZ-C — PWA PUSH ✅ TAMAMLANDI:
[x] backend/push_manager.py — VAPID key + abonelik + push gönderimi
[x] backend/routers/push.py — /vapid-public-key /subscribe /test
[x] episodes.py — yeni bölüm → push otomatik
[x] frontend/pwa.js — SW + subscribe/unsubscribe
[x] frontend/sw.js — push event + notificationclick + cache v2
[x] Settings: Push toggle + Test butonu

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-4 — OTOMATİK ALGI (15 Haz sohbet-19)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] backend/analyzer/chromaprint.py — fpcalc wrapper + .fp.json cache
[x] backend/analyzer/intro_detector.py — sliding window hamming, consensus
[x] backend/models.py — IntroTimestamp ORM
[x] backend/routers/analyze.py — POST/GET/DELETE /api/analyze/intro/{id}[/{ep}]
[x] frontend/player.js — _intro.load/tick/skip + Skip Intro butonu
[x] Canlı test: confidence:1.0 PASS ✅
[x] FFmpeg black frame detect — outro sınır tespiti (sohbet-21)
[ ] Öneri algoritması — genre/tag bazlı (araştırma askıda)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-5 — MANGA ÇEVİRİSİ (sadece PC + GPU) ✅ TAMAMLANDI (15 Haz sohbet-21)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Araç: zyddnys/manga-image-translator
Pipeline: YOLOv8 balon → manga-ocr/PaddleOCR → m2m100/DeepL → LaMa inpaint → render
Kısıt: NVIDIA GPU + CUDA zorunlu (nvidia-smi ile tespit)

BACKEND:
[x] translator/engine.py — subprocess wrapper (--lang TRK, --translator m2m100)
[x] translator/detect_gpu.py — nvidia-smi GPU tespiti + translator kurulum kontrolü
[x] routers/translate.py — POST/GET/DELETE /api/translate/{id}/{ep}
[x] routers/translate.py — GET /api/translate/pages/{id}/{ep} + WS /api/translate/ws
[x] routers/translate.py — GET /api/system/gpu

FRONTEND:
[x] GPU tespiti → _translate.checkGpu() + localStorage-benzeri _gpu cache
[x] "🌐 Çevir" butonu — sadece GPU varsa reader header'da görünür
[x] Çeviri progress WS (sayfa sayfa %) — reader-translate-label güncellenir
[x] Dil toggle: [JP] [TR] — _translate.showOriginal() / showTranslated()
[ ] "✏️ Düzelt" butonu (DB'ye kaydedilir) — gelecek sprint

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-6 — BROWSER EXTENSION ✅ TAMAMLANDI (sohbet-37/38)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] extension/manifest.json (Chrome Manifest V3)
[x] extension/content/tranimaci.js — URL parse + ilerleme push
[x] extension/content/tranimeizle.js — 3 katmanlı parse + domain fix
[x] extension/content/diziwatch.js — URL parse
[x] extension/background.js — service worker, CAPTURE mesajı
[x] backend/routers/extension.py — POST /api/extension/capture (AniList fuzzy match)
    - cover_url + genres AniList'ten otomatik
    - _ensure_site() + _ensure_episode() → indirme butonu çıkıyor
    - 4 katmanlı fuzzy: tam → kısalt → ilk kelime → trailing-s kırp
    Canlı kanıt: Bölüm 12 → "Baki" AniList match ✅ (commit a9fbd24)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MOBİL ADB (Kuroshin.bat, 15 Haz sohbet-19)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] Kuroshin.bat KUROWATCH [3] — adb reverse tcp:8099 + PWA talimatları

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FAZ-7 — VERİ & EPISODE SİSTEMİ (Haz 2026, sohbet-57~74)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SEZON SİSTEMİ (sohbet-71/72):
[x] content tablosuna season_number + parent_id kolonları eklendi
[x] API: GET /api/content?parent_id=X (sezon zinciri)
[x] scripts/season_linker.py — AniList sezon zinciri builder
[x] UI: 35 yeni kart eklendi, sezon zinciri UI gösterimi
[x] Duplikat temizleme: Shangri-La S2 ID=685 silindi, zincir 104→109

URL SAĞLIK SİSTEMİ (sohbet-71):
[x] scripts/ping_all_content.py — 660/660 %100 OK ping testi
[x] URL fix: Nano Machine → ragnarscans.com (178 ep)
[x] URL fix: Büyü İmparatoru → ragnarscans.com (465 ep)
[x] URL fix: A Returner's Magic → manhwahentai.me (268 ep)
[x] manga.py: manhwahentai.me Madara domain desteği eklendi
[x] scripts/ping_results.json — ping sonuçları (660 içerik)

TOPLU EPİSODE SYNC (sohbet-73):
[x] scripts/bulk_episode_sync.py — ping_results.json + listing URL slug
[x] 8658 episode eklendi (509 anime)
[x] 253 anime → turkanime.tv URL | 256 anime → tranimaci.com URL

TURKANIME.TV MODAL FİX (sohbet-73, commit cda45e2):
[x] Sorun: Bootstrap modal backdrop tıklamayı engelliyordu
[x] Çözüm: JS force-remove + click(force=True) + stealth context
[x] Test: FMA / Elfen Lied / Peter Grill — 3/3 stream URL ✅

TRANİMACİ → TURKANİME.TV MİGRATİON (sohbet-74, commit e0d65d6):
[x] scripts/fetch_turkanime_list.py — sitemap.xml.gz ile 6613 slug çekildi
[x] scripts/find_anime_slugs.py — slug eşleştirme (sitemap + HTTP test)
[x] scripts/apply_turkanime_migration.py — DB güncelleme scripti
[x] 22 anime turkanime.tv'ye geçirildi:
    Bleach TYBW, Code Geass R2, Hell's Paradise S2, KONOSUBA S3,
    SPY×FAMILY, Shield Hero, High School DxD NEW, ISHURA S2,
    Blood Blockade & Beyond, Kaguya-sama, Danmachi II,
    Isekai Cheat Magician, By the Grace of Gods 2, Chunibyo S2,
    Another, Miyazaki filmleri (Totoro/Spirited Away/Howl's), Immortal King
[x] 194 tranimaci ep silindi, 194 turkanime.tv ep eklendi
[x] 16/16 URL doğrulama 200 OK ✅
[ ] Kalan 234 tranimaci anime (Türk dizi/film/Western) — kaynak yok
```
