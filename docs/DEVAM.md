# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 15 Haziran 2026 (sohbet-17) · **Aktif sürüm:** v0.5.0 (FAZ-2) · **Son commit:** `9850e2c`

> Yeni Claude'a tek-sayfa devamlılık. İlk önce **bu MD**'yi oku.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT (copy-paste)

```
KuroWatch DEVAM.md oku. Özet:

EN SON YAPILAN (15 Haz sohbet-17) — FAZ-2 TAMAMLANDI (MangaDex + IGDB + MAL):

✅ backend/config.py — get_config() yardımcı fonksiyon
✅ backend/scraper/mangadex.py — MangaDex API (search/detail/chapter_count, mdx: prefix)
✅ backend/scraper/igdb.py — IGDB Twitch OAuth2 client creds (search/detail)
✅ backend/scraper/mal.py — MAL public API (X-MAL-Client-ID, search/detail, mal: prefix)
✅ content.py: /discover?type=game → IGDB; AniList 0 sonuç → MAL fallback; /discover/mangadex endpoint
✅ content.py: /content/{id}/anilist → mdx:/mal:/game tip routing
✅ episodes.py: _check_one() → game skip, mdx: MangaDex, mal: MAL, else AniList
✅ episodes.py: sync_episodes → mdx: MangaDex, mal: HTTPException, anime/manga AniList
✅ settings.py + main.py: mal_client_id default eklendi
✅ index.html: Keşfet tip seçici (Anime/Manga/Manhwa/Oyun), MAL Client ID ayarı
✅ app.js: _discoverType değişkeni, tip seçici butonları, IGDB arama, MAL kaydet
✅ app.js: Add modal Step-1 tip seçici (anime/manga/manhwa/oyun)
✅ app.js: it.id → it.external_id bug fix (discover kartlarında)
✅ app.js: total_episodes/total_chapters hidden input + prefillAddForm + submitAddContent

Canlı kanıtlar (sohbet-17):
  GET /api/discover?q=naruto&type=anime → 12 sonuç, id=20 (AniList) ✅
  GET /api/discover?q=berserk&type=manga via MangaDex → 12 sonuç, mdx:UUID ✅
  GET /api/discover?q=elden+ring&type=game (no creds) → [] ✅
  GET /api/discover?q=solo+leveling&type=manhwa → 3 sonuç (AniList) ✅
  MangaDex chapter_count: Berserk=384, Spy×Family=127 ✅
  GET /api/settings → mal_client_id: "" ✅

✅ IGDB canlı test (sohbet-17 devam):
  Elden Ring (2022) score=95, RDR2 score=94, Zelda BotW — IGDB çalışıyor
  Credentials: config.json'da (.gitignore'da, güvende)
  Twitch App: KuroWatch, Client ID: c9p2...

SIRADAKI GÖREV (sohbet-18):
Seçenekler:
B) FAZ-3 Player/Downloader — yt-dlp backend entegrasyonu
C) PWA + Push notification entegrasyonu
D) Mobile ADB kurulum (Termux + KuroWatch)

BAŞLATMA KOMUTU:
wsl -d Ubuntu-22.04 -u root -- bash -c "fuser -k 8099/tcp 2>/dev/null; sleep 1; source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -m uvicorn backend.main:app --port 8099"

AKTİF DOSYALAR:
- backend/scraper/mangadex.py → MangaDex API (yeni)
- backend/scraper/igdb.py → IGDB Twitch auth (yeni)
- backend/scraper/mal.py → MAL fallback (yeni)
- backend/routers/content.py → discover game/mangadex routing
- backend/routers/episodes.py → check_one multi-source
- frontend/app.js → discover tip seçici + add modal tip
- frontend/index.html → discover UI + MAL settings
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
