# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 20 Haziran 2026 (sohbet-52) · **Aktif sürüm:** v1.0.0 · **Son commit:** `82af85d`

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

SIRADAKİ BÜYÜK GÖREVLER (öncelik sırası — Lord direktifi 20 Haz):

[A] SITE SIRALAMA — Chapter count bazlı (detail kartı)
    - Detail kartında siteler gösterilirken: en fazla bölüm olan site EN ÜSTTE
    - Her sitenin yanında bölüm sayısı görünsün (örn: "asurascans [120]", "mangaokutr [80]")
    - DB: Site.latest_known_ep field zaten var → bunu kullan
    - Sıralama: ORDER BY latest_known_ep DESC (null en alta)
    - Dosyalar: frontend/app.js renderDetailSites()

[B] IN-DETAIL OKUMA/İZLEME BUTONU (popup window)
    - Bölümler tab'ında her bölüm satırının yanına "▶ Oku/İzle" butonu ekle
    - Butona basınca yeni küçük pencere (window.open veya full-screen overlay iframe) ile sitenin
      bölüm URL'ini aç — kullanıcı ayrı tab'a gitmeden kendi içinde izleyebilsin
    - Overlay iframe tercih: z-index:9999, close butonu sağ üstte, ESC ile kapat
    - Dosyalar: frontend/index.html (#read-overlay div ekle), frontend/app.js (_epHtml butonu)

[C] ARKA PLANDA İNDİRME + POPUP
    - Kullanıcı bir bölümü izlerken/okurken → bölümün %50'sine gelince popup göster:
      "Sıradaki bölüm arka planda indiriliyor..."
    - Popup 4sn sonra kapanır (toast notification)
    - Arka planda: GET /api/download/{content_id}/{ep+1} tetiklenir (sessiz)
    - Eğer sonraki bölüm zaten indirilmişse popup çıkmaz
    - Dosyalar: frontend/player.js (progress izleme hook), frontend/app.js (toast util)

[D] ENRICH SITE URLS — yeni siteler + 76 site-siz içerik
    - dizibox.live (Türk dizi + bazı anime): https://www.dizibox.live/{slug}-izle/
    - hdfilmcehennemi.nl (Türk film): https://www.hdfilmcehennemi.nl/{slug}-izle/
    - merlintoon.com (anime/cartoon): URL pattern test edilmeli
    - Hedef: 76 site-siz içeriğin bir kısmına URL ekle
    - Dosyalar: scripts/enrich_site_urls.py

[E] DEAD SİTE YÖNETİMİ (detail kartı)
    - Siteler gösterilirken: erişilemeyen/ölü siteler gizlenmez, gösterilir
    - Ama yanına "⚠️ Erişilemiyor" etiketi koymak için periyodik HTTP HEAD kontrol
    - audit_all_media.py: 676 içerik cover/tag/URL/download durum raporu

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
