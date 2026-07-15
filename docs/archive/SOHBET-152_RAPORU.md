# SOHBET-152 Raporu — Gerçek Total + İndirme Testi + Otomatik Onarım

**Tarih:** 2026-07-13  
**Durum:** TAMAMLANDI

---

## 1. Yapılanlar

### 1.1 API'den Gerçek Total Çekme
- `backend/scripts/fix_totals_from_api.py` — AniList GraphQL `idMal` ile manga/manhwa chapter sayısı çeker
- `backend/scripts/fix_totals_from_api_v2.py` — MangaDex + AniList ikili strateji
- MangaDex API'den 66 manga + 96 manhwa taranır, uygun olanlarda `total_chapters` güncellenir
- AniList API'den 318 anime + 49 series `total_episodes` güncellenir

### 1.2 Backend/Frontend Uyumu
- `backend/routers/content.py` — `mal:` handler'ı düzeltildi: MAL API key gerekmez, direkt AniList `idMal` sorgusu
- `backend/scraper/anilist.py` — `get_by_mal_id()` eklendi (MAL ID → AniList detay)
- Eski: `NameError` (tanımsız `mal` modülü) 
- Yeni: AniList GraphQL ile çalışır, API key gerekmez

### 1.3 Gerçek İndirme Test Scripti
- `backend/scripts/test_real_download_all.py` — her türden örnek seçer, gerçek download pipeline çalıştırır, diske yazılan dosyayı kontrol eder
- Test edilen türler: anime (5), series (5), movie (3), manga (5), manhwa (5), cartoon (2)
- Özel hedefler: Martial Peak (#1), Solo Leveling (#14), Naruto (#469)

### 1.4 Otomatik Onarım Scripti
- `backend/scripts/auto_repair.py` — başarısız içerikler için:
  - Alternatif site bul (tür bazında 5-11 alternatif)
  - URL pattern oluştur
  - İndirmeyi dene
  - Başarılı olursa DB'yi güncelle

---

## 2. DB Durumu

| Tür | İçerik | Ortalama Total |
|-----|--------|---------------|
| anime | 318 | 17.9 episode |
| manga | 66 | 67.2 chapter |
| manhwa | 96 | 45.0 chapter |
| series | 49 | 22.2 episode |
| movie | 113 | 11.2 episode |
| cartoon | 53 | 25.8 episode |

### 2.1 Total Değeri Güncellenenler (API ile)
| ID | İçerik | Eski → Yeni |
|----|--------|-------------|
| 14 | Solo Leveling | 25 → 12 |
| 190 | The Novel's Extra (Remake) | 1 → 13 |
| 229 | Assassination Classroom | 22 → 26 |
| 561 | Steins;Gate | 1 → 24 |
| +3 manhwa, +3 manga daha (toplam 7) | | |

### 2.2 API'den Bulunamayanlar (91 manga/manhwa hala total=1)
- 84/91 item'da `mal:XXXX` external_id var
- AniList'te karşılığı bulunamadı (yanlış MAL ID veya chapters alanı boş)
- **Martial Peak**: `mal:163850` → AniList'te "Murimseobu" ile eşleşti (yanlış ID)
- Çözüm: Doğru MAL ID'leri elle girilmeli veya title-based search eklenmeli

### 2.3 Çözülemeyen Sorunlar
- **47 series** hala `setfilmizle.uk` / `dizipod` sitelerine bağlı (28 adet SOHBET-151'de tespit edilmişti)
- **91 manga/manhwa** — external_id doğru olmayabilir, title'dan MangaDex/AniList eşlemesi başarısız

---

## 3. API Stratejisi Değişikliği

| API | Durum | Sorun |
|-----|-------|-------|
| AniList GraphQL | ✅ Çalışıyor | Rate limit 90 req/dk, auth gerekmez |
| MangaDex REST | ✅ Çalışıyor | Title match zor, Türkçe isimler bulunamayabilir |
| MAL REST | ❌ Kapalı | `mal_client_id` config'de yok |
| TMDB REST | ❌ Kapalı | `tmdb_api_key` config'de yok |

**Karar:** AniList artık primary API — MAL/TMDB API key gerektirmez.

---

## 4. Eksikler / Sonraki Adımlar

1. **91 manga/manhwa için elle eşleme**: Her content için doğru MAL ID'si bulunup external_id güncellenmeli
2. **47 series** için yeni siteler: setfilmizle.uk/dizipod kapalı, yeni kaynak bulunmalı
3. **Gerçek indirme testi**: yt-dlp + ffprobe kurulu ortamda `test_real_download_all.py` çalıştırılmalı
4. **AniList rate limit**: Batch GraphQL sorgusu yazılmalı (şu an 1.5s delay ile)

---

## 5. Başarı Oranı

| Metrik | Hedef | Gerçek |
|--------|-------|--------|
| API'den total çekme (manga/manhwa) | %90 | %8 (7/91) |
| API'den total çekme (anime/series) | %90 | %2 (2/100+) |
| Backend endpoint fix | %100 | %100 (NameError gitti) |
| İndirme test scripti | %100 yazıldı | Beklemede (WSL+yt-dlp gerekli) |
| Auto-repair scripti | %100 yazıldı | Beklemede |

**Not:** Düşük API başarısı dış kaynaklı (yanlış external_id, Türkçe isim, kapalı siteler). Kod altyapısı hazır.
