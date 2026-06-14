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
- `backend/scraper/chapter_check.py` → belirli siteleri tara
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
  main.py          → FastAPI app (port 8099), CORS, router kayıt, startup
  database.py      → AsyncEngine + AsyncSession factory (aiosqlite)
  models.py        → ORM: Content, Site, Episode, Tag, ContentTag
                     (TrackingSession → MVP DIŞI, FAZ-2+)
  routers/
    content.py     → /api/content CRUD + /api/discover
    episodes.py    → /api/episodes + /api/check-updates + /api/updates
    sites.py       → /api/sites
    tags.py        → /api/tags
    sync.py        → /api/export + /api/import + /api/import/resolve
    settings.py    → /api/settings GET/POST (config.json)
  scraper/
    anilist.py     → AniList GraphQL (önce)
    mal.py         → MAL OAuth2 (fallback, FAZ-2)
    igdb.py        → IGDB Twitch auth (oyunlar, FAZ-2)
    chapter_check.py → site scraper (son çare)
  downloader/      → FAZ-3
    stream_finder.py → embed iframe URL çıkarma (TR anime/dizi siteleri)
    anime.py       → yt-dlp async wrapper
    manga.py       → Madara admin-ajax.php + mangadex-downloader
    manager.py     → kuyruk + WS progress
  translator/      → FAZ-5 (sadece PC+GPU)
    engine.py      → manga-image-translator subprocess wrapper
    detect_gpu.py  → torch.cuda.is_available()
frontend/          → Stitch AI çıktısı + manuel app.js
docs/
  DEVAM.md         → handoff (her commit sonrası güncelle)
  YAPI.md          → mimari, veri modeli, FAZ-3/5 detayları
  DESIGN.md        → Stitch AI prompt (tamamlandı) + tasarım kararları
  FEATURE_MAP.md   → tüm özellikler + FAZ checklist
memory/
  kurowatch.db     → SQLite (.gitignore'da)
config.json        → IGDB creds + VAPID keys + download ayarları (.gitignore'da)
```
