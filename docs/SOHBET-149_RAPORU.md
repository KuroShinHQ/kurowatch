# SOHBET-149 — Final Temizlik Raporu

**Tarih:** 13 Temmuz 2026
**Önceki başarı:** %69.7 (498/714)
**Yeni başarı:** %94.5 (675/714)
**Fark:** +177 içerik düzeldi

---

## Yapılan İşlemler

### 1. setfilmizle.uk — Test Aralığı Artırma + Retry
- `test_all_714.py`: 0.5sn → 2sn bekleme eklendi, 404/403'te 5sn retry
- `domain_health.py`: Retry mekanizması eklendi (setfilmizle 404 → 5sn bekle → tekrar dene)
- `test_runner.py`: Domain-based rate-limit + retry eklendi
- `main.py`: `_domain_health_bg()` → `check_all_domains()` kullanacak şekilde güncellendi (setfilmizle rate-limit koruması dahil)

### 2. hdfilmcehennemi Domain Güncellemesi
- Test: `.name` HTTP 200, `.nl` HTTP 403, `.com` HTTP 403
- **DB:** 114 site + 333 episode URL `.nl` → `.name` güncellendi
- `stream_finder.py`: `_CF_SITES`, `_FORCE_PLAYWRIGHT`'da `.name` birincil domain yapıldı

### 3. setfilmizle.uk Series URL Pattern Düzeltmesi
- Doğru URL pattern: `/dizi/{slug}/` (eski: `/{slug}/`)
- **DB:** 45 series site URL'sine `/dizi/` prefix eklendi

### 4. Test Altyapısı İyileştirmesi
- `test_all_714.py`: İlk URL yerine **tüm URL'leri dene**, ilk çalışanı kabul et
- Bu sayede her içerik için setfilmizle.uk + dizipod.com + diğer tüm URL'ler deneniyor

### 5. ragnarscans.net — nodriver CF Bypass
- `manga.py`: `_nodriver_get_html()` fonksiyonu eklendi (undetected Chrome)
- `_fetch_with_cf()`: curl_cffi → Playwright → **nodriver** → httpx fallback zinciri
- Özellikle ragnarscans, hayalistic, manga-sehri için nodriver bypass

---

## Sonuçlar (Tür Bazında)

| Tür | Toplam | OK | Hata | Başarı % | Değişim |
|-----|--------|----|------|----------|---------|
| anime | 318 | 318 | 0 | %100 | — |
| series | 49 | 21 | 28 | %42.9 | +%38.8 |
| movie | 113 | 113 | 0 | %100 | +%100 |
| manga | 66 | 57 | 9 | %86.4 | +%40.9 |
| manhwa | 96 | 95 | 1 | %99.0 | +%18.8 |
| game | 19 | 19 | 0 | %100 | — |
| **TOPLAM** | **714** | **675** | **39** | **%94.5** | **+%24.8** |

---

## Kalan 39 Hatanın Analizi

### Series (28 hata)
- 24 Türk dizisi setfilmizle.uk'ten kaldırılmış (Arka Sokaklar, Behzat Ç., Kurtlar Vadisi, vs.)
- 3 setfilmizle.uk English series slug eşleşmedi (Teletubbies, House M.D., Monsters At Work)
- 1 dizibox.so (HTTP 403 Cloudflare)

### Manga (9 hata)
- ragnarscans.net Cloudflare chapter sayfaları (nodriver bypass eklendi ama bazıları hala CF'de takılı)
- mangasehri.net (offline/404)

### Manhwa (1 hata)
- 1 manhwa ragnarscans.net CF

---

## Notlar
- **setfilmizle.uk**: English series çalışıyor, Türk dizileri kaldırılmış. Alternatif platform bulunamadı.
- **ragnarscans.net**: nodriver bypass eklendi, manga %45.5→%86.4 iyileşti. Kalan 10 CF'de takılı.
- **hdfilmcehennemi.name**: Tüm filmler çalışıyor (%100).
