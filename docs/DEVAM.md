# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 21 Haziran 2026 (sohbet-58) · **Aktif sürüm:** v1.1.0 · **Son commit:** `faa4b38`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (21 Haz sohbet-58):
  - 676 içerik, backend faa4b38 — RESTART LAZIM (Bat [10]→[1])
  - Test: http://localhost:8099

SOHBET-58 YAPILANLARI:
  ✅ 31 manga/manhwa + 10 anime sitesi gerçek URL testi yapıldı
  ✅ stream_finder.py: protocol-relative (//) bug fix + pichive/aso1/anizmplayer tanıma
  ✅ manga.py: _MADARA_DOMAINS güncellendi (mangawow.com/org, ragnarscans.net vb. eklendi)
  ✅ content.py: site sıralaması — çalışan önce, en yüksek bölüm sayısı
  ✅ app.js: primarySite=best non-dead; Sites tab ölü→sona; "✓ Aktif" badge
  ✅ scripts/enrich_fallback_sites.py YENİ: anime (tranimeizle slug→turkanime/anizm) + manga oto eşleştirme

ÇALIŞAN SİTELER (21 Haz test):
  ANİME/DİZİ: tranimaci.com ✅ | hdfilmcehennemi.nl ✅ | turkanime.tv 🟡 | dizibox.live 🟡 | anizm.net ✅ | diziwatch.ac 🟡
  MANGA: mangawow.com ✅ | mangawow.org ✅ | ragnarscans.com ✅ | ragnarscans.net ✅ | hayalistic.com.tr ✅ | merlintoon.com ✅
  ÖLÜLER: tranimeizle.co (CF), mangaokutr.com (offline), mangatr.net (bot), ruyamanga.net (403)

SIRADAKİ GÖREVLER:
  [1] Backend restart: Bat [10] → [1] (faa4b38 aktif etmek için)
  [2] title_tr test: Düzenle modal → "Türkçe Başlık" → kaydet → kart/detay güncellenmeli
  [3] enrich_fallback_sites.py full run: python3 scripts/enrich_fallback_sites.py --type all
      (429 anime + 172 manga/manhwa için fallback URL ekler, dry-run önce test et)
  [4] audit_all_media.py: --no-mark kaldır → gerçek DB güncelle
  [5] Manga çeviri "Düzelt" butonu (FAZ-5 kalan)

⚠️ ÖNEMLİ:
  - enrich_fallback_sites.py: dry-run ile önce test et: --dry-run --limit 20
  - Slug eşleşme oranı: ~%30-50 (tranimeizle slug turkanime'de aynı değilse bulamıyor)
  - anizm.net arama sayfası 403 — direkt slug tahmini kullanılıyor
  - diziwatch.ac embed: four.pichive.online (CF korumalı, yt-dlp başarısız olabilir)
  - DB: episode tablosu (çoğulsuz), kolon: number
  - Backend restart ŞART (Bat [10]→[1])
```

---

## 📦 Proje Yapısı

```
C:\Kuroshin\kurowatch\
  backend/
    main.py              → FastAPI port 8099
    database.py          → migration: title_tr TEXT eklendi (acc5467)
    models.py            → Content.title_tr: Optional[str] eklendi
    routers/
      content.py         → _serialize: title_tr dahil; ContentPatch: title_tr kabul eder
      episodes.py        → bölüm sync
      sites.py / tags.py / sync.py / settings.py / extension.py
    downloader/
      stream_finder.py   → networkidle + JS iframe + 15s + playwright-stealth (4a8d40f)
      anime.py           → yt-dlp wrapper
      manga.py           → Madara + gallery-dl
  frontend/
    index.html           → Edit modal: "Türkçe Başlık" input eklendi
    app.js               → kart+detay: title_tr || title; Edit modal fill+save
  cookies/               → BOŞ (tranimeizle_cookies.txt buraya gelecek)
  tools/
    crawlee_test_tranimeizle.js  → geçici test scripti
    test_tranimeizle.js          → geçici test scripti
```

---

## 🔑 Önemli Notlar

- **title_tr gösterimi:** kart h3 + liste span + detail-title → `title_tr || title`
- **Edit modal:** id=`edit-form-title-tr` input, patchBody'e `title_tr` ekleniyor
- **Tailwind:** JS'de `el.style.X = Y` kullan, dynamic class ÇALIŞMAZ
- **Backend restart:** Bat [10]→[1] (kod değişince mutlaka)
- **tranimeizle.co:** cookies olmadan bypass yok (Playwright+Crawlee+stealth hepsi başarısız)

---

## 📌 Commit Geçmişi (Önemli)

| Commit | Ne |
|--------|----|
| `acc5467` | title_tr: DB migration + Edit modal + kart/detay gösterimi |
| `4a8d40f` | stream_finder: networkidle + JS iframe + 15s + playwright-stealth |
| `7cc75a1` | docs: DEVAM.md sohbet-56 |
| `5c9d39c` | Anime indirme Playwright + Referer fix |
| `1cacc29` | Madara manga lazy-load bug fix |
