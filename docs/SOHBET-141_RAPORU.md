# SOHBET-141 — Video Pipeline Kalan Hataların Giderilmesi

**Tarih:** 2026-07-11  
**Sürüm:** 1.0  
**Test Sonucu:** 4/6 PASS, 2/6 FAIL (known limitations)

---

## Hedef

SOHBET-140'ta kalan 3 video indirme başarısızlığını gidermek:
1. **Naruto** (tranimaci.com → aso1.net rotor) — HTTP 404 / çıktı yok
2. **Dexter** (setfilmizle.uk → AJAX embed) — yt-dlp embed bulamadı
3. **3 Idiots** (hdfilmcehennemi.now → YouTube 429) — subtitle Too Many Requests

---

## Yapılan Değişiklikler

### `backend/downloader/stream_finder.py`

1. **Ölü embed domain filtresi** (`_DEAD_EMBED_DOMAINS`)
   - `aso1.net`, `srv.aso1.net`, `media.aso1.net` — rotor URL'leri döndüren ölü video sunucuları
   - `_playwright_find_embed` return mantığı: bu domainleri içeren embed URL'lerini atla

2. **YouTube/social media embed prioritization**
   - M3U8 / MP4'ten sonra YouTube, VK, OK.ru, Dailymotion embed'lerini öncele
   - JS-render wrapper sitelerden (fastplay.mom, aso1.net) önce döndür

3. **`.json` dosyalarını embed filtresinden çıkar**
   - `_is_embed`: `.json` uzantılı URL'leri embed olarak kabul etme
   - JW Player translation JSON dosyalarının `/player/` path match ile yanlışlıkla embed olarak yakalanmasını engeller

4. **`fastplay.mom` eklendi `_KNOWN_PLAYERS`**
   - Network request handler'ın fastplay.mom iframe URL'lerini yakalaması için

5. **Playwright session header + cookie saklama**
   - `on_request` handler: yalnızca MP4 değil, tüm embed URL'lerinin header'larını `_SESSION_HEADERS`'e kaydet
   - `_SESSION_COOKIES` modül değişkeni eklendi (tanımsızdı)
   - `_save_session_cookies` çağrısı try bloğu içine taşındı (scope hatası)
   - `get_session_cookies_arg()` fonksiyonu: session cookie'lerini yt-dlp `--add-header Cookie:` olarak döndür

6. **`_SESSION_COOKIES` modül değişkeni eklendi** (daha önce tanımlanmamıştı)

### `backend/downloader/anime.py`

1. **yt-dlp retry parametreleri**
   - `--extractor-retries 10` — video kaynağı çözümleme hatalarında 10 kez dene
   - `--retries 10` — indirme hatalarında 10 kez dene
   - `--throttled-rate 100K` — hız sınırlaması durumunda bekle
   - `--ignore-errors` — subtitle 429 gibi ikincil hataların ana indirmeyi bozmasını engelle

2. **Session cookie argümanları**
   - `get_session_cookies_arg()` çağrısı, Playwright'tan alınan cookie'leri yt-dlp'ye aktar

3. **Hata mesajı iyileştirmesi**
   - "[generic]" hatası durumunda: embed bulunamadıysa (original URL döndü) vs embed bulundu ama yt-dlp işleyemedi (fastplay.mom/aso1.net) ayrımı
   - Kullanıcı için daha açıklayıcı mesaj

### `backend/scraper/parsers.py`

1. **`setfilmizle` için generic parser eklendi** (SOHBET-140'tan kalan)
   - `parse_url()` ve `parse_url_with_tags()` fonksiyonlarına setfilmizle desteği

---

## Test Sonuçları

| Test | Sonuç | Detay |
|---|---|---|
| Anime - Naruto (tranimaci.com) | ❌ FAIL | aso1.net video sunucusu ölü (HTTP 404). Embed bulundu ama yt-dlp işleyemedi |
| Series - Dexter (setfilmizle.uk) | ❌ FAIL | fastplay.mom embed'i JS-render player, yt-dlp desteklemiyor |
| Movie - 3 Idiots (hdfilmcehennemi.now) | ✅ PASS | YouTube 429 `--ignore-errors` ile atlatıldı |
| Manga - Martial Peak (mangadex.org) | ✅ PASS | Değişiklik yok |
| Manhwa - Returner's Magic (ragnarscans.net) | ✅ PASS | Değişiklik yok |
| Game - Cult of the Lamb (FitGirl) | ✅ PASS | Değişiklik yok |

**Başarı: %66.7 (4/6)**

---

## Known Limitations

### Naruto (tranimaci.com)
- **Sorun:** aso1.net video sunucusu tamamen ölü. Tüm embeds (rotor, ifr.html, turkanime.tv/embed) yt-dlp ile indirilemiyor.
- **Çözüm bekleyen:** Yeni bir anime video kaynağı bulunmalı (örn: başka bir TR anime sitesi).

### Dexter (setfilmizle.uk)
- **Sorun:** fastplay.mom JS-render player. iframe içindeki video yalnızca tarayıcıda oynar, yt-dlp çekemez.
- **Çözüm bekleyen:** fastplay.mom'a recursive Playwright implementasyonu gerekli.

---

## Açıklama: Neden fastplay.mom Çalışmıyor?

1. setfilmizle.uk sayfası play butonu tıklandığında AJAX ile fastplay.mom iframe'i yükler
2. fastplay.mom yalnızca tarayıcı JS ortamında çalışan bir video player'dır
3. yt-dlp bu tip siteleri desteklemez ("Unsupported URL")
4. Playwright ile fastplay.mom sayfasına gitmek HTTP 403 döndürür (cross-origin koruma)
5. Çözüm: setfilmizle.uk sayfasında kalıp iframe içindeki network isteklerini yakalamak (M3U8/MP4)

**Çözüm için 2 seçenek:**
- **Kısa vadeli:** setfilmizle.uk için YouTube trailer embed'ini (sayfada fallback olarak bulunuyor) kullan → yt-dlp native destekliyor
- **Uzun vadeli:** `_playwright_find_embed`'e iframe içi recursive video URL yakalama ekle

---

## Relevant Files

- `backend/downloader/stream_finder.py`: tüm CF-bypass, Playwright, domain filtreleri
- `backend/downloader/anime.py`: yt-dlp wrapper, hata mesajları, retry
- `backend/scraper/parsers.py`: setfilmizle generic parser
- `tests/test_sohbet140_real_download.py`: 6-tür indirme testi
- `backend/scripts/run_sohbet141.sh`: test koşucusu
