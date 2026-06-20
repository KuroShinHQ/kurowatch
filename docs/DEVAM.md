# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 20 Haziran 2026 (sohbet-52b) · **Aktif sürüm:** v1.0.0 · **Son commit:** `f6e2df2`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (20 Haz sohbet-52):
  - 676 içerik, 670 cover (%99)
  - external_score: 567/676 (%83) dolu (AniList/Jikan)
  - manga.py: 3 yeni Madara site eklendi (ruyamanga.com/net, asurascans.com.tr) commit 82af85d
  - Backend: Bat [10] → [1] ile başlatılır (start /b wsl chancellor yöntemi)
  - Test: http://localhost:8099

SOHBET-52 YAPILANLARI:
  ✅ manga.py _MADARA_DOMAINS → 3 yeni site (httpx testi ile doğrulandı)
     - ruyamanga.com: chapter indir PASS (HTTP 200, 17 wp-manga-chapter-img)
     - ruyamanga.net: Madara onaylı
     - asurascans.com.tr: Madara onaylı, chapter 403 (bot koruması riski)
     - Dead atlanılar: mangaokutr.com, mangatr.net, uzaymanga.com, mangasehri.net, merlinscans.com

SIRADAKİ GÖREVLER (öncelik sırası — 20 Haz güncel):

[1] ✅ TAMAMLANDI — manga.py Madara domains (commit 82af85d)

[2] Site sıralama (chapter count bazlı) — detail kartı
    - Siteler: en fazla bölüm olan EN ÜSTTE, yanında sayı (örn: "asurascans [120]")
    - DB: Site.latest_known_ep zaten var → ORDER BY DESC (null en alta)
    - Dosya: frontend/app.js renderDetailSites()

[3] In-detail okuma/izleme butonu (overlay iframe)
    - Bölüm satırına "▶ Oku/İzle" butonu → tam ekran overlay iframe açılır
    - ESC / X ile kapat, z-index:9999
    - Dosyalar: frontend/index.html (#read-overlay), frontend/app.js (_epHtml)

[4] Arka planda indirme + popup
    - Bölümün %50'sine gelince toast: "Sıradaki bölüm arka planda indiriliyor..."
    - Toast 4sn kapanır; zaten indirilmişse çıkmaz
    - Backend: GET /api/download/{id}/{ep+1} sessiz tetiklenir
    - Dosyalar: frontend/player.js (progress hook), frontend/app.js (toast util)

[5] enrich_site_urls.py — yeni siteler + 76 site-siz içerik
    - dizibox.live: https://www.dizibox.live/{slug}-izle/
    - hdfilmcehennemi.nl: https://www.hdfilmcehennemi.nl/{slug}-izle/
    - merlintoon.com: URL pattern önce test et

[6] stream_finder.py → dizibox.live + hdfilmcehennemi embed desteği

[7] audit_all_media.py + dead site yönetimi
    - 676 içerik: cover/tag/URL/download durum raporu (httpx HEAD)
    - Kırık URL tespiti → detail kartında ⚠️ etiketi

⚠️ ÖNEMLİ:
  - Manga siteleri WSL curl ile 000 verir AMA Python httpx ile OK!
  - Her test ve erişim için httpx kullan, curl kullanma
  - Tailwind: JS'de inline style kullan, dynamic class ÇALIŞMAZ

BAŞLATMA:
  Bat [10] → [1] (chancellor yöntemi) — restart sonrası F5 yeterli
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
