# 🧪 KuroWatch Sistematik Test Planı
**Başlangıç:** 20 Haziran 2026 · **Metot:** Claude talimat → Lord dener → feedback → fix/pass

> Durum: ✅ PASS | ❌ BUG | ⏳ TEST BEKLİYOR | 🔧 FIX YAPILIYOR | ⏭️ ATLANDI

---

## Test Metodolojisi

```
1. Claude: "TEST-XX: [özellik]. Yap: [adımlar]. Beklenen: [sonuç]"
2. Lord:    KuroWatch'ta dener, ne olduğunu söyler
3. Claude:  ✅ PASS → sonraki teste geç
           ❌ BUG → kodu incele, fix yaz, "fix hazır, tekrar dene"
```

---

## GRUP 1: TEMEL NAVIGASYON & GÖRÜNÜM

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-01 | App açılışı — Home ekranı gelir, nav bar görünür | 🔧 | BUG-01: sidebar lg'de aktifti → bottom-nav her ekran fix (commit 0d7e032) |
| T-02 | Nav: Home → Search → Updates → Stats → Settings geçişi | ⏳ | T-01 fix sonrası doğrula |
| T-03 | Home: poster grid yüklenir, cover'lar görünür | ✅ | |
| T-04 | Home: filter chip — "Anime" seçince sadece animeler | ⏳ | |
| T-05 | Home: filter chip — "İzliyor" + "Anime" kombinasyon | ⏳ | |
| T-06 | Home: karta tıklayınca Detail ekranı açılır | ⏳ | |

---

## GRUP 2: DETAIL EKRANI

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-07 | Detail: hero kapak + başlık + tip badge + durum badge | ⏳ | |
| T-08 | Detail: ★ yıldız puan tıklayınca değişir + kaydedilir | ⏳ | |
| T-09 | Detail: "Sonraki Bölümü İşaretle ✓" — progress +1 | ⏳ | |
| T-10 | Detail: Bölümler sekmesi — liste gelir | ⏳ | |
| T-11 | Detail: Bölümler — checkbox tıklayınca ✓ olur | ⏳ | |
| T-12 | Detail: Siteler sekmesi — site listesi + "Aç →" çalışır | ⏳ | |
| T-13 | Detail: Notlar sekmesi — not yazılır + kaydedilir | ⏳ | |
| T-14 | Detail: ✏️ Düzenle butonu — edit modal açılır | ⏳ | |
| T-15 | Detail: Edit modal — başlık/durum/puan değiştirince kaydedilir | ⏳ | |
| T-16 | Detail: Geri ← butonu — home'a döner | ⏳ | |

---

## GRUP 3: İÇERİK EKLEME

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-17 | Add Modal: + butonu açar | ⏳ | |
| T-18 | Add Modal: arama kutusu — AniList/IGDB sonuçları gelir | ⏳ | |
| T-19 | Add Modal: sonuç seçince form otomatik dolar | ⏳ | |
| T-20 | Add Modal: "Manuel Ekle" linki — boş form gelir | ⏳ | |
| T-21 | Add Modal: site ekle satırı — ad + URL girilir | ⏳ | |
| T-22 | Add Modal: Kaydet — içerik DB'ye eklenir, home'a döner | ⏳ | |

---

## GRUP 4: ARAMA

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-23 | Search: kutuya yazınca kütüphanede anlık filtre | ⏳ | |
| T-24 | Search: Keşfet sekmesi — AniList sonuçları gelir | ⏳ | |
| T-25 | Search: Keşfet — "Ekle +" butonu Add Modal'ı açar | ⏳ | |

---

## GRUP 5: GÜNCELLEMELER

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-26 | Updates: "Şimdi Kontrol Et" butonu — spinner gösterir | ⏳ | |
| T-27 | Updates: Kontrol bitince liste güncellenir | ⏳ | |
| T-28 | Updates: Güncelleme satırına tıklayınca Detail açılır | ⏳ | |

---

## GRUP 6: AYARLAR

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-29 | Settings: "Dışa Aktar" — kurowatch_backup.json indirir | ⏳ | |
| T-30 | Settings: "İçe Aktar" — JSON seçince import olur | ⏳ | |
| T-31 | Settings: IGDB/MAL credentials — kaydedilir, kaybolmaz | ⏳ | |
| T-32 | Settings: Cover zenginleştir butonu — çalışır | ⏳ | |

---

## GRUP 7: İSTATİSTİK

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-33 | Stats: Özet kartları — toplam/kütüphane/ort.puan | ⏳ | |
| T-34 | Stats: Tip dağılımı chart görünür | ⏳ | |
| T-35 | Stats: Durum dağılımı bar chart görünür | ⏳ | |

---

## GRUP 8: BÖLÜM YÜKLEYİCİ & SİTE

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-36 | Detail > Bölümler: "Bölümleri Yükle" butonu — site listesi açar | ⏳ | |
| T-37 | Detail > Siteler: + Site ekle formu açılır | ⏳ | |
| T-38 | Detail > Siteler: URL kaydedilir, listede görünür | ⏳ | |

---

## 🐛 Bulunan Buglar

| Bug # | Özellik | Açıklama | Durum |
|-------|---------|----------|-------|
| — | — | Henüz test başlamadı | |

---

## 📊 İlerleme

```
Toplam test: 38
Tamamlanan: 0 / 38
PASS:  0
BUG:   0
```
