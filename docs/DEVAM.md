# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 15 Haziran 2026 (sohbet-19) · **Aktif sürüm:** v0.8.0 (FAZ-4+ADB) · **Son commit:** `4bd8205`

> Yeni Claude'a tek-sayfa devamlılık. İlk önce **bu MD**'yi oku.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT (copy-paste)

```
KuroWatch DEVAM.md oku. Özet:

EN SON YAPILAN (15 Haz sohbet-19) — D+E+F tamamlandı:

D) Kuroshin.bat KUROWATCH [3] Mobil ADB Bağlantısı eklendi
   - adb reverse tcp:8099 tcp:8099 → telefon localhost:8099 = PC port 8099
   - ADB otomatik bulma (PATH/LOCALAPPDATA/C:\Android)
   - Chrome PWA kurulum talimatları

E) FAZ-3 canlı test — YouTube (me at the zoo, 19sn) ile yt-dlp doğrulandı
   - POST /api/download/start → status:done, 465KB, 8sn PASS ✅
   - DELETE /api/download/1 → file_deleted PASS ✅
   - GET /api/download/storage → 0B PASS ✅

F) FAZ-4 Chromaprint intro tespiti — commit 4bd8205
   - backend/analyzer/chromaprint.py — fpcalc async wrapper + .fp.json cache
   - backend/analyzer/intro_detector.py — sliding window hamming distance, consensus
   - backend/models.py — IntroTimestamp ORM (content_id, ep, start, end, confidence)
   - backend/routers/analyze.py — POST/GET/DELETE /api/analyze/intro/{id}[/{ep}]
   - frontend/player.js — _intro.load/tick/skip, openVideo contentId+ep
   - frontend/index.html — #skip-intro-btn overlay (bottom-right)
   Canlı kanıt: ep1+ep2 (aynı 19sn video) → start:0.0, end:19.0, confidence:1.0 PASS ✅

⏭️ SIRADAKI GÖREV (sohbet-20):
- Push (git push origin main) — her iki repo için
- Diziwatch/Crunchyroll gerçek URL canlı testi (kullanıcı URL sağlarsa)
- FAZ-5 (Çeviri motoru) veya Lord'un belirleyeceği yön

BAŞLATMA:
wsl -d Ubuntu-22.04 -u root -e bash -c "source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -m uvicorn backend.main:app --port 8099 --log-level warning"

AKTİF DOSYALAR:
- backend/analyzer/chromaprint.py  → fpcalc wrapper (yeni FAZ-4)
- backend/analyzer/intro_detector.py → LCS karşılaştırma (yeni FAZ-4)
- backend/routers/analyze.py        → analyze router (yeni FAZ-4)
- frontend/player.js                → Skip Intro butonu (güncellendi)
- Kuroshin.bat (ana repo)           → [10/3] ADB mobile (güncellendi)
```

---

## FAZ-3 TAMAMLANDI (15 Haz sohbet-18)

EN SON YAPILAN (15 Haz sohbet-18) — FAZ-3 TAMAMLANDI (İndirici + Player + Manga Reader):

Commit: 06985ba

✅ backend/downloader/anime.py — yt-dlp async subprocess, ilerleme % parse, mp4/mkv/webm çıktı
✅ backend/downloader/manga.py — MangaDex API sayfalar + gallery-dl Madara siteleri
✅ backend/downloader/manager.py — in-memory kuyruk (max 2 eşzamanlı), WS push, daisy-chain tetikleyici
✅ backend/routers/download.py — POST /start, GET /queue, DELETE /{id}, GET /storage
   + GET /serve/{id} (video stream range), GET /pages/{id} + GET /page/{id}/{i} (manga)
   + WebSocket /download/ws (kuyruk durumu push)
✅ backend/main.py — download router eklendi
✅ backend/requirements.txt — yt-dlp 2026.6.9 + gallery-dl 1.32.3 + websockets kuruldu
✅ frontend/player.js — WS bağlantısı, kuyruk render, video player HTML5, manga reader (webtoon/sayfa modu), daisy-chain N+1 otomatik kuyruk
✅ frontend/index.html — İndirmeler ekranı, Player modal, Manga Reader modal, nav badge
✅ frontend/app.js — İndirmeler render hook, bölüm satırına download butonu

Canlı kanıtlar:
  GET /api/download/queue → {"jobs":[]} ✅
  GET /api/download/storage → {"bytes":0,"mb":0.0} ✅
  POST /api/download/start → {"id":1,"status":"queued",...} ✅

✅ FAZ-C (PWA Push) TAMAMLANDI (sohbet-18, commit 8fcbe7b):
- backend/push_manager.py — VAPID key üretimi + abonelik dosya depolama + push gönderimi
- backend/routers/push.py — /push/vapid-public-key + /push/subscribe + /push/test
- episodes.py — check_updates yeni bölüm bulunca push otomatik
- frontend/pwa.js — SW kaydı + subscribe/unsubscribe + VAPID base64url→Uint8Array
- frontend/sw.js — push event + notificationclick, cache v2
- Settings: Push Bildirimleri toggle + Test butonu
VAPID public key: BJ45SGKJg3kn4ucbVjLLEyz8NBes6n3GtKRCY3iXD8PomvLkfmY7EsEfsTpSrXsrjElzjiON7ZXfzu89wHE9cvw

SIRADAKI GÖREV (sohbet-20):
- Push (git push origin main) — kurowatch + kuroshin
- Diziwatch/Crunchyroll gerçek URL canlı testi
- FAZ-5 Çeviri motoru veya Lord belirleyecek

BAŞLATMA KOMUTU:
wsl -d Ubuntu-22.04 -u root -e bash -c "fuser -k 8099/tcp 2>/dev/null; sleep 1; source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -m uvicorn backend.main:app --port 8099 --log-level warning > /tmp/kwb.log 2>&1 &"

AKTİF DOSYALAR:
- backend/downloader/anime.py  → yt-dlp wrapper (yeni)
- backend/downloader/manga.py  → MangaDex + gallery-dl (yeni)
- backend/downloader/manager.py → kuyruk + WS (yeni)
- backend/routers/download.py  → download router (yeni)
- frontend/player.js           → player + reader + WS (yeni)
- frontend/index.html          → İndirmeler ekranı + modaller
- frontend/app.js              → İndir butonu bölüm satırında
```

---

## FAZ-2 TAMAMLANDI (15 Haz sohbet-17)

EN SON YAPILAN (15 Haz sohbet-16) — FAZ-1 kalan görevler sırayla (commit 74bd0d6):

✅ ContentPatch'e external_id eklendi (PATCH ile AniList ID atanabilir)
✅ apiPatch() eklendi (frontend)
✅ renderDetail(): cover_url → bg-image; interaktif yıldız (hover+click → PATCH my_score)
✅ renderArchive(): status=completed filtresi, cover/initials, "Geri Al" → PATCH watching
✅ renderSettings(): config.json okuma, IGDB kaydet, auto-delete toggle, kalite butonları
✅ Settings "Dışa Aktar" → GET /api/export → JSON indir
✅ showScreen → archive/settings ekranı açılınca renderArchive/renderSettings tetikleniyor
✅ index.html: archive-list/archive-count, settings element ID'leri

Canlı kanıt:
  PATCH /api/content/3 {external_id:"87216", total_chapters:200} ✅
  POST /api/check-updates → {checked:3, new_updates:7} ✅
  GET /api/updates → 1 update (JJK 200→207, AniList) ✅

BAŞLATMA KOMUTU:
wsl -d Ubuntu-22.04 -u root -- bash -c "fuser -k 8099/tcp 2>/dev/null; sleep 1; source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -m uvicorn backend.main:app --port 8099"

SIRADAKI GÖREV (sohbet-10):
1. Updates ekranı → "Kontrol Et" butonu /api/check-updates çağırsın
2. Updates ekranı → content_title alanı eksik (DB'den join gerekiyor)
3. Home grid → cover resmi kart üzerinde göster
4. Detail → "Siteler" ve "Notlar" tab içeriği bağla
5. PWA test (mobil Chrome → "Ana ekrana ekle")

KESİNLEŞEN KARARLAR (bu sohbette):
- Mimari: PC + Telefon (Termux) bağımsız, JSON export/import sync
- Telefon kurulum: USB + ADB ile Claude halleder (uygulama bittikten sonra)
- Daisy chain: bölüm %50'de N+1 indir, N bitti → N-1 sil (ayarlanabilir)
- Toplu indirme: tüm seri tek tuşla
- Manhwa/manga için aynı sistem
- Cover resimler: API'den otomatik, yoksa kullanıcı URL girer, hâlâ yoksa fallback SVG
- PWA icon: KuroWatch logo (göz + yazı) — frontend build sırasında oluşturulacak

STİTCH ÇIKTISI ANALİZİ — KRİTİK SORUNLAR:

❌ CDN BAĞIMLILIĞI (offline'da ÇALIŞMAZ):
   - cdn.tailwindcss.com → Tailwind CDN (internet kesince app ölür)
   - fonts.googleapis.com/css2?family=Material+Symbols+Outlined → Google Fonts CDN

❌ 9 AYRI HTML DOSYASI (SPA değil):
   - Her ekran ayrı dosya, sayfa yenilenerek geçiş yapıyor
   - Tek index.html'de section'lara dönüştürülmeli

❌ RENK TUTARSIZLIĞI (ekranlar arası sürükleme):
   - Home bg: #0d0d1a ✅
   - Add Content bg: #0e1417 ❌ (farklı!)
   - Material Design token drift — her ekran farklı generate edildi

❌ MATERIAL DESIGN TOKEN İSİMLERİ:
   - surface-container-high, on-tertiary, on-surface-variant vb.
   - Bunlar Tailwind config'de, CSS variable değil
   - --kw-* custom property'lere dönüştürülmeli

❌ JS YOK: Tüm butonlar statik HTML

SIRADAKI GÖREV (öncelik sırası):
1. frontend/ klasörü kur → 9 code.html'yi tek index.html'ye birleştir
2. CDN'leri kaldır → Tailwind yerine vanilla CSS, Material Symbols yerine SVG icon
3. Renk drift'ini düzelt → tüm ekranlarda #0d0d1a bg
4. app.js yaz → navigasyon + mock data (backend olmadan çalışsın)
5. debug-logger.js yaz → click/fetch/error yakalayan overlay
6. UX eksikliklerini ekle (back button, pull-to-refresh, swipe dismiss, loading state)

STITCH DOSYA KONUMLARI:
C:\Kuroshin\kuroshin-downloads\stitch_kurowatch_media_tracker\
  kurowatch_home_refined\code.html       → HOME (227KB — Tailwind inline)
  content_detail_refined\code.html       → DETAIL
  search_discover_refined\code.html      → SEARCH
  updates_refined\code.html             → UPDATES
  library_stats_refined\code.html       → STATS
  add_content_overlay\code.html          → ADD MODAL
  archive\code.html                      → ARCHIVE
  import_conflict_modal\code.html        → CONFLICT MODAL
  kurowatch_1\DESIGN.md                  → Stitch tasarım özeti (yedek)
```

---

## 🎯 NEREDE KALDIK

### ✅ Sohbet-7'de Tamamlananlar (14 Haz 2026) — Backend FAZ-1

- **database.py**: SQLite async engine, aiosqlite, get_db dependency
- **models.py**: Content/Site/Episode/Update/Tag/ContentTag SQLAlchemy ORM
- **main.py**: FastAPI app, CORS, lifespan (init_db + startup check-updates), static catch-all
- **6 router**: content (CRUD+discover), episodes (check-updates), sites, tags, settings, sync
- **scraper/anilist.py**: AniList GraphQL search + get_detail, manhwa = countryOfOrigin KR
- **.gitignore**: backend/config.json + downloads/ + **/__pycache__/ eklendi
- Commit: `834b8ab`

### ✅ Sohbet-6'da Tamamlananlar (14 Haz 2026) — Faz-B CDN Kaldırma

- **Tailwind CLI** `tools/tailwindcss.exe` (v4.3.1, standalone, Node.js'siz)
- `tailwind.config.js` + `tailwind-input.css` → Tailwind v4 @import + @theme + @layer
- `frontend/tailwind.css` derlendi (42KB, tüm custom class'lar dahil)
- **Material Symbols WOFF2** indirildi → `frontend/icons/material-symbols.woff2` (1.1MB)
- `style.css` → @font-face + `.material-symbols-outlined` lokal tanım
- **index.html** → Tailwind CDN + Google Fonts CDN + inline script config TAMAMEN kaldırıldı
- **PWA icon-192.png + icon-512.png** PIL ile üretildi (göz logosu tasarımı)
- Commit: `eab4369`

### ✅ Sohbet-2'de Tamamlananlar (14 Haz 2026)

**MD Araştırma + Düzeltme:**
- YAPI.md: `Update` tablosu eklendi, APScheduler çelişkisi giderildi, 6 eksik endpoint eklendi
- YAPI.md: Manhwa = `type: MANGA, countryOfOrigin: KR` (AniList'te ayrı tip yok)
- YAPI.md: `my_score` nullable, `external_id` + `my_progress_pct` alanları eklendi
- YAPI.md: TrackingSession → MVP DIŞI, IGDB token cache + VAPID config eklendi
- YAPI.md: AniList rate limit (90/dk), IGDB token ömrü (~60 gün), MangaDex API (FAZ-2) belgelendi
- YAPI.md: `nextChapter` yok → manga güncelleme = `API.chapters > DB.total_chapters` karşılaştırması
- FEATURE_MAP.md: Backend checklist güncellendi (TrackingSession MVP dışı, doğru router listesi)
- Klasör yapısı: `tracking.py` kaldırıldı → `settings.py` + doğru router isimleri

**Araştırma Özeti (Sohbet-2):**
- AniList: 90 req/dk limit, `chapters` field manga güncelleme tespiti için
- IGDB: Twitch token ~60 gün, `cover.image_id` → URL prefix ekle
- MAL OAuth: localhost:5050 redirect, single-user için yeterli
- Web Push: `pywebpush` + `py-vapid`, VAPID keys config.json'da
- CSS Donut chart: SVG `stroke-dasharray` veya `conic-gradient()` (kütüphane yok)
- MangaDex API: auth yok, `/manga/{id}/feed` son chapter için

### ✅ Sohbet-1'de Tamamlananlar (14 Haz 2026)

**Altyapı:**
- `gh` CLI kuruldu (`C:\Kuroshin\tools\gh.exe`)
- GitHub repo: `KuroShinHQ/kurowatch` (private, 6 commit)
- `C:\Kuroshin\kurowatch\` klasör yapısı
- Kuroshin.bat `[10]` → KuroWatch başlat
- Ana Kuroshin `.gitignore`'a `kurowatch/` eklendi

**Dokümantasyon (tamamen hazır):**
- `CLAUDE.md` — AniList/MAL/IGDB API stratejisi, bug önleme, sohbet protokolü
- `docs/YAPI.md` — mimari, veri modeli, 30 backend kararı (araştırma bulguları dahil)
- `docs/DESIGN.md` — Stitch AI final prompt (8 ekran, renk paleti, animasyon, haptic, PWA)
- `docs/FEATURE_MAP.md` — ASCII diyagram, veri akışı, dosya→özellik haritası, checklist

**Araştırma tamamlandı:**
- Stitch AI: max 5 ekran/üretim, 2 batch planı, post-Stitch checklist
- Claude Code: context kaybı, rate limit, atomic commit protokolü
- Tracker şikayetleri: MAL/AniList eksiklerinin KuroWatch'ta nasıl çözüldüğü tablosu
- Premium animasyon: Netflix spring curves, Web Vibration API haptic sistemi

### ✅ Sohbet-4'te Tamamlananlar (14 Haz 2026)
- Stitch AI 9 ekran üretildi (Home/Detail/Search/Updates/Stats/Add/Archive/Conflict/Settings)
- Stitch çıktısı analiz edildi — 5 kritik sorun tespit edildi
- DEVAM.md + FEATURE_MAP.md + YAPI.md frontend build planıyla güncellendi

### 🔴 Sıradaki (Öncelik Sırası) — sohbet-8

1. `app.js` USE_MOCK=false → E2E test (frontend → /api/content → DB)
2. Discover ekranı AniList araması bağlantısı (frontend renderSearch → /api/discover)
3. `Add Content` formu → /api/content POST gerçek çağrı
4. `/api/check-updates` canlı test (AniList external_id'li içerikle)
5. Kuroshin.bat [10] → venv path fix

---

## 🛠️ KRİTİK BİLGİLER

### Deployment Mimarisi (Kesinleşti — 14 Haz)
```
PC (Windows) — kendi bağımsız instance:
  uvicorn backend.main:app --port 8099
  İndirmeler → C:\Users\...\Downloads\KuroWatch\
  SQLite    → kurowatch/memory/kurowatch.db

Telefon (Android, Termux kurulu ✅, USB debug açık ✅):
  uvicorn backend.main:app --port 8099
  İndirmeler → /sdcard/Download/KuroWatch/
  SQLite    → ~/kurowatch/memory/kurowatch.db

Sync: Settings > Export JSON → diğer cihazda Import
Dışarıdan erişim + HTTPS + bildirim: Cloudflare Tunnel (Termux'ta)
```

### İndirme Davranışı (FAZ-3 — Kesinleşti)
```
Daisy chain:   Bölüm %50'de → N+1 arkaplanda inmeye başlar
               N+1 başlayınca → N+2 başlar (zincir devam)
Auto-delete:   N bitti → N-1 silindi (config: auto_delete=true/false)
Toplu indirme: Tüm seri → baştan sona seçili kalitede
Kalite:        Global ayar (360p/720p/1080p/best) — config.json
Aynısı manhwa/manga için geçerli (chapter bazlı)
```

### Stack
- Backend: Python FastAPI + SQLAlchemy async + SQLite (aiosqlite)
- Frontend: Stitch AI çıktısı → HTML/CSS + Manuel vanilla app.js
- Mobil: PWA (manifest.json + sw.js)
- Port: 8099 (hem PC hem Termux)

### API Stratejisi
| İçerik | Birincil | Fallback |
|---|---|---|
| Anime | AniList GraphQL (ücretsiz, auth yok) | MAL OAuth2 |
| Manga | AniList GraphQL | scraper |
| Manhwa | AniList GraphQL | scraper |
| Oyun | IGDB (Twitch auth) | manuel |

### Stitch AI Batch Planı
```
BATCH 1 (Standard mod, 1 generation):
  Home + Detail + Search + Updates + Stats

BATCH 2 (Experimental mod, 1 generation):
  Add Modal + Settings + Conflict Modal
```

### Önemli Dosyalar
```
docs/DESIGN.md      → Stitch'e verilecek prompt (son bölüm: "Stitch AI Final Prompt")
docs/FEATURE_MAP.md → Tüm özellikler nerede, hangi dosyada → kaybolursa buraya bak
docs/YAPI.md        → Backend kararları, API detayları
CLAUDE.md           → Geliştirme direktifleri
```

### Komutlar
```powershell
# Backend başlat
cd C:\Kuroshin\kurowatch
python -m uvicorn backend.main:app --reload --port 8099

# gh CLI (PATH'e ekle)
$env:PATH += ";C:\Kuroshin\tools"
gh --version

# Git push
$env:PATH += ";C:\Kuroshin\tools"
git push origin main
```

### Portlar (Kuroshin ile çakışma yok)
```
8099 → KuroWatch Backend
8080 → Llama server
9003 → Bridge WS
9004 → Bridge HTTP
9005 → Chancellor HTTP
```
