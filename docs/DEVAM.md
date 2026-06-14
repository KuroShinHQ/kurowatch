# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 14 Haziran 2026 (sohbet-6) · **Aktif sürüm:** v0.1.1 · **Son commit:** `eab4369`

> Yeni Claude'a tek-sayfa devamlılık. İlk önce **bu MD**'yi oku.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT (copy-paste)

```
KuroWatch DEVAM.md oku. Özet:

EN SON YAPILAN (14 Haz sohbet-6) — Faz-B CDN Kaldırma TAMAM (commit eab4369):

✅ frontend/ klasörü dolu (13 dosya):
   - index.html      → 7 section + 2 modal SPA shell, SIFIR CDN (68KB)
   - tailwind.css    → Tailwind CLI v4.3.1 derlendi (42KB, lokal)
   - style.css       → @font-face Material Symbols + :root --kw-* değişkenleri
   - app.js          → navigasyon + 5 mock item + apiGet/apiPost (USE_MOCK=true)
   - debug-logger.js → KuroLog overlay (?kurodev=1 veya logo 3x tık)
   - i18n.js         → TR/EN data-i18n sistemi
   - locales/tr.json + en.json → 89 anahtar
   - manifest.json   → PWA: theme #00d4ff, bg #0d0d1a
   - sw.js           → cache-first shell + network-first /api/*
   - icons/icon.svg  → KuroWatch göz logosu
   - icons/material-symbols.woff2 → lokal Material Symbols font (1.1MB)
   - icons/icon-192.png + icon-512.png → PWA PNG ikonları (PIL ile üretildi)

✅ Tailwind v4 build kurulumu:
   - C:\Kuroshin\tools\tailwindcss.exe (v4.3.1, 107MB standalone)
   - tailwind.config.js + tailwind-input.css (v4 @import + @theme + @layer utilities)
   - Custom class'lar dahil: font-label-caps, text-display-lg, rounded-card, p-gutter vb.
✅ SIFIR CDN bağımlılığı — PWA offline tamamen çalışır
✅ HTTP test: tüm 13 dosya 200 OK

SIRADAKI GÖREV (sohbet-7 / Backend):
1. backend/database.py → SQLite async engine (aiosqlite)
2. backend/models.py → Content, Site, Episode, Tag ORM
3. backend/main.py → FastAPI app (port 8099, CORS, router kayıt)
4. backend/routers/content.py → CRUD (GET /api/content, POST, PATCH, DELETE)
5. backend/routers/episodes.py → /api/check-updates
6. Curl ile test: app.js'deki USE_MOCK=false yap → API uç noktaları doğrula

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

### 🔴 Sıradaki (Öncelik Sırası)

**ÖNCE: Frontend Build (backend olmadan tam çalışacak)**
1. `frontend/index.html` → 9 code.html'yi tek dosyada birleştir (section'lar)
2. CDN'leri kaldır:
   - Tailwind CDN → vanilla CSS (class'ları dönüştür)
   - Google Fonts CDN → SVG ikonlar (Heroicons/Phosphor local)
3. Renk tutarsızlıklarını düzelt (tüm ekranlarda #0d0d1a)
4. `frontend/app.js` → navigasyon + mock data (API olmadan)
5. `frontend/debug-logger.js` → click/fetch/error overlay logger
6. UX eksiklikleri: back button, pull-to-refresh, swipe-dismiss, loading state, error state

**SONRA: Backend**
7. `backend/database.py` → SQLite async engine
8. `backend/models.py` → Content, Site, Episode, Tag, Update, Config
9. `backend/main.py` → FastAPI app (port 8099, CORS, startup)
10. `backend/routers/content.py` → CRUD
11. `backend/routers/sync.py` → export/import/conflict
12. `backend/scraper/anilist.py` → AniList GraphQL

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
