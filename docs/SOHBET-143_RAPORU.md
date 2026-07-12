# SOHBET-143 RAPORU — Naruto/tranimaci Auth Sorunu + 6/6 PASS

## Özet

SOHBET-142'de tek FAIL olarak kalan Naruto S01E01 (tranimaci.com) sorunu çözüldü.
Toplam 9 alternatif Türk anime sitesi test edildi, sadece **animexe.com** auth gerektirmeden çalışıyor.

## Sorun Kök Nedeni

tranimaci.com, tüm sayfalarda Next.js `[data-player-embed]` div'i içinde
**triangle-alert** SVG uyarı ikonu gösteriyor. Auth session `null` olduğu için
video player yüklenmiyor. Bu bir site politikası — üyelik gerekiyor.

## Test Edilen Siteler

| Site | Naruto URL | Durum |
|------|-----------|-------|
| **animexe.com** | `/watch/naruto/1/1` | ✅ ÇALIŞIYOR — direkt MP4, auth yok |
| **acheriya.com** | `/izle/naruto` | ❌ Naruto anasayfası açılıyor, bölüm player'ı yok |
| **animpow.com** | `/naruto-1-bolum-izle` | ❌ HTTP 404 + auth duvarı |
| **openani.me** | `/naruto-1-bolum-izle` | ❌ HTTP 404, player yok |
| **codanime.net** | `/turkce-anime-izle/naruto-1-bolum-izle` | ❌ HTTP 404, boş sayfa |
| **tranimeizle.io** | `/naruto-1-bolum-izle` | ❌ CaptchaChallenge (bot koruması) |
| **turkanime.tv** | `/video/naruto-1-bolum` | ❌ Auth duvarı, login gerekiyor |
| **tranimeizle.co** | `/video/naruto-1-bolum` | ❌ Auth duvarı |
| **anizium.com** | `/naruto` | ❌ Login redirect |

## Çözüm

`animexe.com` doğrudan `<video>` tag ile MP4 sunuyor (renjiabari.asia CDN).
stream_finder'ın mevcut Playwright fallback'i zaten bu URL'yi bulabiliyordu.
Sadece stream_finder'ın animexe.com'u tanıması ve DB'deki episode URL'inin
güncellenmesi gerekiyordu.

## Değişiklikler

1. **DB (kurowatch.db):** Naruto ep1 URL `tranimaci.com/video/naruto-1-bolum`
   → `animexe.com/watch/naruto/1/1`
2. **stream_finder.py:** `_ANIME_ONLY_DOMAINS` ve `_FORCE_PLAYWRIGHT`'a
   `animexe.com` eklendi
3. **test_sohbet142_full_e2e.py:** WSL path (`/mnt/c/...`) → Windows path
   (`C:\...`) çevirisi eklendi

## Test Sonucu

**6/6 PASS — %100 başarı!**

- Naruto S01E01: 84.8 MB MP4 ✅
- Dexter S08E01: 875 MB ✅
- 3 Idiots: 15.2 MB ✅
- Martial Peak Bölüm 1: 19 sayfa ✅
- Returner's Magic Bölüm 1: ✅
- Cult of the Lamb magnet: ✅

## Gelecek Riskler

- animexe.com ileride auth ekleyebilir veya kapanabilir
- Yedek olarak başka site bulunamadı (tüm alternatifler auth gerektiriyor)
- tranimaci.com'a cookies.txt ile giriş yapılırsa belki çalışabilir
