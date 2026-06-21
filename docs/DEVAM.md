# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 21 Haziran 2026 (sohbet-60) · **Aktif sürüm:** v1.1.0 · **Son commit:** `1dd682a`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (21 Haz sohbet-60):
  - 676 içerik, backend 1dd682a aktif — restart GEREKMİYOR
  - Test: http://localhost:8099

SOHBET-60 YAPILANLARI:
  ✅ anizm.net tam indirme: 422.5 MB MP4 (sousou-no-frieren ep1)
  ✅ turkanime.tv indirme TAMAMLANDI: 885.6 MB (commit 1dd682a)
     - FORCE_PLAYWRIGHT + popup/sunucu-click + 32sn bekleme
     - on_request MP4 header yakalama → yt-dlp CF bypass (sec-ch-ua vb.)
  ✅ hayalistic.com.tr manga: ch0149 indirildi
  ✅ title_tr: API+frontend kod doğrulandı
  ✅ Manga "Düzelt" PUT endpoint mevcut (translate.py:178)
  ⏸️ dizibox.live: 429 rate limit (daha sonra dene)

İNDİRME DURUM HARİTASI:
  ANİME:
    anizm.net    ✅ 422.5 MB OK
    tranimaci.com ✅ Playwright CDN MP4
    turkanime.tv  ✅ Playwright 32sn + header capture → alucard.click 885MB
    dizibox.live  ⏸️ 429 rate limit
    hdfilmcehennemi.nl 🟡 test edilmedi
  MANGA:
    mangawow.com    ✅ 12 sayfa OK
    ragnarscans.com ✅ 25 sayfa OK
    ragnarscans.net ✅ aynı fix geçerli
    hayalistic.com.tr ✅ ch0149 OK

SIRADAKİ GÖREVLER:
  [1] dizibox.live testi (rate limit geçince)
  [2] hdfilmcehennemi.nl indirme testi
  [3] PCT:0 sorunu — alucard.click progress parse düzelt
  [4] title_tr null temizleme fix (exclude_none=True → exclude_unset=True)
  [5] MANUAL_SITES.md'den seçilen URL'leri DB'ye ekle
⚠️ ÖNEMLİ:
  - turkanime.tv: on_request MP4 header → _SESSION_HEADERS → yt-dlp --add-header
  - turkanime.tv: alucard.click 885MB (720p seçilse de 1080p geliyor, tek kalite)
  - PCT:0 sorunu: yt-dlp alucard.click indirmesinde progress satırı parse edilemiyor
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
