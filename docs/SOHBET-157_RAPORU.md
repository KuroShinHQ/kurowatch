# SOHBET-157 Raporu: Alternatif Siteleri DB'ye Ekle + MangaDex ID Senkronizasyonu

**Tarih:** 2026-07-14
**Hedef:** KuroWatch yeniden %90+ başarı

## Özet

MangaDex senkronizasyonu ile **manga/manhwa %95 canlandı** (134→8 orphan). Film URL dönüşümü kısmi başarılı (4/53). Anime ve cartoon için hâlâ kaynak gerekli.

| Tür | Toplam | Orphan (önce) | Orphan (sonra) | Canlılık |
|-----|--------|---------------|----------------|----------|
| manga | 66 | 59 | 5 | **%92 → %92 (MangaDex)** |
| manhwa | 96 | 75 | 3 | **%97 → %97 (MangaDex)** |
| series | 49 | 2 | 2 | **%96** |
| movie | 113 | 60 | 60 | %47 (hdfilmcehennemi.nl efektif ölü) |
| game | 19 | 0 | 0 | **%100** (FitGirl) |
| anime | 318 | 308 | 308 | **%3** (kritik) |
| cartoon | 53 | 53 | 53 | **%0** |
| **TOTAL** | **714** | **557** | **431** | |

## Yapılanlar

### 1. MangaDex UUID Senkronizasyonu ✅
- **162 manga/manhwa** içerik taranıp MangaDex API ile eşleştirildi
- **135 unique UUID** bulundu ve DB'ye `external_id = mdx:{uuid}` olarak yazıldı
- **111 yeni MangaDex site kaydı** eklendi (primary olmayanlar mevcut siteleri korur)
- Toplam chapter sayıları güncellendi (API aggregate ile)
- **İndirme testi: ✅ Martial Peak Ch.3844 (660KB, 16 sayfa)** MangaDex CDN'den indirildi

### 2. Hdfilmcehennemi.nl → .io Dönüşümü ⚠️
- 53 film URL'si test edildi
- **Sadece 4/53 başarılı** (.io mirror çok sınırlı içerik)
  - American Psycho → hdfilmcehennemi.io/american-psycho/
  - Planet of the Apes → hdfilmcehennemi.io/planet-of-the-apes/
  - Shark Tale → hdfilmcehennemi.io/shark-tale/
  - The Collector → hdfilmcehennemi.io/the-collector/

### 3. Kalan 25 Orphan Manga/Manhwa Retry ✅
- Alternatif İngilizce başlıklarla MangaDex'te tekrar arandı
- **21/25 found**, 4 hala bulunamadı

### 4. Duplicate Temizliği ✅
- 16 duplicate UUID tespit edildi (aynı manga farklı başlıklarla DB'de 2 kayıt)
- Gerçek duplicatelere MangaDex sitesi geri eklendi
- Yanlış eşleşmeler (ID=43, 89, 90) temizlendi

## DB Durumu

| Metrik | Değer |
|--------|-------|
| Toplam içerik | 714 |
| Orphan içerik | 431 (%-22.6) |
| Alive site | 330 |
| Dead site | 1,692 |
| external_id güncellenen | 135 |

## Hala Orphan Kalanlar

### Manga (5)
- ID=26 Deli Mühendis
- ID=43 Şamanın Yolu (yanlış eşleşme, silindi)
- ID=67 Sonsuz Döngüde Hapsolan
- ID=90 Sémalarin Kilici (yanlış eşleşme, silindi)
- ID=91 Oyun Obu Familia Aile Senki

### Manhwa (3)
- ID=89 The Unbeatable Dungeon's Lazy Boss Monster (yanlış eşleşme, silindi)
- ID=153 Martial Divine Demon
- ID=174 Shadow of the Supreme (yanlış eşleşme, silindi)

### Anime (308), Cartoon (53), Movie (60), Series (2)
Alternatif kaynak bulunamadı.

## Sıradaki Görevler

1. **Anime kaynağı entegrasyonu** — tranimeizle.org.tr (Anizm), OpenAnime, AniTurk
2. **Cartoon kaynağı araştırması** — 53 içerik sitesiz kaldı
3. **Movie URL pattern keşfi** — hdfilmcehennemi.nl yeni URL yapısı
4. **MangaDex chapter sayısı doğrulama** — bazı fuzzy matchler hatalı olabilir
5. **monomanga.com.tr Next.js downloader** — JS render ile içerik çekme

## Scripts

- `backend/scripts/sohbet157_mangadex_sync.py` — Ana MangaDex UUID sync
- `backend/scripts/sohbet157_retry_orphan.py` — Kalan orphanlar için İngilizce başlık denemesi
- `backend/scripts/sohbet157_movie_conversion.py` — Hdfilmcehennemi.nl→.io dönüşümü
- `backend/scripts/sohbet157_fix_duplicates.py` — Duplicate UUID temizliği
- `backend/scripts/sohbet157_restore_dups.py` — Gerçek duplicatelere site geri ekleme
- `backend/scripts/sohbet157_mark_dead.py` — Kalan ölü domainleri işaretleme
- `backend/scripts/sohbet157_test_download.py` — MangaDex indirme doğrulama

## JSON Çıktılar

- `docs/sohbet157_mangadex_results.json` — Tüm MangaDex eşleşmeleri
- `docs/sohbet157_movie_results.json` — Film dönüşüm sonuçları
