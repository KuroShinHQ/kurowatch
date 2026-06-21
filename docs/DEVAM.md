# 🚀 KuroWatch DEVAM — Yeni Sohbet Brief
**Son güncelleme:** 21 Haziran 2026 (sohbet-61b) · **Aktif sürüm:** v1.1.0 · **Son commit:** `7d920ea`

> Yeni Claude'a tek-sayfa devamlılık. Bu dosyayı oku, sonra TEST_PLAN.md'e bak.

---

## ⚡ YENİ SOHBET BAŞLANGIÇ PROMPT

```
KuroWatch DEVAM.md oku. Özet:

MEVCUT DURUM (21 Haz sohbet-61b):
  - 676 içerik, backend RESTART GEREKİYOR (7d920ea — bat menüsü)
  - Test: http://localhost:8099

SOHBET-61 YAPILANLARI:
  ✅ PCT:0 fix: anime.py chunk-based stdout — yt-dlp \r progress artık güncellenir
  ✅ title_tr null fix: content.py exclude_unset — PATCH null ile DB'den siler
  ✅ dizibox.so stream_finder'a eklendi; CF confirmed → askıya
  ✅ hdfilmcehennemi.nl play selector .play-that-video; CF confirmed → askıya
  🔍 turkanime eşleştirme araştırması TAMAMLANDI:
     - slug tahmin yöntemi çalışmıyor (İngilizce vs Japonca romaji)
     - turkanime.tv/sitemap/tv/sitemap1-3.xml.gz bulundu (TÜM animeler burada)
     - build_ta_index.py YAZILDI → sitemap'tan {slug→ep1_url} JSON üretir
     - Sonraki adım: index'i oluştur → AniList romaji ile eşleştir → DB'ye ekle

SOHBET-62 SIRASI:
  [1] backend restart (bat menüsü — 7d920ea kodu aktif değil)
  [2] python3 scripts/build_ta_index.py
        → scripts/ta_index.json oluşturur (~binlerce slug)
  [3] match_ta.py yaz: ta_index × AniList romaji → 329 anime eşleştir → DB ekle
        Mantık: get_detail(anilist_id) → romaji → slug → ta_index lookup
  [4] PCT + title_tr null fix doğrula (frontend)

⚠️ ÖNEMLİ:
  - turkanime.tv: on_request MP4 header → _SESSION_HEADERS → yt-dlp --add-header
  - build_ta_index.py: sitemap1-3.xml.gz → /mnt/c/.../scripts/ta_index.json
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
