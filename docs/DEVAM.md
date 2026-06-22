# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 22 Haziran 2026 (sohbet-69) · **Aktif sürüm:** v1.1.0 · **Son commit:** `a35d399`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (22 Haz sohbet-69):
  - 676 içerik, backend a35d399 aktif (WSL'de çalışıyor, PID 644 uvicorn port 8099)
  - ⚠️ SORUN: localhost:8099 Windows tarayıcıdan ERR_FAILED — port forward çalışmıyor
    (WSL mirrored mode aktif; Kuroshin.bat portproxy eklenirse çözülür)
  - Çalışan kaynağı olan: ~280 içerik
  - Test: http://localhost:8099 (önce backend erişim sorununu çöz!)

SOHBET-69 YAPILANLARI:
  ✅ DESIGN.md + FEATURE_MAP.md mevcut kodla uyumlu güncellendi (a35d399)
     nav/settings/detail/archive/downloads ekranları dokümante edildi
  ❌ T-06 test edilemedi: localhost:8099 ulaşılamıyor (port forwarding sorunu)

SOHBET-70 SIRASI:
  [1] ÖNCE: localhost:8099 erişim sorununu çöz
      → Kuroshin.bat KUROWATCH bölümüne portproxy 8099 ekle (admin gerektirmez mı?) VEYA
      → .wslconfig'de networkingMode=mirrored zaten var, sorun başka olabilir
      → WSL'den curl http://localhost:8099 çalışıyor ✅ — sorun Windows→WSL yönünde
  [2] TEST_PLAN.md T-06 testi: "Herhangi karta tıkla → Detail ekranı açılır mı?"
  [3] T-07..T-38 devam

⚠️ ÖNEMLİ:

⚠️ ÖNEMLİ:
  - PORT SORUNU: networkingMode=mirrored var ama 8099 Windows'a gelmiyor
    Bat'ta portproxy 8099→WSL IP'si eklenebilir (Kuroshin.bat :KUROWATCH bölümü)
  - ESLESMEYEN.md: docs/ESLESMEYEN.md — Lord URL bildirir, Claude DB'ye ekler
  - enrich_turkanime.py: SQLite'a direkt yazar (API değil — WSL←→Windows port sorunu)
  - ta_index.json + ta_romaji_cache.json → scripts/ (yeniden çalıştırmaya gerek yok)
  - dizibox.so + hdfilmcehennemi.nl: CF bypass yok, cookies.txt şart (askıya)
  - anizmplayer.com m3u8 → Referer: anizm.net/ şart
  - DB: episode tablosu (çoğulsuz), kolon: number
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
- **Backend restart:** Bat menüsünden (kod değişince MUTLAKA); `wsl -e bash` ile background başlatma güvenilmez
- **tranimeizle.co:** cookies olmadan bypass yok (Playwright+Crawlee+stealth hepsi başarısız)

---

## ⚠️ HATA YAPMA LİSTESİ (Sohbet-60'tan öğrenildi)

### WSL / Python ortamı
- **Playwright WSL'de SADECE venv'de çalışır:** `/root/kuroshin/venv/bin/activate` kaynak almadan test etme — `python3`, `python3.11` bulamaz
- **Test komutu şablonu:** `wsl -e bash -c "source /root/kuroshin/venv/bin/activate && cd /mnt/c/Kuroshin/kurowatch && python -c '...'"` — eksikse import hatası alırsın
- **`wsl -e /bin/bash -c`** → hata verir (Git bash çakışması); her zaman `wsl -e bash -c` kullan
- **WSL'de background process:** `nohup ... &` ve `setsid ... &` PowerShell/Bash üzerinden çalışmaz — Lord'dan bat menüsü restart iste

### Backend geliştirme
- **`model_dump(exclude_none=True)`** → None değer gönderince field güncellenmez; temizleme için `exclude_unset=True` gerekir
- **Backend kodu değişince HEMEN restart:** `stream_finder.py`, `anime.py` vb. değişince Python `sys.modules` cache eski kodu tutar — eski hatayla test etmiş olursun

### Playwright / stream_finder
- **`on_request` callback'i:** Playwright isteği GÖNDERİR ama yanıtın 200 olduğunu garanti etmez; URL'yi bulsan da sunucu reddedebilir
- **turkanime.tv bekleme:** iframe (media.aso1.net → alucard.click) 25-30sn içinde MP4 isteği yapar; 12sn yetmez, 32sn gerekli
- **`found_embed[0]` tuzağı:** İlk yakalanan URL en iyi URL değil; m3u8 → .mp4 → diğer sırayla önceliklendir
- **CF korumalı direkt MP4:** `--impersonate` ve `--extractor-args "generic:impersonate"` işe YARAMAZ; asıl çözüm Playwright'ın kendi request header'larını yakalayıp yt-dlp'ye `--add-header` ile geçirmek

### yt-dlp
- **Cloudflare 403 teşhis:** `HTTP Error 403` + `Server: cloudflare` → CF clearance sorunu; `HTTP Error 429` → rate limit (bekle, tekrar dene)
- **`--add-header "key:value"`** → yt-dlp ilk `:` karakterinde böler, değer içinde `:` olabilir (sec-ch-ua gibi) — sorun yok
- **`range: bytes=0-` header'ı** yt-dlp'ye geçirme — skip et, yt-dlp kendi range header'ını yönetir
- **alucard.click PCT:0 sorunu:** yt-dlp progress satırı parse edilemiyor (muhtemelen format farklı); indirme bitince PCT:100 geliyor, indirme çalışıyor

### Test sırası
- Önce `wsl` ile direkt Python scripti test et (venv'le), sonra API üzerinden test et — böylece hangi katmanda hata olduğu netleşir
- Job "downloading" durumuna geçtiyse başarı; `/downloads/` klasörüne `.part` dosyası büyüyorsa gerçekten iniyor

---

## 📌 Commit Geçmişi (Önemli)

| Commit | Ne |
|--------|----|
| `1dd682a` | turkanime.tv: Playwright header capture + CF bypass (885MB test OK) |
| `acc5467` | title_tr: DB migration + Edit modal + kart/detay gösterimi |
| `4a8d40f` | stream_finder: networkidle + JS iframe + 15s + playwright-stealth |
| `5c9d39c` | Anime indirme Playwright + Referer fix |
| `1cacc29` | Madara manga lazy-load bug fix |
