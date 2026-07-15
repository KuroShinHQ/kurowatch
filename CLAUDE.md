# KuroWatch — Claude Code Direktifleri

## Model & Çalışma Şekli

**Model:** Claude Sonnet 4.6 (200K context, hybrid reasoning, adaptive thinking)

Nasıl kullanmalı:
- Mimarı kararlar ve çok dosyalı değişiklikler için Plan Mode kullan (önce sor, sonra yaz)
- Küçük, net scoplu değişikliklerde direkt uygula — plan mode overhead
- Context dolunca → `docs/DEVAM.md` güncelle + commit + Lord'a rapor ver (Kuroshin ana projesi gibi)
- Sonnet 4.6 adaptive thinking: karmaşık problem → otomatik daha çok düşünür; basit → hızlı gider

### Sohbet Yönetimi (Araştırma — Kritik)
Araştırma bulgusu: Claude Code uzun sohbette reasoning history kaybeder → garip kararlar, tekrar.
```
HER SOHBET:    1 modül = 1 sohbet (örn: database.py sohbeti, content router sohbeti)
HER MODÜL:     Tamamlanınca commit + DEVAM.md güncelle
RATE LIMIT:    Büyük refactor = ayrı sohbet; küçük fix = mevcut sohbet
CONTEXT DOLU:  Sormadan DEVAM.md güncelle + commit + yeni sohbet talimatı ver
```

---

## API Stratejisi (Araştırıldı — 14 Haz 2026)

### Anime / Manga — AniList (ÖNCELİKLİ)
```
Endpoint: POST https://graphql.anilist.co
Auth: YOK (okuma için tamamen public)
Format: GraphQL query + variables
Veri: 500K+ anime/manga, bölüm sayısı, kapak, türler, yayın durumu
```
**Neden önce AniList:** Auth gerektirmiyor, büyük veritabanı, GraphQL esnek.

### Anime / Manga — MAL (FALLBACK)
```
Base URL: https://api.myanimelist.net/v0.20/
Auth: OAuth2 PKCE, Bearer token, X-MAL-Client-ID header
```
**Dikkat:** MAL auth karmaşık — AniList bulamazsa devreye gir.

### Oyunlar — IGDB (Twitch)
```
Base URL: https://api.igdb.com/v4
Auth: Twitch OAuth2 Client Credentials (Client ID + Secret → Bearer token)
Format: POST, APICalypse query language (kendi sözdizimi)
Ücretsiz: non-commercial için evet
```
**Kurulum:** Twitch Dev hesabı + Client ID/Secret → `backend/scraper/igdb.py`

### Web Scraper (SON ÇARE)
- AniList/MAL/IGDB bulamazsa scraper devreye girer
- `backend/scraper/parsers.py` → site parser'ları (chapter_check.py'nin yerini aldı)
- `backend/scraper/sources.py` → kaynak (source) kayıt defteri
- Her site için ayrı parser yaz (siteler değişir)

---

## Web Search Ne Zaman Kullan

| Durum | Neden Arama Gerekli |
|---|---|
| Yeni site scraper yazarken | Sitenin CSS selector'ları değişmiş olabilir |
| AniList/IGDB API değişikliği şüphesi | Endpoint/field deprecated olabilir |
| Yeni FastAPI/SQLAlchemy sürümü | Breaking changes kontrol |
| PWA manifest/service worker | Tarayıcı desteği değişiyor |
| Site anti-bot güncellendi | Yeni bypass stratejisi |

---

## Bug Önleme Protokolü (Kritik)

### Mimari kural: Önce Sözleşme, Sonra Kod
1. API endpoint → request/response şeması ÖNCE yaz
2. DB model → ORM class ÖNCE yaz
3. Sonra router ve scraper

### Test Katmanları
```
1. Tip kontrolü      → Python type hints + mypy (statik)
2. Birim test        → her router fonksiyonu izole test
3. Entegrasyon test  → gerçek DB + HTTP client
4. Canlı kanıt       → manuel inject veya curl ile doğrula
```

### Claude'a Özgü Hatalar (Kaçın)
- ❌ N+1 query — SQLAlchemy lazy load tuzağı → her ilişkide `selectinload` kullan
- ❌ Async/sync karışımı — FastAPI endpoint `async def`, DB call `await` OLMALI
- ❌ Import döngüsü — models.py ↔ routers birbirini import etmesin, `__init__.py` boş
- ❌ SQLite eşzamanlı yazma — tek kullanıcı ama yine de `aiosqlite` async driver şart
- ❌ CORS unutmak — frontend farklı port (Stitch dev server) → FastAPI'de CORS middleware

### Commit Kuralı
Her çalışan modül tamamlanınca commit + `docs/DEVAM.md` güncelle.
Yarım bırakma — ya tamamla ya `# TODO` ile işaretle.

---

## Genel Kurallar (Kuroshin stili)

- `docs/DEVAM.md` → tek-sayfa handoff, her bağımsız iş bitince güncelle
- Push: Lord açıkça `git push` isteyince — autonomous push yok
- Manuel test yasak — curl + log analiz ile test et
- Kanıtsız iş kapatma yasak — canlı kanıt olmadan tamamlandı deme
- Yeni MD oluşturma yasak — `docs/` altına ekle
- Ana MDler: `docs/DEVAM.md` (handoff) + `docs/YAPI.md` (mimari)

---

## Dosya Haritası

```
backend/
  __init__.py
  main.py          → FastAPI app (port 8099), CORS, 17 router kayıt, startup
  database.py      → AsyncEngine + AsyncSession factory (aiosqlite)
  models.py        → ORM: Content, Site, Episode, Tag, ContentTag
  config.py        → config.json loader helper
  config.json      → GERÇEK config: IGDB/MAL/TMDB creds, VAPID keys, download ayarları (.gitignore'da)
  push_manager.py  → Web Push (VAPID) gönderim yöneticisi
  reclassify.py    → Content tip/site yeniden sınıflandırma util
  requirements.txt / Dockerfile

  routers/         (17 router — main.py'de kayıtlı)
    content.py     → /api/content CRUD + /api/discover
    episodes.py    → /api/episodes + /api/check-updates + /api/updates
    sites.py       → /api/sites
    tags.py        → /api/tags
    sync.py        → /api/export + /api/import + /api/import/resolve
    settings.py    → /api/settings GET/POST (config.json)
    download.py    → /api/download (kuyruk/start/cancel/ws)          [FAZ-3]
    system.py      → /api/system (health/status/version/domains)     [FAZ-2]
    mal_sync.py    → /api/sync/mal (MAL list sync, OAuth callback)
    analytics.py   → /api/analytics (kullanım istatistikleri)
    analyze.py     → /api/analyze (intro/outro tespiti)
    translate.py   → /api/translate (manga çeviri)
    stream.py      → /api/stream (playback proxy)
    push.py        → /api/push (VAPID subs/notify)
    extension.py   → /api/extension (browser ext bridge)
    game.py        → /api/game CRUD
    game_download.py → /api/game-download (FitGirl/magnet)

  scraper/
    anilist.py     → AniList GraphQL (önce)
    mal.py         → MAL OAuth2 (fallback)
    igdb.py        → IGDB Twitch auth (oyunlar)
    mangadex.py    → MangaDex API (manga/manhwa)
    tmdb.py        → TMDB (film/dizi metadata + kapak)
    fitgirl.py     → FitGirl game repacks scraper
    parsers.py     → site parser'ları (chapter_check.py'nin yerini aldı)
    sources.py     → kaynak (source) kayıt defteri
    tag_extractor.py → tag çıkarıcı

  downloader/      → FAZ-3
    stream_finder.py → embed iframe URL çıkarma (TR anime/dizi siteleri)
    anime.py       → yt-dlp async wrapper
    manga.py       → Madara admin-ajax.php + mangadex-downloader
    manager.py     → kuyruk + WS progress
    integrity.py   → download bütünlük/doğrulama

  analyzer/        → intro/outro atlama (FAZ-4)
    chromaprint.py → audio fingerprint
    intro_detector.py / outro_detector.py

  services/        → paylaşılan servis katmanı
    db_updater.py  → idempotent site insert, domain migration
    domain_finder.py → DDG/Google search, alternatif site bulma
    domain_health.py → async domain health checker (CF detection)
    download_client.py → aria2/qbittorrent client
    tag_sync.py    → site tag senkronizasyonu
    test_runner.py → URL test suite, per-domain/per-type rapor
    url_patterns.py → UrlPattern, slug/domain extraction

  translator/      → FAZ-5 (sadece PC+GPU)
    engine.py      → manga-image-translator subprocess wrapper
    detect_gpu.py  → torch.cuda.is_available()

  scripts/         → tek-seferlik bakım/migration/sohbetXXX script'leri
    (fix_*.py, bulk_*.py, sohbet136–167_*.py, test_all_*.py ...)

  tools/           → DB/URL sağlık araçları
    content_health.py, url_ping.py

frontend/          → Stitch AI çıktısı + manuel modüller
  index.html       → ana SPA
  app.js           → ana uygulama (250KB)
  player.js        → video player + indirme modülü
  style.css        → özel stiller
  tailwind.css     → derlenmiş Tailwind
  pwa.js + sw.js + manifest.json → PWA/service worker
  i18n.js + locales/{en,tr}.json → i18n
  debug-logger.js → debug logger
  icons/           → app ikonları

extension/         → Chrome tarayıcı eklentisi
  manifest.json, background.js
  content/{crunchyroll,diziwatch,mangadex,tranimaci,tranimeizle,common}.js
  popup/{popup.html,popup.css,popup.js}
  icons/

tests/             → pytest entegrasyon/E2E suite
  conftest.py, pytest.ini
  test_backend_integrity.py, test_sohbet138–142_e2e.py
  test_detail*.py, test_home.py, test_hybrid.py ...

docs/
  DEVAM.md         → handoff (her commit sonrası güncelle)
  YAPI.md          → mimari, veri modeli, FAZ-3/4/5 detayları
  DESIGN.md        → Stitch AI prompt + tasarım kararları
  FEATURE_MAP.md   → tüm özellikler + FAZ checklist
  TEST_PLAN.md     → test planı
  ESLESMEYEN.md    → eşleşmeyen içerik checklist
  MANUAL_SITES.md  → manuel site eşleştirme referansı
  NETFLIX_ILHAM.md → Netflix UI ilham/rehber
  SOHBET-164/165_RAPORU.md → güncel sohbet raporları
  archive/         → tamamlanan/eski belgeler (SOHBET-130~163 raporları, JSON test çıktıları)

memory/
  kurowatch.db     → SQLite (.gitignore'da)
  backups/         → DB zip yedekleri

# Runtime/data (.gitignore'da):
#   logs/, downloads/, gallery-dl/, temp/, cookies/, covers/
```
