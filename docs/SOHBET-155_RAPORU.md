# SOHBET-155 Raporu: Gerçek %5 İndirme Testi

**Tarih:** 2026-07-13
**Test Script:** `backend/scripts/s155_final.py`

## Özet

| Tür | Test | Sonuç |
|-----|------|-------|
| Manga | MangaDex | ✅ OK (19 sayfa, PIL doğrulama) |
| Manhwa | MangaDex fallback | ❌ Site for sale/dead |
| Anime | tranimaci.com stream_finder | ❌ CF PoW challenge bypass edilemiyor |
| Movie | hdfilmcehennemi.nl stream_finder | ❌ Site 404/403 |
| Series | check_sites | ❌ Tüm siteler dead/CF |
| Game | FitGirl Repacks | ✅ OK (magnet link tespiti) |

## Detaylı Sonuçlar

| İçerik | Tür | Method | Durum | Detay |
|--------|-----|--------|-------|-------|
| Martial Peak | manga | MangaDex ch1 download | ✅ | 19 sayfa, PIL verify OK |
| Cult of the Lamb | game | FitGirl magnet check | ✅ | 2 magnet link bulundu |
| Frostpunk 2 | game | FitGirl magnet check | ✅ | 2 magnet link bulundu |
| Hardcore Leveling Warrior | manhwa | check_sites | ❌ | 4 site var ama hepsi dead/CF |
| Solo Leveling | manhwa | check_sites | ❌ | 4 site var ama hepsi dead/CF |
| Game of Thrones | series | check_sites | ❌ | 2 site var, tranimaci CF |
| Breaking Bad | series | check_sites | ❌ | 5 site var, hepsi dead |
| 3 Idiots | movie | stream_finder | ❌ | hdfilmcehennemi.nl 404+403 |
| Fight Club | movie | stream_finder | ❌ | hdfilmcehennemi.nl 404+403 |
| The Silence of the Lambs | movie | check_sites | ❌ | 2 site var, tranimaci CF |
| Naruto | anime | stream_finder | ❌ | tranimaci.com timeout 90s |

## Site Sağlık Durumu

| Site | Durum | Sorun |
|------|-------|-------|
| mangadex.org | ✅ Çalışıyor | API-based, her manga var |
| fitgirl-repacks.site | ✅ Çalışıyor | HTTP 200, magnet link var |
| mangatr.app | ❌ **DOMAIN SATILIK** | Alan adı süresi dolmuş |
| manhwahentai.me | ❌ **DNS ÇÖKÜK** | Erişilemiyor |
| setfilmizle.uk | ❌ **SİTE KALDIRILMIŞ** | 404 |
| dizipod.com | ❌ **SİTE KALDIRILMIŞ** | 404 |
| hdfilmcehennemi.nl | ❌ **404** | Film sayfaları 404, CF 403 |
| tranimaci.com | ❌ **CF PoW Challenge** | JS PoW SHA-256, nodriver+Playwright bypass edemiyor |
| mangasehri.net | ❌ **CF 403** | Cloudflare ile bloklu |
| merlintoon.com | ❌ **CF 403** | Cloudflare ile bloklu |
| mangakurdo.com | ❌ **BAĞLANAMIYOR** | Connection error |
| dizipub.com | ❌ **DOMAIN SATILIK** | - |
| monomanga.com.tr | ⚠️ **Next.js** | HTTP 200 ama JS render gerekli |

## Tespit Edilen Sorunlar

### 1. tranimaci.com CF PoW Challenge
- Site Cloudflare Managed Challenge (JS PoW SHA-256) kullanıyor
- `_resolve_tranimaci()`: mirror'a yönlendiriyor (tranimeizle.co) ama orada da aynı challenge var
- Playwright 90sn bekliyor, PoW'u çözüyor gibi görünüyor ama sonra player elementi DOM'da bulunamıyor
- `_NODRIVER_HTML_SITES` ile nodriver HTML alınıyor (25631 byte) ama embed/iframe/video tag'i yok
- **Kök neden:** Player sayfa yüklendikten çok sonra JS ile inject ediliyor, selector'lar eski kalmış

### 2. hdfilmcehennemi.nl 404
- Tüm film URL'leri (`/film/...-izle-2/`) HTTP 404 dönüyor
- curl_cffi ile de HTTP 403 (Cloudflare)
- Site ya taşınmış ya da URL yapısı değişmiş
- **Alternatif bulunamadı**

### 3. Madara siteleri ölü
- mangatr.app: domain satılık
- mangasehri.net: CF 403
- merlintoon.com: CF 403
- ragnarscans.net: durumu bilinmiyor (test edilmedi)
- **Kök neden:** Çoğu Madara sitesi Cloudflare korumasına geçti veya kapandı

### 4. Dizi siteleri tamamen ölü
- setfilmizle.uk, dizipod.com: kaldırılmış
- Alternatif dizi sitesi DB'de yok

### 5. MangaDex dışı manga kaynağı yok
- monomanga.com.tr HTTP 200 ama Next.js ile JS render
- Mevcut Madara parser'ı çalışmıyor

## Çalışan Çözümler

### Manga/Manhwa: **MangaDex API**
- `_mangadex_chapter()` fonksiyonu çalışıyor
- Tüm manga/manhwa için MangaDex ID'si bulunup kullanılabilir
- API rate limit var ama makul

### Oyun: **FitGirl Repacks**
- HTTP 200, magnet link çekilebiliyor
- `gallery-dl` veya `httpx` ile sayfa scrape yeterli
- Magnet link'ten torrent indirme ayrı bir iş

### Anime: **Alternatif çözüm gerekli**
- Tranimaci.com artık çalışmıyor
- Yeni bir anime kaynağı eklenmeli (örn. tranimeizle.com veya benzeri)
- Veya yt-dlp ile direkt anime sitelerinden indirme

### Film/Dizi: **Alternatif çözüm gerekli**
- Hdfilmcehennemi.nl ölü
- Yeni film/dizi kaynağı eklenmeli

## Öneriler

1. **Acil:** Tüm manga/manhwa için MangaDex ID'si bulup DB'ye ekle (MangaDex birincil kaynak olsun)
2. **Acil:** Ölü siteleri DB'de işaretle (`is_dead=True`)
3. **Kısa vade:** monomanga.com.tr için yeni bir downloader yaz (Next.js site)
4. **Kısa vade:** Yeni anime kaynağı bul + stream_finder'a ekle
5. **Kısa vade:** Yeni film/dizi kaynağı bul + stream_finder'a ekle
6. **Uzun vade:** tranimaci.com için Playwright bypass'ını düzelt (selektor güncelleme)
7. **Uzun vade:** Cloudflare siteleri için curl_cffi impersonate yapılandırması

## Test Edilen Scriptler

- `backend/scripts/s155_final.py` — Final test script
- `backend/scripts/s155_test.py` — İlk deneme (broken URL derivation)
- `backend/downloader/stream_finder.py` — Stream URL bulma (tranimaci + hdfilmcehennemi)
- `backend/downloader/manga.py` — Manga downloader (MangaDex çalışıyor, Madara ölü)

## Loglar

```
Test: 11 total | OK=3 | FAIL/WARN=8
OK: Martial Peak (MangaDex, 19 pages), Cult of the Lamb (FitGirl), Frostpunk 2 (FitGirl)
FAIL: 8 content items (stream/dead sites)
```
