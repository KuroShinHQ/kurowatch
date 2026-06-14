# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 14 Haziran 2026 (sohbet-2) · **Aktif sürüm:** v0.1.0 · **Son commit:** `2974da6`

> Yeni Claude'a tek-sayfa devamlılık. İlk önce **bu MD**'yi oku.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT (copy-paste)

```
KuroWatch DEVAM.md oku. Özet:

EN SON YAPILAN (14 Haz sohbet-1):
✅ GitHub repo oluşturuldu: github.com/KuroShinHQ/kurowatch (private)
✅ Klasör yapısı kuruldu: C:\Kuroshin\kurowatch\
✅ gh CLI kuruldu: C:\Kuroshin\tools\gh.exe
✅ Kuroshin.bat [10]: KuroWatch başlat (port 8099)
✅ Tüm tasarım kararları netleşti (30 karar)
✅ Araştırma tamamlandı: Stitch AI, Claude Code, tracker şikayetleri, Netflix animasyon

OLUŞTURULAN DOSYALAR:
- CLAUDE.md          → Sonnet 4.6 direktifleri, API stratejisi, bug önleme
- docs/DEVAM.md      → bu dosya
- docs/YAPI.md       → mimari, veri modeli, backend kararları
- docs/DESIGN.md     → Stitch AI final prompt (BATCH 1 ve BATCH 2)
- docs/FEATURE_MAP.md → tüm özelliklerin diyagramı, dosya eşleştirme, checklist

SIRADAKI GÖREV (öncelik sırası):
1. Stitch AI'a git → DESIGN.md "Stitch AI Final Prompt" bölümünü kopyala
   BATCH 1 (Standard mod): Home + Detail + Search + Updates + Stats
   BATCH 2 (Experimental mod): Add Modal + Settings + Conflict Modal
2. Stitch çıktısı gelince → frontend/ klasörüne koy
3. Post-Stitch checklist uygula (DESIGN.md'de var)
4. Backend yazmaya başla:
   - backend/database.py (SQLite async engine + aiosqlite)
   - backend/models.py (Content, Site, Episode, Update, Tag, ContentTag — TrackingSession MVP dışı)
   - backend/main.py (FastAPI app)
   - backend/routers/content.py (CRUD + /api/discover)
```

---

## 🎯 NEREDE KALDIK

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

### 🔴 Sıradaki (Öncelik Sırası)

**ÖNCE: Stitch AI Frontend**
1. stitch.google.com → DESIGN.md "Stitch AI Final Prompt" bölümü → BATCH 1
2. Çıktıyı `frontend/` klasörüne koy
3. DESIGN.md post-Stitch checklist uygula (Google token temizle, app.js yaz, manifest ekle)
4. BATCH 2 → Add Modal + Settings + Conflict Modal

**SONRA: Backend**
5. `backend/database.py` → SQLite async engine
6. `backend/models.py` → Content, Site, Episode, Tag, Update, Config
7. `backend/main.py` → FastAPI app (port 8099, CORS, startup)
8. `backend/routers/content.py` → CRUD
9. `backend/routers/sync.py` → export/import/conflict
10. `backend/scraper/anilist.py` → AniList GraphQL

---

## 🛠️ KRİTİK BİLGİLER

### Stack
- Backend: Python FastAPI + SQLAlchemy async + SQLite (aiosqlite)
- Frontend: Stitch AI çıktısı → HTML/CSS + Manuel vanilla app.js
- Mobil: PWA (manifest.json + sw.js)
- Port: 8099

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
