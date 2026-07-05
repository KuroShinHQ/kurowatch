# KuroWatch Tespit Edilen Sorunlar (5 Temmuz 2026)

> ⛔ **KRİTİK**: Bu dosyadaki sorunlar düzeltilmeden yeni özellik eklenmez.

---

## P1 — Video Player Butonları (9 buton, çoğu çalışmıyor)

### Durum
Sağ üstteki 9 butondan birkaçı hariç diğerleri çalışmıyor.

| # | ID | İşlev | Çalışıyor? | Sorun |
|---|----|-------|-----------|-------|
| 1 | player-cc-btn | Altyazı Paneli | ✅ JS var | CSS/konum sorunu olabilir |
| 2 | player-ambient-btn | Ambient Mode | ✅ | — |
| 3 | player-quality-btn | Kalite Seçimi | ❌ **Kozmetik** | video.src DEĞİŞMİYOR, sadece data-quality güncelleniyor. Gerçek kalite değişimi YOK |
| 4 | player-episodes-btn | Bölüm Listesi | ✅ JS var | API'den episode çekiyor |
| 5 | player-lock-btn | Ekran Kilidi | ✅ | — |
| 6 | player-capture-btn | Ekran Görüntüsü | ✅ | — |
| 7 | player-theater-btn | Theater Mode | ❓ CSS var | `hidden sm:flex` — mobile'da gizli. CSS class tanımlı |
| 8 | player-pip-btn | Picture-in-Picture | ❓ | Browser API'ye bağlı, mobile'da gizli |
| 9 | player-mini-btn | Mini Player | ❓ CSS var | `hidden sm:flex` — mobile'da gizli |

**Kök neden:** Kalite seçimi için backend'de farklı çözünürlükte stream yok. Sadece tek bir dosya sunuluyor (`/api/download/serve/{jobId}`). Kalite butonu kullanıcıya yanlış umut veriyor.

### Çözüm önerisi
- Kalite butonunu **gizle** veya "Otomatik" olarak sabitle (mevcut durumu göster, değiştirme)
- Veya butona tıklandığında "Bu özellik henüz kullanılamıyor" toast'u göster

---

## P2 — Nano Machine 403 Forbidden (ragnarscans.com)

### Durum
- **İçerik ID:** 18 (Nano Machine, type=manga)
- **DB'deki siteler:** MangaGezgini (`mangagezgini.com`) + MangaŞehri (`mangasehri.net`)
- **Episode URL'i:** `https://ragnarscans.com/manga/nano-makine/bolum-1/`
- **Hata:** `Client error '403 Forbidden' for url 'https://ragnarscans.com/...'`

### Kök neden: **SİTE-EPISODE URL TUTARSIZLIĞI**
Content'in site listesi (`/api/content/{id}` → `sites[]`) ile episode URL'leri (`/api/content/{id}/episodes` → `url`) **farklı domain'lere** işaret ediyor:
- Content siteleri: mangagezgini.com, mangasehri.net
- Episode URL'leri: ragnarscans.com

Episode URL'leri eski bir sync'ten kalma. Ragnarscans.com artık 403 döndürüyor (muhtemelen Cloudflare veya IP ban).

### Kapsam
Bu sorun sadece Nano Machine'de değil — episode URL'leri ile content site listesi arasında yaygın bir **eşleşme kayması** var. Tüm içeriklerde episode URL'lerinin doğruluğu kontrol edilmeli.

### Çözüm önerisi
1. Episode URL'lerini content'in primary site'ına göre yeniden derive et
2. Veya content site listesine ragnarscans.com'u ekle (çalışıyorsa)
3. 403 hatası alınınca otomatik olarak fallback site'ı dene

---

## P3 — Black Butler: "video embed bulunamadı" (tranimaci.com)

### Durum
- **İçerik ID:** 716 (Black Butler: Public School Arc, type=anime)
- **Episode URL:** `https://tranimaci.com/video/black-butler-public-school-arc-1-bolum`
- **Site:** tranimaci.com
- **Hata:** `tranimaci.com sitesinde video embed bulunamadı veya desteklenmiyor`

### Kök neden
stream_finder.py'nin tranimaci.com için iki bypass katmanı var:
1. **nodriver** (CF Managed Challenge çözer, 20sn bekler)
2. **Playwright** (stealth, request interception)

İkisi de başarısız olunca yt-dlp'ye orijinal URL verilir, yt-dlp de `[generic]` hatası verir (desteklenmeyen embed).

### Olası nedenler
1. tranimaci.com'da bu anime gerçekten yok (yanlış slug)
2. tranimaci.com sayfa yapısı değişti (iframe/player class değişti)
3. CDN token süresi doldu
4. nodriver/Playwright bypass çalışmıyor (yeni bot detection)

### Çözüm önerisi
1. Önce URL'in tranimaci.com'da geçerli olup olmadığını manuel kontrol et
2. stream_finder.py'de tranimaci.com için CSS selector'ları güncelle
3. Varsa çalışan alternatif site ekle

---

## P4 — Video Player: Tüm butonlar DOM'da ama görünmez/kullanılamaz

### Durum
Playwright testi `test_player_buttons.py` yazıldı ama `page` fixture eksikliğinden çalışmadı. Player modal'ı açmak için OYNAT butonuna basmak gerekiyor.

### Olası sorunlar
1. Player modal'ı z-index sorunu — butonlar görünmüyor olabilir
2. CSS `hidden sm:flex` — mobile viewport'ta 3 buton gizli
3. Video yoksa (src boşsa) butonların çoğu işlevsiz
4. Kalite seçici panelde "UYGULA" butonu hiçbir şey yapmıyor

### Ne test edilmeli
- [ ] Player modalı açılıyor mu?
- [ ] 9 buton da görünür mü? (desktop viewport)
- [ ] CC butonu panel açıyor mu?
- [ ] Ambient butonu canvas gösteriyor mu?
- [ ] Quality panel açılıp kapanıyor mu?
- [ ] Lock butonu overlay gösteriyor mu?
- [ ] Capture butonu screenshot indiriyor mu?
- [ ] Theater/PiP/Mini butonları çalışıyor mu?

---

## P5 — Episode URL Derivation (episodes.py) — Sayısal Çakışma Riski

### Durum
`_ep_url_for_number()` fonksiyonu, URL'deki sayısal bölüm numarasını regex ile bulup değiştiriyor. 

### Risk
URL'de birden fazla sayı varsa (örn: slug içinde yıl, sezon no, başka ID), yanlış sayı değiştirilebilir.

Örnek: `/berserk-1997/ep-1-bolum` → `1997` yerine `1998` yapılabilir.

### Çözüm önerisi
Regex'te `bolum` veya `chapter` kelimesine yakın sayıyı tercih et. `_extract_ep_from_url()` zaten bunu yapıyor ama `_derive_ep_url()` fallback'te hala hata yapabilir.

---

## P6 — Manga Download: ragnarscans.com _OFFLINE veya CF Korumalı Olabilir

### Durum
ragnarscans.com manga.py'de `_MADARA_DOMAINS` listesinde ama `_CF_BLOCKED` setinde DEĞİL. 403 Forbidden dönüyorsa ya Cloudflare koruması var ya da IP banlanmış.

### Yapılması gereken
1. `requests.get('https://ragnarscans.com')` ile site erişilebilirliğini test et
2. CF koruması varsa `_CF_BLOCKED` setine ekle
3. DNS çözümlemesi yapılamıyorsa `_OFFLINE` setine ekle
4. Çalışan alternatif site var mı kontrol et (mangagezgini.com, mangasehri.net)

---

## Özet: Düzeltme Sırası

| Öncelik | Sorun | Çözüm |
|---------|-------|-------|
| **P1** | Quality butonu kozmetik | Butonu gizle veya "Otomatik" yap |
| **P2** | Episode URL ≠ Site URL | Sync mekanizmasını düzelt |
| **P3** | tranimaci.com embed yok | stream_finder'ı güncelle veya URL'i doğrula |
| **P4** | Player buton testi yaz | PW testi düzeltip çalıştır |
| **P5** | URL derivation sayısal çakışma | Regex'i iyileştir |
| **P6** | ragnarscans.com 403 | Site durumunu kontrol et, offline/CF olarak işaretle |
