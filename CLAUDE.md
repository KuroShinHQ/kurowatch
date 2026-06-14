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
  models.py        → ORM: Content, Site, Episode, Tag, ContentTag, TrackingSession
  routers/
    content.py     → /api/content CRUD
    tracking.py    → /api/track süre
    sites.py       → /api/sites
    tags.py        → /api/tags
    episodes.py    → /api/episodes
    sync.py        → /api/export + /api/import
  scraper/
    anilist.py     → AniList GraphQL (önce)
    mal.py         → MAL OAuth2 (fallback)
    igdb.py        → IGDB Twitch auth (oyunlar)
    chapter_check.py → site scraper (son çare)
frontend/          → Stitch AI çıktısı (henüz boş)
docs/
  DEVAM.md         → handoff
  YAPI.md          → mimari + site listesi
  DESIGN.md        → Stitch AI prompt (hazırlanacak)
memory/
  kurowatch.db     → SQLite (.gitignore'da)
```
