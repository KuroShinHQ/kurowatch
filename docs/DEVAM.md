# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 23 Haziran 2026 (sohbet-77) · **Aktif sürüm:** v1.2.0 → v7 revizyon başladı · **Son commit:** `b877af5`

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

**FAZ-V7-0: CSS Token Temeli** ← BAŞLANGIÇ NOKTASI
```
[ ] Stitch HTML'lerden ortak Tailwind config bloğunu çıkar
[ ] kurowatch/frontend/tailwind.config.js → v7 token sistemi ekle
    (bg-primary:#0d0d1a, bg-card:#1a1a2e, primary-container:#00d4ff)
[ ] style.css :root → v7 CSS değişkenlerini unify et
[ ] tailwindcss.exe ile local build → tailwind.css?v=7 üret
[ ] Tüm Stitch HTML'lerdeki CDN linklerini listele → silinecekler
```

**FAZ-V7-1: Home v7** (kurowatch_home_solo_leveling_sim/code.html)
```
[ ] Sinematik Hero banner → radyal gradyan + "Nebula Genesis" benzeri
[ ] "Devam Et" satırı → shimmer progress bar + Electric Cyan glow
[ ] Poster grid v7 → hover scale(1.02→1.18) + active:scale-[0.95]
[ ] index.html #screen-home içeriğini Stitch v7 ile replace et
[ ] app.js renderHome() → v7 hero + devam-et satırı kısımları ekle
```

**FAZ-V7-2: Search v7** (kurowatch_search_filter_v7_master/code.html + arama_filtreleme_hybrid)
```
[ ] Akıllı filtre paneli (tür/yıl/puan slider) → v7 slide-in panel
[ ] Sonuç kart grid → v7 card spec (hover 1.02→1.18)
[ ] index.html #screen-search → Stitch v7 ile replace et
[ ] app.js renderSearch() → filtre panel toggle + filtre state
```

**FAZ-V7-3: Detail v7** (kurowatch_detail_solo_leveling_sim/code.html)
```
[ ] v7 hero kapak → backdrop blur + renk ayarı
[ ] Bölüm listesi → is_watched badge + progress odaklı sıralama
[ ] Karakter galerisi → yatay scroll, karakter kartları
[ ] index.html #screen-detail → Stitch v7 ile replace et
[ ] app.js openDetail() → karakter galerisi + bölüm listesi render
```

**FAZ-V7-4: Video Player v7 Cinema Master**
```
Ana player (kurowatch_video_oynat_c_v7_gold_master_hybrid/code.html):
[ ] Tüm alt overlay HTML'leri ana player'a gömülü hale getir:
    - Altyazı/Ses seçimi (kurowatch_video_oynat_c_altyaz_ve_ses_se_imi_v7)
    - Bölüm seçimi (kurowatch_video_oynat_c_b_l_m_se_imi_v7)
    - Kalite seçimi (kurowatch_video_oynat_c_kalite_se_imi_v7)
[ ] Ambient Glow canvas → requestAnimationFrame dominant renk
[ ] Intro Atla / Sonraki Bölüm → markers.intro/outro logic
[ ] Ekran kilidi → pointer-events-none + 2sn basılı tutma
[ ] Capture → canvas.drawImage + Blob indir
[ ] index.html #modal-player → Stitch v7 ile replace et
[ ] player.js → v7 kontrol mantığı (hız/kalite/altyazı/ambient)
[ ] API: GET /api/v7/player/init/:episode_id (stream + markers + assets)
[ ] API: POST /api/v7/player/sync (heartbeat 30sn)
```

**FAZ-V7-5: Manga Reader v7 Hybrid**
```
[ ] Webtoon/Sayfa hybrid engine → IntersectionObserver (webtoon) + swipe (sayfa)
[ ] Kuro Translate panel → v7 AI çeviri arayüzü
    (kurowatch_kuro_translate_v7_master + smart_clean_sim)
[ ] Smart Clean sim → opacity slider + text block overlay
[ ] Lazy loading → loading="lazy" + decoding="async"
[ ] Pre-fetch n+1, n+2 sayfaları
[ ] index.html manga reader → Stitch v7 ile replace et
[ ] API: GET /api/v7/reader/chapter/:id
[ ] API: POST /api/v7/translate/vision (image_url + target_lang + smart_clean)
[ ] API: POST /api/v7/reader/sync (heartbeat, last_page)
```

**FAZ-V7-6: Updates v7** (kurowatch_updates_v7_master_rafine/code.html)
```
[ ] Zaman akışı → yeniden eskiye sıralama
[ ] Okunmamış → sol cyan border + parlak bg
[ ] index.html #screen-updates → Stitch v7 ile replace et
[ ] app.js renderUpdates() → v7 zaman akışı
```

**FAZ-V7-7: Downloads v7** (kurowatch_downloads_v7_master_rafine/code.html)
```
[ ] Depolama göstergesi → cihaz storage bar
[ ] İndirme hızı → aktif job'lar için hız (MB/s)
[ ] index.html #screen-downloads → Stitch v7 ile replace et
[ ] app.js renderDownloads() → v7 storage bar + hız
```

**FAZ-V7-8: Stats v7** (kurowatch_stats_v7_master/code.html)
```
[ ] Tür dağılım grafikleri → CSS/SVG donut + bar chart v7
[ ] İzleme süreleri → toplam saat + günlük ortalama
[ ] index.html #screen-stats → Stitch v7 ile replace et
[ ] app.js renderStats() → v7 grafik render
```

**FAZ-V7-9: Settings v7 Master** (kurowatch_settings_v7_final_master/code.html)
```
[ ] API key form'ları → AniList/MAL/IGDB/DeepL validate butonu
[ ] Çeviri ayarları → (kurowatch_eviri_ayarlar_v7_final_simulation)
[ ] İndirme ayarları → otomatik silme, kalite seçici
[ ] index.html #screen-settings → Stitch v7 ile replace et
[ ] app.js renderSettings() → v7 form'lar + API key doğrulama
[ ] API: POST /api/proxy/validate-key (service + key)
[ ] API: PATCH /api/user/settings
```

**FAZ-V7-10: JS Event Wiring (app.js refactor)**
```
[ ] Tüm v7 ekranları için event handler'ları app.js'e ekle
[ ] showScreen() → v7 geçiş animasyonları (spring)
[ ] data-api-endpoint + data-field özniteliklerini bağla
[ ] 4px grid kuralı kontrolü (8/12/16/24px spacing)
[ ] active:scale-[0.95] → tüm interaktif elemanlara
```

**FAZ-V7-11: Iron Inquisitor Kalite Testi**
```
[ ] v7 tasarım kalitesi testi — pixel-perfect kontrol
[ ] Renk drift kontrolü (#0d0d1a / #00d4ff tutarlılığı)
[ ] 4px grid kuralı ihlalleri
[ ] CDN bağımlılığı kalmadı mı kontrol
```

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (22 Haz sohbet-71b):
  - 679 içerik, backend ✅ ÇALIŞIYOR (localhost:8099, bat→10→1 ile başlat)
  - Test: http://localhost:8099

SOHBET-71 TAMAMLANDI — URL Sağlık + Kapsamlı Ping ✅
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
