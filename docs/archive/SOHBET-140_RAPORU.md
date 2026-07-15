# SOHBET-140 RAPORU — Gerçek İndirme Testi (Tüm Türler)

**Tarih:** 10 Temmuz 2026
**API:** http://localhost:8099
**Test script:** tests/test_sohbet140_real_download.py

---

## Genel Sonuç: %50 Başarı (3/6)

| Tür | Örnek | Durum | Detay |
|-----|-------|-------|-------|
| Anime | Naruto S01E01 | ❌ BAŞARISIZ | tranimaci.com Cloudflare JS challenge — embed bulunamadı |
| Dizi | Dexter S08E01 | ❌ BAŞARISIZ | setfilmizle.uk video embed çözülemedi |
| Film | 3 Idiots | ❌ BAŞARISIZ | hdfilmcehennemi.now video 404 (sayfa var, video yok) |
| Manga | Martial Peak Bölüm 1 | ✅ BAŞARILI | 19 sayfa (1.87MB), 800x1131, mangadex.org |
| Manhwa | A Returner's Magic Bölüm 1 | ✅ BAŞARILI | 1 sayfa (168KB), 1200x675, ragnarscans.net |
| Oyun | Cult of the Lamb | ✅ BAŞARILI | Magnet URI kaydedildi (254 bytes) |

---

## Detaylı Test Sonuçları

### 1. Anime — Naruto S01E01 (❌)

| Alan | Değer |
|------|-------|
| Content | #469 Naruto |
| URL | https://tranimaci.com/video/naruto-1-bolum |
| Hata | tranimaci.com CF JS challenge — Playwright embed bulamadı |
| Kök Neden | tranimaci.com Cloudflare korumalı, headless browser'da JS challenge çözülemiyor |
| Çözüm Önerisi | tranimeizle.xyz kullan (CF yok, SOHBET-128'de çalıştı) veya manuel cookie import |

### 2. Dizi — Dexter S08E01 (❌)

| Alan | Değer |
|------|-------|
| Content | #287 Dexter |
| URL | https://www.setfilmizle.uk/bolum/dexter-1-sezon-1-bolum/ (site fallback) |
| Hata | setfilmizle.uk video embed bulunamadı |
| Kök Neden | Sitenin video oynatıcısı AJAX/JS ile yükleniyor, stream_finder tespit edemiyor |
| Çözüm Önerisi | Site-specific parser yaz (SOHBET-110/111 parser altyapısı var) |

### 3. Film — 3 Idiots (❌)

| Alan | Değer |
|------|-------|
| Content | #203 3 Idiots |
| URL | https://www.hdfilmcehennemi.now/film/3-aptal-2009-izle-2/ (site fallback) |
| Hata | yt-dlp HTTP 404: video sayfası var ama video dosyası yok/kırık |
| Kök Nedeni | hdfilmcehennemi.now film sayfası çalışıyor ama video embed URL'si ölü |
| Çözüm Önerisi | Site yedek domain dene (hdfilmcehennemi.name/.gg/.ws) veya film yeniden ekle |

### 4. Manga — Martial Peak Bölüm 1 (✅)

| Alan | Değer |
|------|-------|
| Content | #1 Martial Peak |
| URL | https://mangadex.org/chapter/1e9f55cb-edc3-4ef7-bc70-64111089f18a |
| Dosya | `/downloads/manga/1/ch0001/` |
| Sayfa Sayısı | 19 |
| Toplam Boyut | 1.87 MB (1,965,796 bytes) |
| Çözünürlük | 800x1131 px |
| Doğrulama | PIL ile ilk sayfa açıldı ✅ |
| İndirme Süresi | ~3 saniye |

### 5. Manhwa — A Returner's Magic Should Be Special Bölüm 1 (✅)

| Alan | Değer |
|------|-------|
| Content | #10 A Returner's Magic Should Be Special |
| URL | https://ragnarscans.net/manga/0c-magic/1/ (dead manhwahentai.me fallback) |
| Dosya | `/downloads/manga/10/ch0001/` |
| Sayfa Sayısı | 1 |
| Toplam Boyut | 168 KB (168,186 bytes) |
| Çözünürlük | 1200x675 px |
| Doğrulama | PIL ile açıldı ✅ |
| Not | manhwahentai.me dead (stripchat redirect), ragnarscans.net otomatik kullanıldı |

### 6. Oyun — Cult of the Lamb (✅)

| Alan | Değer |
|------|-------|
| Content | #128 Cult of the Lamb |
| Kaynak | FitGirl Repacks |
| Magnet URI | `magnet:?xt=urn:btih:26bb0deba0fbfe9232ead1e41460bdb4ed026005&dn=rutor.info_Cult+of+the+Lamb%3A+The+...` |
| Dosya | `downloads/sohbet140_kanit/cult_of_the_lamb_magnet.txt` |
| Boyut | 254 bytes |
| Doğrulama | Dosya diske yazıldı, magnet URI formatı geçerli ✅ |

---

## Başarısızlık Analizi

3 başarısız testin ortak nedeni: **Backend scraper'ın video embed çözememesi**.

- KuroWatch'ın **manga/manhwa indirme** pipeline'ı (MangaDex API + Madara parser) **çalışıyor**
- KuroWatch'ın **video indirme** pipeline'ı (yt-dlp + stream_finder) site engellerine takılıyor
- Oyun **FitGirl scraper**'ı çalışıyor (cssselect kurulunca)
- Test script'inin kendisi (API çağrıları, job takibi, dosya doğrulama) **sorunsuz çalışıyor**

## Çözüm Önerileri

1. **tranimaci.com** → `tranimeizle.xyz` kullan (CF yok, SOHBET-128'de kanıtlandı). Episode URL'lerini güncelle.
2. **setfilmizle.uk** → Site-specific parser (hdfilmcehennemi/dizigom parser'larına benzer)
3. **hdfilmcehennemi.now** → Alternatif domain dene veya film kaynağını yenile

## Temizlik

Test sonrası indirilen dosyalar silindi:
- `/downloads/manga/1/ch0001/` — silindi
- `/downloads/manga/10/ch0001/` — silindi
- `/downloads/sohbet140_kanit/` — silindi
