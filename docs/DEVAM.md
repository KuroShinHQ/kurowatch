# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 24 Haziran 2026 (sohbet-92) · **Aktif sürüm:** v1.3.6 → Jobs persist + Progress fix + OYNAT fix · **Son commit:** `66f2c61`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## 🔥 AKTİF GÖREV — FAZ-V7 Frontend Revizyon (sohbet-77 itibarıyla)

### Stitch v7 Dosya Envanteri
```
C:\Kuroshin\kuroshin-downloads\stitch_kurowatch_netflix_tasar_m_rehberi\
  kurowatch_home_solo_leveling_sim\code.html         337 satır — HOME v7
  kurowatch_detail_solo_leveling_sim\code.html       361 satır — DETAIL v7
  kurowatch_search_filter_v7_master\code.html        383 satır — SEARCH v7
  kurowatch_video_oynat_c_v7_gold_master_hybrid\code.html  250 satır — PLAYER v7
  kurowatch_manga_okuyucu_v7_master\code.html        311 satır — READER v7
  kurowatch_updates_v7_master_rafine\code.html       315 satır — UPDATES v7
  kurowatch_downloads_v7_master_rafine\code.html     386 satır — DOWNLOADS v7
  kurowatch_stats_v7_master\code.html                438 satır — STATS v7
  kurowatch_settings_v7_final_master\code.html       583 satır — SETTINGS v7
  kurowatch_video_oynat_c_altyaz_ve_ses_se_imi_v7\  — Player altyazı/ses overlay
  kurowatch_video_oynat_c_b_l_m_se_imi_v7\          — Player bölüm seçimi overlay
  kurowatch_video_oynat_c_kalite_se_imi_v7\          — Player kalite seçimi overlay
  kurowatch_kuro_translate_v7_master\                — Kuro Translate v7
  kurowatch_kuro_translate_v7_master_smart_clean_sim\ — Smart Clean sim
  kurowatch_eviri_ayarlar_v7_final_simulation\       — Çeviri ayarları
  kurowatch_arama_filtreleme_v7_master_hybrid\       — Search filtre hybrid
  kurowatch_teknik_api_spesifikasyonu_coder_ready.md — Tüm API şemaları
  kurowatch_backend_entegrasyon_rehberi_v7.md        — Backend entegrasyon
  kurowatch_video_player_teknik_logic_spesifikasyonu_v7_master.md
  kurowatch_manga_reader_teknik_api_logic_spesifikasyonu_v7_master_pro.md
```

### FAZ-V7 TODO Listesi

### ⚠️ KRİTİK BULGU (plan revizyonu)
```
Stitch HTML'lerdeki data-api-endpoint attribute'ları sadece tasarım notu —
otomatik API çağrısı yapmıyor. Tüm data binding app.js'te yapılıyor.
Yeni backend route SADECE 1 TANE gerekiyor (validate-key).
Geri kalan TÜMÜ mevcut /api/ endpoint'lerine map ediyor.
```

### Backend → Frontend Gerçek Eşleşmesi
```
HOME Hero          → GET /api/content → top-score item        (app.js filter)
HOME Devam Et      → GET /api/content → progress 1–99%        (app.js filter)
HOME Anime Row     → GET /api/content?type=anime              ✅ mevcut
HOME Manga Row     → GET /api/content?type=manga              ✅ mevcut
SEARCH             → GET /api/content?type=X&q=Y              ✅ mevcut
DETAIL Bölüm       → GET /api/content/:id/episodes            ✅ mevcut
DETAIL Karakter    → GET /api/content/:id/anilist → characters ✅ mevcut
PLAYER kontroller  → player.js local state (HTTP yok)         ✅ HTML replace yeter
PLAYER Intro skip  → GET /api/analyze/intro/:id               ✅ mevcut
READER Sayfalar    → GET /api/download/pages/:id              ✅ mevcut
READER Translate   → POST /api/translate/:id/:ep              ✅ mevcut
UPDATES            → GET /api/updates                         ✅ mevcut
DOWNLOADS          → GET /api/download/queue + /storage       ✅ mevcut
STATS              → GET /api/content → JS hesaplama          ✅ mevcut
SETTINGS kaydet    → POST /api/settings                       ✅ mevcut
SETTINGS key test  → POST /api/proxy/validate-key             ❌ YENİ (1 endpoint)
```

---

**FAZ-V7-0: CSS Token Temeli** ✅ TAMAMLANDI (commit 584869d)
```
[x] tailwind.config.js → v7 token sistemi merge et
    (bg-primary:#0d0d1a, bg-card:#1a1a2e, primary-container:#00d4ff)
    Stitch'in Material token adlarını --v7-* CSS değişkenlerine map et
[x] style.css :root → v7 CSS değişkenlerini unify et
[x] tailwindcss.exe ile local build → tailwind.css?v=31 üret (CDN yok)
[x] Stitch HTML'lerdeki CDN scriptleri remove listesi çıkar
```

**FAZ-V7-1: Home v7** ✅ TAMAMLANDI (commit 584869d)
```
[x] index.html #screen-home → v7 Hybrid layout (Hero + satırlar + kütüphane grid)
    IDs: home-hero-bg/title/meta/synopsis/status-badge/continue-btn/detail-btn
         home-continue-row / home-anime-row / home-manga-row / home-games-row
         home-library-grid (KORUNDU — mevcut app.js kırılmaz)
[x] app.js renderHomeV7() ekle:
    → GET /api/content → hero (top my_score), devam-et (pct 1-99%), tip satırları
    → renderHome() içinden paralel çağrılıyor (bağımsız)
[x] style.css: glass-btn / spring-bounce / animate-pulse-cyan / shimmer-bar
```

**FAZ-V7-2: Search v7** ✅ TAMAMLANDI (commit 10c7979)
```
[x] index.html #screen-search → v7 Hybrid layout
    - Sekme (Kütüphanem/Keşfet) + FİLTRELE toggle butonu
    - Filtre paneli: Tip (anime/manga/manhwa/game) + Tür chip + Sıralama
    - Kütüphanem: #library-search-results grid cols-3
    - Keşfet: #search-results grid cols-3
[x] renderLibrarySearch(): v7 aspect-[2/3] cover kartlar (stripe+badge+başlık+skor)
[x] renderSearch(): v7 grid kartlar + alt Ekle butonu
[x] _buildDiscoverGenreChips(): v7 chip stili
[x] _initSearchTabs(): v7 tab class + filtre toggle mantığı
[x] tailwind.css v32 rebuild
```

**FAZ-V7-3: Detail v7** ✅ TAMAMLANDI (commit cb5b13a)
```
[x] #screen-detail hero: 480px yükseklik, cinema gradient, floating header
    badges + title (uppercase 26px) + DEVAM ET CTA + 3 secondary action
[x] detail-continue-btn: progress 1-99%'de görünür, "DEVAM ET — Bölüm N" etiketi
[x] detailSwitchTab: 'characters' tab eklendi (matchMap ile eşleşme)
[x] detail-tab-characters: yatay scroll karakter galerisi (avatar, isim, rol, VA)
[x] anilist.py: characters(sort:ROLE, perPage:20) query + _format() entegrasyonu
[x] tailwind.css v33 rebuild
```

**FAZ-V7-4: Video Player v7 Cinema Master** ✅ TAMAMLANDI (commit 78f1115)
```
[x] index.html #modal-player → Stitch Gold Master HTML ile replace et
    - video-master + controls-overlay (auto-hide 3.5sn, opacity transition)
    - Orta: play/pause (büyük cyan) + rewind/forward 10s
    - Üst: geri, başlık, bölüm etiketi, CC/hız/kalite/bölüm/kilit/capture butonları
    - Alt: skip-intro (pulse-cyan), timeline (progress+buffer+knob), zaman, next-ep, fullscreen
[x] 3 gömülü panel:
    - panel-episodes: sağ drawer (85%/400px) — bölüm listesi + download_done badge
    - panel-quality: alt bottom sheet — mevcut kalite gösterimi (1080p/720p/480p/360p)
    - panel-subtitle: alt bottom sheet — CC toggle + oynatma hızı seçici (0.5x–2x)
[x] player.js v7 güncellemeleri:
    - _controls: show/resetTimer/setPlaying/updateTime (timeline + zaman display)
    - _lock: toggle → controls-overlay gizle + kilit overlay göster
    - _captureFrame: canvas.drawImage(video) → PNG indir
    - _panelEpisodes: /api/content/:id/episodes fetch + render + tıkla geç
    - _panelQuality / _panelSubtitle: open/render/close
    - video play/pause/ended → _controls.setPlaying() (event listeners)
    - timeline seek: mousedown+mousemove+touchstart → video.currentTime
    - timeupdate → _controls.updateTime() (progress bar + zaman göstergesi)
    - buffer progress → timeline-buffer dolumu
[x] style.css: player-theater/mini kuralları → v7 ID'leri (controls-overlay, video-master)
[x] tailwind.css v34 rebuild
```

**FAZ-V7-5: Manga Reader v7 Hybrid** ✅ TAMAMLANDI (commit d5e8f02)
```
[x] index.html #modal-reader → Stitch v7 ile replace (commit c193dab)
    - reader-header: glass sticky, WEB/SAYFA toggle, JP/TR, fullscreen, kuro-translate-btn
    - reader-pages: padding-top:64px, padding-bottom:128px
    - reader-nav: ALWAYS visible (v7), progress bar + cur/total + prev/next chapter + ±page
    - reader-ui-toggle: FAB orta-alt (visibility toggle)
    - panel-translate: Kuro Translate bottom sheet — Smart Clean toggle, font/opacity slider
[x] player.js _readerUI + _panelTranslate nesneleri (sohbet-78c)
[x] player.js tüm wiring tamamlandı (sohbet-79):
    - _render(): data-page-idx eklendi, nav hide kaldırıldı, _updateProgress çağrısı
    - _updateProgress(): progress bar + page-num + pct-label + cur-page + of-pages
    - _initScrollObserver(): IntersectionObserver webtoon scroll progress takibi
    - open(): reader-chapter-label + _readerUI.reset()
    - close(): _panelTranslate.close() + observer.disconnect()
    - toggleMode(forceWebtoon): webtoon-btn/page-btn stil senkronizasyonu
    - DOMContentLoaded: tüm yeni butonlar + sliders + merkez-tap + scroll auto-hide
    - tailwind.css v35 rebuild
```

**FAZ-V7-6: Updates v7** ✅ TAMAMLANDI (commit 8a0a41e)
```
[x] index.html #screen-updates → v7 replace (zaman gruplu: Bugün/Dün/Bu Hafta/Daha Önce)
[x] app.js renderUpdates(): kart v7 (56×80 cover + badge + action/read btn)
    GÖRDÜM → PATCH /api/updates/:id/read, DETAYLAR → renderDetail
    tailwind.css v36 rebuild
```

**FAZ-V7-7: Downloads v7** ✅ TAMAMLANDI (commit 7c0d971)
```
[x] index.html #screen-downloads → v7 replace (gruplama: İndiriliyor/Tamamlandı/Hata)
[x] player.js _jobCard(): 56×80 cover box + progress HTML + v7 action butonlar
[x] player.js _renderDownloadScreen(): _section() ile grup başlıkları
[x] app.js showScreen(): screen-downloads → window.kuroDownload.render()
    tailwind.css v37 rebuild
```

**FAZ-V7-8: Stats v7** ✅ TAMAMLANDI (commit a814825)
```
[x] index.html #screen-stats → bento 2×2 + donut SVG + CSS bars + genre chips
[x] app.js renderStats(): stats-completed + CSS bar tip dağılımı + genre chip v7 stil
    TYPE_LABELS map, donut dashoffset düzeltme
    tailwind.css v38 rebuild
```

**FAZ-V7-9: Settings v7 Master** ✅ TAMAMLANDI (commit e60dfbe)
```
[x] index.html #screen-settings → v7 glass section layout, tüm ID korundu
    Hızlı Gezinti / API & Bağlantılar / Veri Yönetimi / Etiketler
    İndirme Ayarları / Site Cookies / Bildirimler / Hakkında
[x] backend/routers/settings.py: POST /api/proxy/validate-key
    anilist/mal/igdb/deepl için httpx async doğrulama
    {valid: bool, message: str}
[x] app.js showScreen() duplicate satır kaldırıldı
    tailwind.css v39 rebuild
```

**FAZ-V7-10: app.js Wiring** ✅ TAMAMLANDI (commit 2f822b6)
```
[x] showScreen() → spring geçiş cubic-bezier(0.34,1.56,0.64,1), translateX 24px / translateY 18px
[x] Pull-to-refresh: screen-home + screen-updates, touchstart/move/end, 72px eşik, ptr-indicator FAB
[x] renderSettings(): _validateKey() helper + settings-igdb-test buton wiring
[x] settings HTML: settings-igdb-test butonu + settings-validate-result div eklendi
    tailwind.css v40 rebuild
```

**FAZ-V7-11: Iron Inquisitor Kalite Testi** ✅ TAMAMLANDI (commit 8073473)
```
[x] CDN bağımlılığı → SIFIR ✅
[x] Renk drift → #1a1b2e → #1a1a2e düzeltildi (2 yer)
[x] glass-card tanımı doğrulandı (index.html style tag, 16 kullanım)
[x] v7 ekranlar layout tutarlı (pt-20/pb-6/px-4 pattern)
[x] @keyframes spin → style.css'e eklendi (PTR indicator + animate-spin class)
[x] 4px grid: legacy popup'lar (progress-quick-edit, download-float) kabul edilebilir
[x] Son kalite geçişi + commit ✅
```

### 🎉 FAZ-V7 TAMAMEN TAMAMLANDI (V7-0..11 = 12/12)

**FAZ-V7 Bug Fix** ✅ TAMAMLANDI (commit 112ed4d)
```
Kapsamlı 30-hata analizi → 15 kritik/yüksek/orta bug fix:

RUNTIME CRASH FIX (app.js):
[x] openReadOverlay/closeReadOverlay IIFE scope'a taşındı
    (DOMContentLoaded closure'ındaydı → bölüm linkine tıklanınca ReferenceError)
[x] window.openDetail exposed (hero DEVAM ET / DETAYLAR CTA → tanımsız fonksiyondu)

NAV FIX (app.js):
[x] _NAV_ORDER bottom-nav sırasıyla hizalandı: home→search→updates→downloads→settings→stats→archive
    (eskisi: stats settings'in önündeydi, downloads en sonda — animasyon yönü yanlıştı)
[x] valid[] array'e screen-downloads eklendi (#screen-downloads hash açılmıyordu)

LISTENER FIX (app.js):
[x] _initSearchTabs: discover-type-btn + filterBtn birikmeli addEventListener önlendi
    (her search ekranına geçişte listener birikiyordu)
[x] _addActiveType değişkeni: submitAddContent CSS class escape query kaldırıldı

UX FIX (app.js):
[x] renderDetail başında progress-quick-edit paneli sıfırlanıyor

PLAYER FIX (player.js):
[x] player-volume-btn mute toggle listener eklendi (tamamen bağlantısızdı)
[x] panel-quality: list item tıklanabilir buton oldu, _selected state takibi,
    apply butonu video.dataset.quality'i gerçekten güncelliyor
[x] Reader: nextChapter() + prevChapter() metotları eklendi
    - reader-prev/reader-next artık BÖLÜM geçişi (eskiden sayfa geçişiydi)
    - reader-prev-page/reader-next-page sayfa geçişi olarak kaldı
    - webtoon modunda prev/next otomatik chapter geçişi yapıyor
    - _triggerAutoNextChapter() jobs listesinden sonraki bölümü buluyor ve açıyor

KALAN (bilerek bırakıldı):
- HATA-25: active+hidden class — CSS specificity incelendi, gerçek bug değil
- HATA-29: settings version hardcoded — backend'den çekilmiyor
```

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (24 Haz sohbet-86):
  - Backend ⚠️ KAPALI (bat→10→1 ile başlat)
  - Son commit: 3e7af9e (HOME spacing + SEARCH filtre port)

✅ SOHBET-86 TAMAMLANDI — SEARCH FİLTRELE + HOME spacing:
  commit 0cfbad1 (SEARCH) + 3e7af9e (HOME):

  SEARCH FİLTRELE (Stitch birebir port):
  [x] Buton: icon 18px, gap-2, px-4, hover:brightness, "FİLTRELE" büyük harf
  [x] Filtre paneli tam Stitch layout: Tür → Tip → Yıl+Puan → Durum → Sıralama
  [x] Yıl butonları (Hepsi/2025/2024/2023) → _filterYear state
  [x] Puan range slider (0-10) → _filterScore state, "Hepsi/X.X+" label
  [x] Durum grid 4 buton (İzliyorum/Bitti/Planlı/Hepsi) → _filterStatus state
  [x] renderLibrarySearch: yıl+puan+durum JS filter + sıralama uygulama
  [x] tailwind v46 + SW cache v8

  HOME spacing (Stitch'e yaklaştırma):
  [x] Devam Et section: mb-8 mt-4 → mb-12, text-18px → text-20px tracking-tight
  [x] Row divler: px-4 → pl-4 pr-4 (sol-açık Netflix efektine hazır)
  [x] Devam Et row: pb-3 → pb-4

  NOT YAPILMAYANLAR (sohbet-87'ye):
  ❌ DETAIL revizyon (Lord Stitch AI prompt gerekiyor)
  ❌ Downloads Video Oynat / Manga Oku buton testi (backend kapalıydı)
  ❌ HOME daha derin revizyon (Lord görüp karar verecek)

SOHBET-87 TAMAMLANDI — URL Sağlık Taraması + Toplu Fix:
  [x] 513 içerik otomatik test → 509 OK / 4 FAIL
  [x] Murim Login 171 ep → manhwahentai.me ✅
  [x] Gintama → gintama-2015 slug ✅
  [x] Howl duplikat silindi
  [x] manga.py OFFLINE listesi (majorscans vb.) — commit 3544b16
  KALAN: 3 Ghibli (URL yok), AoT 500 (geçici)
  Settings Cinema → tema seçilince değişmiyor ❓

SOHBET-88 TAMAMLANDI — DETAIL Stitch port + Tema fix (commit ebb73d3):
  [x] Settings Cinema/Kawaii/Kuro tema → CSS değişkenler gerçekten uygulanıyor
  [x] DETAIL hero 530px, KUROWATCH header ortada
  [x] Episode thumbnail 128×72px + aktif/tamamlanan stiller
  SW cache v11

SOHBET-89 TAMAMLANDI — Download fix + HOME kütüphane kaldır + turkanime.tv migration:
  [x] DB migration: 4942 episode turkanime.tv → tranimaci.com (tam olarak yapılmamıştı!)
  [x] 717 site URL turkanime.tv/tranimeizle → tranimaci.com
  [x] manga.py: protocol-relative URL fix (//cdn.manhwahentai.me → https://...)
  [x] anime.py: [generic] hata mesajı düzeltildi (actual_url==url koşulu kaldırıldı)
  [x] stream_finder.py: Playwright context'e cookies.txt yükle (force_playwright siteleri için)
  [x] HOME: "Tüm Kütüphane" grid gizlendi (Stitch AI'da yok, karmaşıklık yaratıyordu)
  [x] SW v12, app.js v34 (cache bust)
  Commit: ec3ac33 (download), ceeebdb (HOME fix)

SOHBET-90 TAMAMLANDI — HOME scroll + tema + notlar:
  [x] Manga indirme: manhwahentai.me Bölüm 1 → 9.3 MB ✅ ÇALIŞIYOR
  [x] HOME: "Tüm Kütüphane" grid kaldırıldı (ceeebdb)
  [x] HOME yatay scroll: overflow-x-hidden kaldırıldı, touch-action + -webkit-overflow-scrolling:touch eklendi (51d24cd)
  [x] Tema: CSS var(--kw-*) override sistemi (SW v13, app.js v35)
  ❌ ANİME İNDİRME: tranimaci.com "video embed bulunamadı" hatası — stream_finder.py tranimaci.com için embed çıkaramıyor
     → tranimaci.com Playwright veya direkt yt-dlp test gerekiyor
     → Sorun: tranimaci.com için Playwright'ta hangi selector'ların çalıştığı bilinmiyor
  ❌ HOME yatay scroll: Hâlâ bozuk — overflow-x-hidden kaldırmak yetmedi
     → iOS -webkit-overflow-scrolling:touch eklendi, yetmezse Playwright gerekebilir

SOHBET-91 TAMAMLANDI — HOME scroll + tranimaci.com ANİME İNDİRME FİX (cdd28a4 + DB migration):
  [x] HOME scroll: touch-action:pan-x + _addDragScroll() (mouse drag) — SW v14, app.js v36
  [x] tranimaci.com: _FORCE_PLAYWRIGHT eklendi, networkidle 25sn, wait_secs 30sn (cdd28a4)
  [x] DB migration: 8654 ep URL'si www.tranimaci.com → tranimaci.com (www. redirect sorunuydu!)
  [x] KANIT: stream_finder KONOSUBA Ep1 → cdn10.videostraeam10.can.re/...1080p.mp4?token=... ✅
  ⚠️ Token süresi: CDN token dinamik (yt-dlp hemen başlarsa sorun yok)
  ⚠️ HOME scroll: Backend açık olduğunda test edilmeli — touch-action fix teorik

SOHBET-91b EK BULGULAR (gerçek test):
  HOME scroll: çalışıyor AMA snap-x mandatory sert → snap-proximity yapılacak
  Tema: ✅
  ANİME sorunlar:
    ❌ OYNAT → player AÇILMIYOR (donuyor) — openVideo(_jobs[jobId]) null (WS gelmeden önce)
    ❌ bat restart → TÜM JOBS SİLİNİYOR — manager.py in-memory storage
    ❌ %0→%100 atlama → WS progress anlık render etmiyor
    ❌ Diğer sayfalarda float indicator çalışmıyor
    ✅ İndirme tamamlandı (503.4 MB, dosya diskte var)

SOHBET-92 TAMAMLANDI — Jobs persist + Progress await fix + OYNAT fix (commit 66f2c61):
  [x] manager.py: JSON persist (downloads/jobs.json) — restart'ta jobs korunuyor
  [x] main.py: lifespan'de load_jobs() çağrılıyor
  [x] anime.py + manga.py: on_progress() → await on_progress() — progress artık anlık
  [x] player.js: openVideo API fallback — _jobs null ise /api/download/queue fetch
  [x] index.html: snap-x snap-proximity — scroll sertliği azaldı, SW v15, player.js v6

SOHBET-93 ODAĞI (backend restart + cihazda test):
  1. bat→5→1 (backend restart — manager.py değişti)
  2. Anime indir → progress bar'ın %0→%100 atlamadığını doğrula
  3. bat restart → OYNAT butonunun görüldüğünü doğrula (jobs.json persist)
  4. HOME scroll proximity → sertlik azaldı mı test et
  5. Float indicator diğer sayfada görünüyor mu?
```
  MANGA/MANHWA URL FIX:
    - Nano Machine (178 ep): ragnarscans.com/manga/nano-makine/bolum-N/
    - Büyü İmparatoru (465 ep): ragnarscans.com/manga/buyu-imparatoru/bolum-N/
    - A Returner's Magic (268 ep): manhwahentai.me/manhwa/.../chapter-N/ (29e205c)
    - The Hunter (109 ep): mangawow.com — değişmedi
  ANİME URL FIX (38 ep → tranimaci.com):
    - Dungeon Meshi / Faraway Paladin / Uncle / Baki's Path 2
  KAPSAMLİ PİNG (scripts/ping_all_content.py):
    - 660/660 içerik %100 OK (anime+manga+manhwa)
    - tranimaci.com (497 anime) | manhwahentai.me (118) | ragnarscans.com (39)
    - Sonuç: scripts/ping_results.json
  Episodeli içerik özeti: 8/8 Madara img doğrulaması ✅

SOHBET-72 TAMAMLANDI — Sezon Sistemi ✅:
  - DB: content.season_number + parent_id eklendi (migration otomatik)
  - API: GET /api/content/{id}/seasons → sezon listesi
  - AniList: get_relations() SEQUEL/PREQUEL desteklendi
  - Script: scripts/season_linker.py çalıştırıldı:
    → 8 mevcut S2/S3 parent_id ile S1'e bağlandı
    → 2 yeni S1 oluşturuldu (Tate no Yuusha 682, Spy x Family 683)
    → 35 yeni sequel kartı AniList'ten çekildi (cover+tranimaci URL)
    → Toplam anime: 497 → 534
  - UI: detail view sezon tab bar eklendi (S1/S2/S3 butonlar, tıkla geç)
  - ⚠️ Backend RESTART gerekiyor (bat→5→1 veya 6→restart)
  
  Sezon zinciri örnekleri:
    KonoSuba: S1(412)→S2(714)→S3(101), Spy: S1(683)→S2(106)
    Dungeon Meshi: S1(96)→S2(684), Shangri-La: S1(104)→S2(109+685)[duplikat]

SOHBET-73 SIRASI — Lord karar verir
  [A] Toplu episode URL yükleme (534 anime — 0 episodeli olanlar)
  [B] UI geliştirme / FloatingUI
  [C] KuroRecon alarm
  [D] Shangri-La S2 duplikatı temizle (ID=685 veya 109 sil)

⚠️ ÖNEMLİ:

⚠️ ÖNEMLİ:
  - NAT MODE: .wslconfig networkingMode=NAT (mirrored kaldırıldı)
    Bat→10→1 portproxy otomatik kurar (UAC bir kez)
  - ESLESMEYEN.md: docs/ESLESMEYEN.md — Lord URL bildirir, Claude DB'ye ekler
  - enrich_turkanime.py: SQLite'a direkt yazar (API değil — WSL←→Windows port sorunu)
  - ta_index.json + ta_romaji_cache.json → scripts/ (yeniden çalıştırmaya gerek yok)
  - dizibox.so + hdfilmcehennemi.nl: CF bypass yok, cookies.txt şart (askıya)
  - anizmplayer.com m3u8 → Referer: anizm.net/ şart
  - DB: episode tablosu (çoğulsuz), kolon: number
```

---

## 📦 Proje Yapısı

```
C:\Kuroshin\kurowatch\
  backend/
    main.py              → FastAPI port 8099
    database.py          → migration: title_tr TEXT eklendi (acc5467)
    models.py            → Content.title_tr: Optional[str] eklendi
    routers/
      content.py         → _serialize: title_tr dahil; ContentPatch: title_tr kabul eder
      episodes.py        → bölüm sync
      sites.py / tags.py / sync.py / settings.py / extension.py
    downloader/
      stream_finder.py   → networkidle + JS iframe + 15s + playwright-stealth (4a8d40f)
      anime.py           → yt-dlp wrapper
      manga.py           → Madara + gallery-dl
  frontend/
    index.html           → Edit modal: "Türkçe Başlık" input eklendi
    app.js               → kart+detay: title_tr || title; Edit modal fill+save
  cookies/               → BOŞ (tranimeizle_cookies.txt buraya gelecek)
  tools/
    crawlee_test_tranimeizle.js  → geçici test scripti
    test_tranimeizle.js          → geçici test scripti
```

---

## 🔑 Önemli Notlar

- **title_tr gösterimi:** kart h3 + liste span + detail-title → `title_tr || title`
- **Edit modal:** id=`edit-form-title-tr` input, patchBody'e `title_tr` ekleniyor
- **Tailwind:** JS'de `el.style.X = Y` kullan, dynamic class ÇALIŞMAZ
- **Backend restart:** Bat menüsünden (kod değişince MUTLAKA); `wsl -e bash` ile background başlatma güvenilmez
- **tranimeizle.co:** cookies olmadan bypass yok (Playwright+Crawlee+stealth hepsi başarısız)

---

## ⚠️ HATA YAPMA LİSTESİ (Sohbet-60'tan öğrenildi)

### WSL / Python ortamı
- **Playwright WSL'de SADECE venv'de çalışır:** `/root/kuroshin/venv/bin/activate` kaynak almadan test etme — `python3`, `python3.11` bulamaz
- **Test komutu şablonu:** `wsl -e bash -c "source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -c '...'"` — eksikse import hatası alırsın
- **`wsl -e /bin/bash -c`** → hata verir (Git bash çakışması); her zaman `wsl -e bash -c` kullan
- **WSL'de background process:** `nohup ... &` ve `setsid ... &` PowerShell/Bash üzerinden çalışmaz — Lord'dan bat menüsü restart iste

### Backend geliştirme
- **`model_dump(exclude_none=True)`** → None değer gönderince field güncellenmez; temizleme için `exclude_unset=True` gerekir
- **Backend kodu değişince HEMEN restart:** `stream_finder.py`, `anime.py` vb. değişince Python `sys.modules` cache eski kodu tutar — eski hatayla test etmiş olursun

### Playwright / stream_finder
- **`on_request` callback'i:** Playwright isteği GÖNDERİR ama yanıtın 200 olduğunu garanti etmez; URL'yi bulsan da sunucu reddedebilir
- **turkanime.tv bekleme:** iframe (media.aso1.net → alucard.click) 25-30sn içinde MP4 isteği yapar; 12sn yetmez, 32sn gerekli
- **`found_embed[0]` tuzağı:** İlk yakalanan URL en iyi URL değil; m3u8 → .mp4 → diğer sırayla önceliklendir
- **CF korumalı direkt MP4:** `--impersonate` ve `--extractor-args "generic:impersonate"` işe YARAMAZ; asıl çözüm Playwright'ın kendi request header'larını yakalayıp yt-dlp'ye `--add-header` ile geçirmek

### yt-dlp
- **Cloudflare 403 teşhis:** `HTTP Error 403` + `Server: cloudflare` → CF clearance sorunu; `HTTP Error 429` → rate limit (bekle, tekrar dene)
- **`--add-header "key:value"`** → yt-dlp ilk `:` karakterinde böler, değer içinde `:` olabilir (sec-ch-ua gibi) — sorun yok
- **`range: bytes=0-` header'ı** yt-dlp'ye geçirme — skip et, yt-dlp kendi range header'ını yönetir
- **alucard.click PCT:0 sorunu:** yt-dlp progress satırı parse edilemiyor (muhtemelen format farklı); indirme bitince PCT:100 geliyor, indirme çalışıyor

### Test sırası
- Önce `wsl` ile direkt Python scripti test et (venv'le), sonra API üzerinden test et — böylece hangi katmanda hata olduğu netleşir
- Job "downloading" durumuna geçtiyse başarı; `/downloads/` klasörüne `.part` dosyası büyüyorsa gerçekten iniyor

---

## 📌 Commit Geçmişi (Önemli)

| Commit | Ne |
|--------|----|
| `1dd682a` | turkanime.tv: Playwright header capture + CF bypass (885MB test OK) |
| `acc5467` | title_tr: DB migration + Edit modal + kart/detay gösterimi |
| `4a8d40f` | stream_finder: networkidle + JS iframe + 15s + playwright-stealth |
| `5c9d39c` | Anime indirme Playwright + Referer fix |
| `1cacc29` | Madara manga lazy-load bug fix |
