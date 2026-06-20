# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 20 Haziran 2026 (sohbet-54) · **Aktif sürüm:** v1.1.0 · **Son commit:** `c0b656d`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (20 Haz sohbet-54):
  - 676 içerik, 670 cover (%99), 6 cover-sız (Türk yapımı)
  - external_score: 567/676 (%83) dolu
  - Backend: port 8099 — RESTART LAZIM (c0b656d değişikliği uygulanmadı)
  - Test: http://localhost:8099

SOHBET-54 YAPILANLARI:
  ✅ anime.py + episodes.py + frontend (app.js, index.html, player.js) refactor (c0b656d)
     - AniList bölüm sync (13 bölüm türetme), "İzle — Bölüm 1" shortcut
     - Floating indicator ile sessiz indirme

AKTİF SORUNLAR (çözüm bekliyor):
  ❌ tranimeizle.io 404: Siteler sekmesine ana page girildi, bölüm URL girilmeli
     - Doğru format: /anime/<slug>/<N>-bolum veya /<slug>-<N>-bolum-izle
     - Lord'un 1. bölüm sayfasını açıp URL'yi Siteler sekmesine girmesi gerekiyor
  ❌ yt-dlp hataları: ?su=... Crunchyroll URL → premium gerekli + cookies yok
     - Çözüm: Settings → Cookies → tranimeizle için cookie ekle
  ❌ Anime Türkçe isim yok: AniList yalnızca English + Romaji döndürüyor
     - title_tr alanı DB'de YOK → migration + Edit modal + AniList sync güncelleme gerekli

SIRADAKİ GÖREVLER (öncelik sırasıyla):
  [A] title_tr alanı: models.py migration + Edit modal + save API (Türkçe isim)
  [B] tranimeizle bölüm URL şablonu çöz (Lord URL bulup Siteler'e girsin → test)
  [C] audit_all_media.py tam koşu (--no-mark kaldır, gerçek DB güncelle)
  [D] Manga çeviri "Düzelt" butonu (FAZ-5 kalan)

⚠️ ÖNEMLİ:
  - Manga siteleri WSL curl ile 000 verir AMA Python httpx ile OK!
  - Tailwind: JS'de inline style kullan, dynamic class ÇALIŞMAZ
  - Backend restart ŞART: Bat [10] → [1]

BAŞLATMA:
  Bat [10] → [1] (chancellor restart — c0b656d değişiklikleri aktif etmek için)
  Test URL: http://localhost:8099
```

---

## 📦 Proje Yapısı

```
C:\Kuroshin\kurowatch\
  backend/
    main.py              → FastAPI port 8099, CORS, router kayıt
    database.py          → AsyncEngine + aiosqlite
    models.py            → Content, Site, Episode, Tag, ContentTag ORM
    routers/
      content.py         → /api/content CRUD + /api/discover + /api/content/enrich-covers
      episodes.py        → /api/episodes + /api/check-updates + /api/updates
      sites.py           → /api/sites
      tags.py            → /api/tags
      sync.py            → /api/export + /api/import + /api/import/resolve
      settings.py        → /api/settings
      extension.py       → /api/extension (capture/status/sites)
    scraper/
      anilist.py         → AniList GraphQL (ana kaynak)
      mal.py             → MAL OAuth2 (fallback)
      igdb.py            → IGDB Twitch (oyunlar)
      chapter_check.py   → site scraper
    downloader/          → FAZ-3 (yt-dlp + gallery-dl + Playwright)
    translator/          → FAZ-5 (manga-image-translator + GPU detect)
  frontend/
    index.html           → SPA shell, tüm ekranlar
    app.js               → tüm UI mantığı (renderHome, openDetail, vb.)
    player.js            → video/manga oynatıcı + FAZ-4 outro + FAZ-5 çeviri
    style.css            → global stiller (Tailwind build + custom)
    pwa.js               → PWA push notification (FAZ-7a)
  extension/             → Chrome/Firefox Manifest V3 extension
  scripts/
    bulk_cover_fetch.py  → AniList+Jikan zinciri, direkt SQLite (backend yok)
    enrich_anilist.py    → eski cover zenginleştirme (bulk_cover_fetch yeni)
  memory/
    kurowatch.db         → SQLite (gitignore)
  config.json            → API keys (gitignore)
  docs/
    DEVAM.md             → bu dosya
    TEST_PLAN.md         → sistematik test listesi
    FEATURE_MAP.md       → tüm özellik envanteri
    YAPI.md              → mimari kararlar
```

---

## 🔑 Önemli Notlar

- **Tailwind kuralı:** JS'de `el.style.X = Y` kullan, dynamic class ÇALIŞMAZ (CDN build)
- **Backend restart şart:** Kod değişince chancellor cache tuttuğu için mutlaka restart
- **WSL'den başlatma:** `setsid` ile + bat [10]→[1] en güvenilir
- **Cover upload:** `POST /api/content/{id}/cover` (multipart) + `/covers/` static mount
- **Extension capture:** `POST /api/extension/capture` → AniList eşleştir → DB

---

## 📌 Commit Geçmişi (Önemli)

| Commit | Ne |
|--------|----|
| `b85c251` | v0.3.1 bug fix paketi (503, cover zenginleştir, yıldız, genre, timeout) |
| `2c62fb5` | Home kart cover onerror HTML injection fix |
| `a9fbd24` | Extension capture: cover+genres AniList, 4 katmanlı fuzzy |
| `dd4bed8` | Video/manga overflow fix |
| `5c9d39c` | Anime indirme Playwright + Referer fix |
| `1cacc29` | Madara manga lazy-load bug fix |
