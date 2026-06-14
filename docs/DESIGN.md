# KuroWatch — DESIGN.md (Stitch AI Prompt Taslağı)

> Bu dosya Stitch AI'a verilecek prompt içindir.
> Soru-cevap tamamlandıktan sonra "## Stitch AI Final Prompt" bölümü doldurulacak.

---

## Doldurulacak Sorular (Yanıt Bekleniyor)

| # | Soru | Yanıt |
|---|---|---|
| 1 | Genel tema? | _(dark / glassmorphism / amoled+neon)_ |
| 2 | Ana ekran düzeni? | _(grid / liste / karma)_ |
| 3 | İçerik tipi renk ayrımı? | _(evet-aksan / ikon-yeterli / hayır)_ |
| 4 | Navigasyon tipi? | _(alt tab bar / sol sidebar / top nav)_ |
| 5 | Kart tasarımı? | _(kapak büyük / yatay küçük kapak / sadece yazı)_ |
| 6 | Puan gösterimi? | _(yıldız / sayısal 10 üzerinden / her ikisi)_ |
| 7 | Progress bar? | _(evet bölüm/saat / hayır)_ |
| 8 | Yeni bölüm badge? | _(+N site adı / sadece nokta / renk değişimi)_ |
| 9 | Arama/filtre yeri? | _(üstte sabit bar / arama ikonuna tıkla / her ikisi)_ |
| 10 | Vurgu rengi? | _(cyan / mor / turuncu / kırmızı)_ |

---

## Ekranlar (Planlanan)

```
1. Ana Ekran (Home)
   - Yeni bölüm gelenler bölümü (hero veya liste)
   - Devam eden izleme/okuma listesi
   - Tip filtresi: Tümü / Anime / Manga / Manhwa / Oyun

2. Arama Ekranı (Search)
   - İsme göre arama
   - Kategoriye/etikete göre filtre
   - Sonuçlarda ekle butonu

3. Detay Ekranı (Content Detail)
   - Kapak + başlık + puan + süre
   - Bölüm listesi (okundu/izlendi işaretle)
   - Siteler (birincil + alternatifler)
   - Kişisel not

4. Profil / İstatistik Ekranı
   - Toplam süre (anime/manga/oyun ayrı)
   - Kategori dağılımı (pasta grafik)
   - Ortalama puan

5. Ayarlar Ekranı
   - Tema seçimi
   - Export / Import butonu
   - Site yönetimi
```

---

## Teknik Kısıtlar (Stitch'e Bildir)

```
- Backend: FastAPI Python, port 8099
- API calls: fetch('/api/...') — relative URL
- Auth: YOK (single user, local app)
- Font: sistem fontları tercihli (Google Fonts import yok — offline çalışmalı)
- Animasyonlar: CSS transition/animation (WebGL yok, hafif olsun)
- PWA: manifest.json + service worker (offline destek)
- Responsive: mobil öncelikli (320px min), tablet (768px), desktop (1280px+)
- Renk değişkenleri: CSS custom properties (--color-bg, --color-accent, vb.)
```

---

## Stitch AI Final Prompt

_(Soru-cevap tamamlandıktan sonra buraya yazılacak)_

```
[HENÜZ DOLDURULMADI]
```
