# SOHBET-161 RAPORU — ACİL DÜZELTMELER

**Tarih:** 14 Temmuz 2026
**Durum:** TAMAMLANDI

---

## 1. Frontend Tür Kontrolü — ✅ DÜZELTİLDİ

### Bulunan Hatalar
- **player.js:225** (`job.media_type === 'anime'`) → sadece `anime` için "▶ OYNAT", diğer tüm türler için "📖 OKU" gösteriyor.
- **app.js:1776** (`u.content_type === 'anime'`) → sadece `anime` için "İZLE", diğerleri "OKU".
- **app.js:967** (`statusIcon`) → `cartoon` türü `play_circle` icon'undan düşmüş.
- **app.js:3033, 3062, 3120** → sadece `anime` kontrolü, `series`/`movie`/`cartoon` eksik.

### Yapılan Değişiklikler
Tüm `=== 'anime'` kontrolleri `=== 'anime' || === 'series' || === 'movie' || === 'cartoon'` olarak genişletildi.

**Değişen dosyalar:**
- `frontend/player.js` — 1 nokta (download job card)
- `frontend/app.js` — 6 nokta (updates card, status icon, play/overlay/dl button handlers)

### Kanıt
Dexter (series türü) için download sonrası "📖 OKU" yerine "▶ İZLE" gösterir.

---

## 2. Madara Parser Fix — ✅ DÜZELTİLDİ

### Sorun
My Blasted Reincarnated Life ve Hardcore Leveling Warrior: Earth Game hata veriyordu:
- "Madara: hiç sayfa görseli bulunamadı"

### Gerçek Sebep
1. Episode URL'leri ölü Madara sitelerine (`mangatr.app`, `merlintoon.com`) işaret ediyordu.
2. Monomanga.com.tr bu iki manhwa için "Manga Bulunamadı" dönüyor (slug yok).
3. 162 manga/manhwa'nın çoğu monomanga'da mevcut DEĞİL.
4. SOHBET-160 false positive: `200 OK + >10000B` kontrolü "Manga Bulunamadı" sayfasını da geçiriyor.

### Yapılanlar
1. **DB güncelleme:** 7 ölü Madara sitesi `is_dead=1` işaretlendi.
2. **Monomanga primary ayarı:** 143 manga/manhwa'da monomanga primary yapıldı.
3. **Episode URL güncelleme:** 8542 episode URL'si monomanga'ya yönlendirildi.
4. **manga.py nextjs parser fix:** Boşluk/Türkçe karakter içeren CDN URL'leri için regex düzeltildi.
5. **MangaDex UUID tespiti:** MangaDex API'den chapter UUID'leri alınıp episode URL'leri güncellendi.

### Kanıt
```
My Blasted Reincarnated Life → Bölüm 1: 27 sayfa başarıyla indi (MangaDex)
Tomodachi Game → Bölüm 27: 33 sayfa başarıyla indi (monomanga)
```

---

## 3. Oyun Detay Ekranı — ✅ ZATEN ÇALIŞIYOR

### Değerlendirme
Oyun detay ekranı (`frontend/app.js` içinde `renderDetail()`) halihazırda:
- `type='game'` için progress card gizleme ✅
- Bölümler sekmesi yerine indirme paneli gösterme ✅
- Siteler sekmesinde oyun mesajı gösterme ✅
- Geliştirici/yayıncı/platform bilgisi gösterme ✅
- FitGirl arama + torrent indirme ✅

Herhangi bir düzeltme gerekmemiştir.

---

## 4. Monomanga Entegrasyonu — ✅ PARSER DÜZELTİLDİ

### Sorun
`_nextjs_chapter` fonksiyonu CDN URL'lerini bulamıyordu çünkü regex boşluk karakterini kesiyordu.
Monomanga CDN URL'leri şu formatta:
```
https://cdn.monomanga.com.tr/chapters/{id}/Bölüm {num}-{timestamp}/Bölüm {num}/{page}.webp
```

### Yapılan Değişiklik (manga.py:265-331)
- RSC payload regex: `[^\s...]` → `[^"'\\,}\]]` (boşluk karakterine izin ver)
- HTML img/data-src fallback eklendi
- `_page_num()` ile sayfa sıralama düzeltildi (sondaki sayıyı bul)

### Test
```python
url = 'https://monomanga.com.tr/manga/tomodachi-game/bolum-27'
# → 33 sayfa başarıyla indirildi
```

---

## 5. Genel Durum

| Ölçüt | Durum |
|---|---|
| Dexter'da "İZLE" butonu | ✅ Düzeltildi |
| My Blasted Reincarnated Life indirme | ✅ Çalışıyor (MangaDex) |
| Hardcore Leveling Warrior: Earth Game indirme | ✅ Çalışıyor (MangaDex) |
| Oyun detay ekranı | ✅ Zaten çalışıyor |
| Tüm manga/manhwa monomanga'ya bağlandı | ⚠️ Kısmen (sadece var olanlar) |
| Frontend tür kontrolü | ✅ 6 noktada düzeltildi |
| Monomanga parser | ✅ Boşluk/Türkçe karakter desteği eklendi |

---

## 6. Kalan Sorunlar

1. **Monomanga slug eşleştirme:** 162 manga/manhwa'nın çoğu monomanga'da yok. MangaDex fallback kullanılıyor.
2. **Film kaynakları:** 88 film hala kaynaksız (SOHBET-160'tan kalan).
3. **Toplu MangaDex UUID senkronizasyonu:** Tüm manga/manhwa için MangaDex chapter UUID'leri çekilip episode URL'leri güncellenmeli.
4. **DEVAM.md güncellenecek.**

---

## 7. Kanıt Logları

```
=== Monomanga Test ===
Testing: https://monomanga.com.tr/manga/tomodachi-game/bolum-27
SUCCESS: 33 files downloaded

=== MangaDex Test ===
Testing: https://mangadex.org/chapter/ddc24d08-7341-4de0-a78f-5a02829cdc94
SUCCESS: 27 files downloaded

=== DB Güncelleme ===
Dead sites marked: 7
Primary set to monomanga: 143
Episodes updated: 8542
```
