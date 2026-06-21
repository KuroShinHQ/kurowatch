# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 21 Haziran 2026 (sohbet-59) · **Aktif sürüm:** v1.1.0 · **Son commit:** `aa3c10f`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (21 Haz sohbet-59):
  - 676 içerik, backend aa3c10f aktif — restart GEREKMİYOR
  - Test: http://localhost:8099
  - 151 fallback URL DB'ye eklendi (enrich çalıştı ✅)
  - 608 ölü site is_dead=True işaretlendi (audit çalıştı ✅)

SOHBET-59 YAPILANLARI:
  ✅ enrich_fallback_sites.py çalıştı: 101 anime(turkanime) + 45 manga + 5 manhwa → DB'ye eklendi
  ✅ audit_all_media.py: 608 ölü site işaretlendi
  ✅ manga.py: reading-content hard-check kaldırıldı → ragnarscans.com 25 sayfa OK ✅
  ✅ stream_finder.py: _is_embed JS/CSS filtresi eklendi, /ifr.html pattern eklendi
  ✅ docs/MANUAL_SITES.md: 383 anime + 71 manga + 29 manhwa eşleşmeyen liste
  ✅ anizm.net indirme ÇALIŞIYOR: stream_finder → m3u8 → yt-dlp (test OK)
  ✅ mangawow.com indirme ÇALIŞIYOR: 12 sayfa test OK
  ✅ ragnarscans.com indirme ÇALIŞIYOR: 25 sayfa test OK
  🔄 anizm.net tam indirme testi arka planda (bh0wii1ej) — sonuç bekleniyor

İNDİRME DURUM HARİTASI:
  ANİME:
    anizm.net    ✅ stream_finder m3u8 buluyor → yt-dlp OK (tam test sonucu bekle)
    tranimaci.com ✅ Playwright CDN MP4 (önceden çalışıyor)
    turkanime.tv  ❌ CF bot koruması — embed URL session-specific, headless'ta geçersiz
    dizibox.live  🟡 test edilmedi
    hdfilmcehennemi.nl 🟡 test edilmedi
  MANGA:
    mangawow.com    ✅ 12 sayfa OK
    ragnarscans.com ✅ 25 sayfa OK (reading-content fix sonrası)
    ragnarscans.net ✅ aynı fix geçerli
    hayalistic.com.tr 🟡 test edilmedi

SIRADAKİ GÖREVLER:
  [1] anizm.net indirme sonucunu doğrula (bh0wii1ej task tamamlandıysa)
  [2] turkanime.tv için alternatif: turkanime.tv embed'i → IndexIcerik AJAX → iframe yakala
      → stream_finder'a popup+sunucu-click ekle (popup: button.site-popup-close)
  [3] hayalistic.com.tr + dizibox.live + hdfilmcehennemi.nl indirme testleri
  [4] title_tr UI testi: Düzenle modal → "Türkçe Başlık" → kaydet → kart/detay
  [5] Manga çeviri "Düzelt" butonu (FAZ-5 kalan)

⚠️ ÖNEMLİ:
  - turkanime.tv: popup selector = button.site-popup-close | sunucu btn = button.btn.btn-sm.btn-default
  - turkanime.tv: IndexIcerik('ajax/videosec&b=...') AJAX → embed iframe src yakala
  - anizmplayer.com m3u8 → Referer: anizm.net/ şart (yt-dlp --add-header)
  - manga.py: reading-content check kaldırıldı, fallback img extraction aktif
  - DB: episode tablosu (çoğulsuz), kolon: number
  - MANUAL_SITES.md: 383+71+29 eşleşmeyen içerik → Lord manuel URL ekleyecek
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
