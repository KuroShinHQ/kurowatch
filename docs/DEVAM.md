# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 20 Haziran 2026 (sohbet-47) · **Aktif sürüm:** v1.0.0 · **Son commit:** `b85c251`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md + TEST_PLAN.md oku. Özet:

MEVCUT DURUM (20 Haz sohbet-47):
  - 676 içerik, 670 cover (%99) — bulk_cover_fetch.py ile düzeltildi
  - Backend: Bat [10] → [1] ile başlatılır (start /b wsl chancellor yöntemi)
  - Test: http://localhost:8099/api/content

AKTİF ÇALIŞMA: Sistematik bug testi
  - Test metodolojisi: Claude test talimatı verir → Lord KuroWatch'ta dener → feedback
  - Tüm özellikler sırayla test edilecek (TEST_PLAN.md takip et)
  - Sonraki test: TEST_PLAN.md'deki ilk ❌ veya ❓ işaretli test

BAŞLATMA:
  Bat [10] → [1] (chancellor yöntemi)
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
