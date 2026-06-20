# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 21 Haziran 2026 (sohbet-56) · **Aktif sürüm:** v1.1.0 · **Son commit:** `4a8d40f`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (21 Haz sohbet-56):
  - 676 içerik, backend 4a8d40f — RESTART LAZIM
  - Test: http://localhost:8099

SOHBET-56 YAPILANLARI:
  ✅ stream_finder: networkidle + JS iframe + 15s bekleme + playwright-stealth (4a8d40f)
  ✅ tranimeizle.co "Bot Kontrol" CAPTCHA teşhis edildi:
     - Görsel CAPTCHA (puzzle) — headless bypass yok
     - Çözüm: cookies/tranimeizle_cookies.txt (Netscape format) şart
     - cookies dizini şu an BOŞ: C:\Kuroshin\kurowatch\cookies\

AKTİF SORUNLAR:
  ❌ tranimeizle.co indirme: CAPTCHA engeli — cookies gerekli
     - Lord, Chrome'da CAPTCHA çöz → Cookie-Editor extension → Netscape export
     - Kaydet: C:\Kuroshin\kurowatch\cookies\tranimeizle_cookies.txt
  ❌ tranimeizle.io 404: Bölüm URL girilmeli (Siteler sekmesi)
  ❌ Anime Türkçe isim yok: title_tr alanı DB'de yok

SIRADAKİ GÖREVLER (öncelik sırasıyla):
  [A] cookies.txt varsa → tranimeizle.co tekrar test
  [B] mangaokutr.com testi → 67 içerik, Madara tema, manga.py var
  [C] title_tr alanı: models.py migration + Edit modal + save API
  [D] Manga çeviri "Düzelt" butonu (FAZ-5 kalan)

⚠️ ÖNEMLİ:
  - playwright-stealth v2.0.3: Stealth().apply_stealth_async(page) — stealth_async DEĞİL
  - DB tablo: episode (çoğulsuz), kolon: number (episode_number değil)
  - Backend restart ŞART: Bat [10] → [1]
  - tranimaci.com: ÇALIŞIYOR (Playwright 10sn + Referer)

BAŞLATMA:
  Bat [10] → [1] (chancellor restart — 4a8d40f değişiklikleri aktif)
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
  cookies/               → BOŞ — tranimeizle_cookies.txt buraya gelecek
  memory/
    kurowatch.db         → SQLite (gitignore)
  config.json            → API keys (gitignore)
  docs/
    DEVAM.md             → bu dosya
    TEST_PLAN.md         → sistematik test listesi
    FEATURE_MAP.md       → tüm özellik envanteri
    YAPI.md              → mimari kararlar
  debug_stream.py        → geçici teşhis aracı (silinebilir)
  check_botpage.py       → geçici teşhis aracı (silinebilir)
  check_db.py            → geçici teşhis aracı (silinebilir)
```

---

## 🔑 Önemli Notlar

- **Tailwind kuralı:** JS'de `el.style.X = Y` kullan, dynamic class ÇALIŞMAZ (CDN build)
- **Backend restart şart:** Kod değişince chancellor cache tuttuğu için mutlaka restart
- **WSL'den başlatma:** `setsid` ile + bat [10]→[1] en güvenilir
- **Cover upload:** `POST /api/content/{id}/cover` (multipart) + `/covers/` static mount
- **Extension capture:** `POST /api/extension/capture` → AniList eşleştir → DB
- **tranimeizle.co CAPTCHA:** cookies/tranimeizle_cookies.txt (Netscape) olmadan indirme yok
- **DB tablo:** `episode` (çoğulsuz); kolon `number` (episode_number değil)

---

## 📌 Commit Geçmişi (Önemli)

| Commit | Ne |
|--------|----|
| `4a8d40f` | stream_finder: networkidle + JS iframe + 15s + playwright-stealth |
| `b28f10d` | anime.py: hata mesajları iyileştirildi |
| `1def47a` | stream_finder: Crunchyroll/VRV iframe filtresi |
| `e1bb754` | "Bölümleri Güncelle" butonu |
| `5c9d39c` | Anime indirme Playwright + Referer fix |
| `1cacc29` | Madara manga lazy-load bug fix |
