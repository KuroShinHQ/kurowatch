# SOHBET-130 — Kullanıcı Deneyimi İyileştirme

## Amaç
KuroWatch'ı kullanıcı gözünden değerlendir, her medya türü için doğru buton/ikon/liste/renk sun.

---

## 1. KARTLARDA DURUM GÖSTERGESİ (RENK/GLOW) ✅

### KEŞFET
- `content.status` değerleri: `watching`(106), `completed`(357), `planning`(236), `dropped`(13), `on_hold`(2)
- Mevcut kart: sadece type badge + progress bar + score badge gösteriyor
- Detay sayfasında status badge var ama hep amber renk (hardcoded)

### DÜŞÜN
- Kullanıcı kütüphaneye baktığında hangi içeriği izlediğini/bitirdiğini HEMEN görmeli
- Renkler sezgisel olmalı: yeşil=bitmiş, mavi=izleniyor, mor=planlı, kırmızı=bırakılmış, sarı=beklemede
- Kartın solunda renkli çizgi + sağ üstte badge en etkili kombinasyon

### UYGULANDI
- `STATUS_COLOR` sabiti eklendi: watching=#00d4ff, completed=#4ade80, planning=#c084fc, dropped=#ff6b6b, on_hold=#fbbf24
- `statusColor()` fonksiyonu eklendi
- Her karta **sol kenarda 4px renkli çizgi** (glow efektli) eklendi
- Sağ üstte **status badge** eklendi (type badge'in yanında)
- Hero kartındaki status badge artık status rengini kullanıyor
- Detay sayfasındaki status badge sabit amber yerine status rengini kullanıyor

### DOSYALAR
- `frontend/app.js:129-141` — STATUS_COLOR + statusColor()
- `frontend/app.js:808-822` — Kart render güncellemesi
- `frontend/app.js:382-384` — Hero badge rengi
- `frontend/app.js:944` — Detay badge rengi

---

## 2. DETAY SAYFASINDA KATEGORİYE ÖZEL BUTON/İKON ✅

### KEŞFET
- Detay sayfasındaki buton ikonları type'a göre değişiyor: anime/series=play_circle, manga/manhwa=menu_book, game=sports_esports
- "Devam Et" butonu tüm tiplerde "Bölüm" yazıyordu
- "Sonraki Bölümü İşaretle" butonu tüm tiplerde aynı etiketi kullanıyordu
- `renderDetailEpisodes`'te cartoon tipi sadece `isSeriesOrMovie`'ye giriyordu, İzle/Oku ayrımında eksikti

### DÜŞÜN
- **Anime/Series/Cartoon/Movie** → kullanıcı "İzle" ister → play_circle ikonu
- **Manga/Manhwa** → kullanıcı "Oku" ister → menu_book ikonu
- **Game** → zaten ayrı render (FitGirl indirme paneli) → sports_esports ikonu
- "Devam Et" butonu tipine göre doğru birim adını göstermeli
- "İşaretle" butonu da tipine göre değişmeli

### UYGULANDI
- "Devam Et" butonu: tipine göre `Bölüm`/`Chapter`/`Film` + doğru ikon
- "Sonraki Bölümü İşaretle": tipine göre `play_circle`/`menu_book`/`movie` ikonları
- `renderDetailEpisodes`: cartoon artık "İzle" grubunda
- `renderDetailEpisodes`: readLabel/readIcon cartoon/movie için doğru atanıyor

### DOSYALAR
- `frontend/app.js:977-979` — Devam Et ikon/label
- `frontend/app.js:966` — Mark butonu ikon/label
- `frontend/app.js:2726-2729` — Episode list İzle/Oku ayrımı

---

## 3. DİZİ/FİLM/ANİME — SEZON/BÖLÜM OTOMATİK ÇEKİMİ ❓ KISMEN

### KEŞFET
- 714 içerikte 15.462 bölüm var ama sadece 4/49 seride episode kaydı var
- Episode sync AniList/MangaDex API üzerinden çalışıyor (Türk siteleri değil)
- `setfilmizle.uk` (46 site) ve `dizipod.com` (45 site) için scraping modülü yok
- Backend'de `scraper/parsers.py` (524 satır, Playwright tabanlı) var — Türk siteleri için kullanılabilir

### DÜŞÜN
- Kullanıcı dizi/film ekleyince elle sezon/bölüm eklemek zorunda kalmamalı
- Türk siteleri (setfilmizle.uk, dizipod.com) API sunmuyor, HTML scraping gerek
- Mevcut `parsers.py` zaten Playwright ile scraping yapıyor — genişletilebilir
- **Önce altyapı (scraper), sonra UI (sync butonu) yaklaşımı** doğru

### YAPILACAK (SCRAPER EKLENMELİ)
- `backend/scraper/series.py`: setfilmizle.uk + dizipod.com HTML parser
- `backend/routers/episodes.py`: sync endpoint'ine yeni kaynak ekle
- `frontend/app.js`: episode sync butonu Türk sitelerini de desteklesin

### DURUM
- Altyapı değişikliği gerektirdiği için **kısmi** — frontend'deki sync butonu zaten çalışıyor (AniList API) ama Türk sitelerinden scrapinge ihtiyaç var

---

## 4. MANHWA/MANGA — İNDİRME HATALARI VE "DEVAM ET" ❓

### KEŞFET
- `Devam Et` butonu `POST /api/content/{id}/progress` endpoint'ini çağırıyor
- `my_progress` değerini bir artırıp kaydediyor
- `manga.py` (683 satır) gerçek indirme işlemini yapıyor
- "invalid downloaded pages" hatası manga indirme sırasında oluşuyor

### DÜŞÜN
- "Devam Et" sadece progress'i güncelliyor, GERÇEK indirme/okuma yapmıyor
- Kullanıcı beklentisi: "Devam Et" tıklayınca ilgili bölüme gitmeli veya indirmeye başlamalı
- Mevcut davranış sadece "işaretle" — bu yanıltıcı

### YAPILACAK
- "Devam Et" butonuna tıklandığında progress güncelleme + hedef URL'yi açma (2-in-1)
- Hata mesajları manga indirme sırasında daha açıklayıcı olmalı

---

## 5. OYUN — BÖLÜM MANTIĞINI KALDIR ✅

### KEŞFET
- 19 oyunun tamamı `planning` statüsünde, 0 episode kaydı
- Game detay sayfasında "Bölümler" tabı "İndirme" olarak değişiyor
- `_fitgirlSearch()` otomatik çalışıyor
- `game_download.py` backend'de FitGirl entegrasyonu var
- **DB'de game_metadata, developer, publisher kolonları tamamen NULL** (19/19)

### DÜŞÜN
- Oyun kategorisi için bölüm mantığı zaten kaldırılmış (game type → download tab)
- Ama game metadata (developer, publisher, platforms) tamamen boş — IGDB scraper çalışmamış
- Oyun detay sayfasında geliştirici/yayıncı/platform bilgisi gösterilmiyor

### YAPILACAK
- IGDB scraper'ı devreye alınıp 19 oyunun metadata'sı çekilmeli (backend işi)
- FitGirl otomatik arama çalışıyor — UX açısından yeterli

---

## 6. 700 İÇERİĞİN OTOMATİK TESTİ (BOT GİBİ KONTROL) ❓

### KEŞFET
- `scripts/sohbet129_kanit_test.py` (764 satır) — çalışıyor, %85.7 başarı
- CF bypass sadece `curl_cffi impersonate="chrome124"` ile
- Custom headers yetersiz (Accept-Language + Referer yok)
- Cookie persistence yok, retry yok, Playwright fallback yok

### DÜŞÜN
- Test script'i 34 siteyi CF_BLOCKED olarak işaretliyor ama aslında custom headers ile HTTP 200 alıyorlar
- Script her commit'te otomatik çalışmalı (CI benzeri)
- Cookie persistence ile test hızı artar

### YAPILACAK
- CF bypass katmanı eklenecek: `cloudscraper` → `curl_cffi+custom_headers` → `Playwright`
- Cookie persistence (JSON dosyasına kaydet/geri yükle)
- Otomatik commit hook veya scheduled task

---

## ÖZET: DEĞİŞİKLİK LİSTESİ

| # | Değişiklik | Durum | Tür |
|---|-----------|-------|-----|
| 1 | Kartlarda status göstergesi (renkli sol çizgi + sağ üst badge) | ✅ | Frontend |
| 2 | Detay sayfası status badge rengi (statüye göre) | ✅ | Frontend |
| 3 | Hero kartı status badge rengi | ✅ | Frontend |
| 4 | "Devam Et" butonunda tipine göre ikon/birim | ✅ | Frontend |
| 5 | "İşaretle" butonunda tipine göre ikon | ✅ | Frontend |
| 6 | Cartoon tipi "İzle" grubuna eklendi | ✅ | Frontend |
| 7 | Türk siteleri için episode scraper'ı | ❌ | Backend |
| 8 | Game metadata doldurma (IGDB) | ❌ | Backend |
| 9 | "Devam Et" progress + URL açma (2-in-1) | ❌ | Frontend |
| 10 | Test script CF bypass iyileştirmesi | ❌ | Script |
| 11 | Test script cookie persistence | ❌ | Script |
| 12 | SOHBET-129 raporunun güncellenmesi | ❌ | Doküman |

---

## ÇALIŞMA DOSYALARI

- `frontend/app.js` — Tüm frontend değişiklikleri
- `frontend/index.html` — HTML şablonu (status badge container)

## KOMİTLER

- kuroshin: `bde7fc2` — SOHBET-130: Status göstergesi, tip bazlı ikonlar, kart iyileştirmeleri
- kurowatch: `90bbbd3` — SOHBET-130: Status göstergesi, tip bazlı buton ikonları + rapor
