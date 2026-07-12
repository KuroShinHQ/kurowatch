# SOHBET-146 — HDFILMCEHENNEMİ Domain Güncellemesi (107 Film)

**Tarih:** 12 Temmuz 2026  
**Hedef:** 107 hdfilmcehennemi.now kaynaklı film hatasını otomatik çözmek  
**Yöntem:** .now search API ile doğru slug'ları bul, domain değiştir  

---

## Yapılan İşlemler

### 1. Domain Araştırması
- hdfilmcehennemi.**now** hala çalışıyor (homepage 200, search çalışıyor)
- hdfilmcehennemi.**nl** farklı URL yapısı kullanıyor: `/{slug}/` (no `/film/` prefix, İngilizce slug)
- .nl site search'i yok, sadece homepage'de 46 film (çoğu 2025-2026 yapımı)

### 2. URL Yapısı Keşfi
- .now film sayfaları: `/film/{turkce-slug}-{yil}-izle-{num}/` formatında
- DB'deki eski URL'ler: `/{slug}-izle/` (yıl yok, `/film/` prefix yok, versiyon yok)
- .now search API ile her film için doğru slug bulundu

### 3. DB Güncellemeleri
| Tablo | İşlem | Sayı |
|---|---|---|
| `episode.url` | `.now` → `.now/film/` (Türkçe yıllı slug) | 297 satır |
| `episode.url` | `.now` → `.nl` (WALL-E, Howl's Moving Castle) | 2 satır |
| `site.site_url` | `.now` → `.now/film/` | 113 satır |
| `site.site_url` | `.nl` base domain fix | 3 satır |

### 4. Bulunamayan Filmler (15)
Koleksiyon/seri filmleri ve niche yapımlar:
- Cem Yılmaz Fundamentals, Corpse Bride, Fetih 1453, Gladio
- I Am Legend, Ice Age (Serisi), Kurtlar Vadisi Irak
- Léon: The Professional, Matrix Serisi, Pacific Rim (Serisi)
- Real Steel, Resident Evil Serisi, Scorpion King Serisi
- Transformers Serisi, Undisputed (Serisi)

---

## Test Sonuçları

| Metrik | SOHBET-145 (Önce) | SOHBET-146 (Sonra) | Değişim |
|---|---|---|---|
| **TOPLAM OK** | 513/714 (%71.8) | **590/714 (%82.6)** | **+77** |
| anime | 317/318 (%99.7) | 317/318 (%99.7) | — |
| series | 2/49 (%4.1) | 20/49 (%40.8) | **+18** |
| movie | 6/113 (%5.3) | 49/113 (%43.4) | **+43** |
| manga | 36/66 (%54.5) | 48/66 (%72.7) | **+12** |
| manhwa | 81/96 (%84.4) | 85/96 (%88.5) | **+4** |
| game | 19/19 (%100) | 19/19 (%100) | — |

---

## Kalan 124 Hatanın Analizi

| Kaynak | Adet | Durum |
|---|---|---|
| **setfilmizle.uk** | 45 | URL şeması değişti, eski slug'lar eşlenemiyor |
| **dizipod.com** | ~10 | Tamamen ölü site |
| **hdfilmcehennemi.now** (bulunamayan) | ~15 | Koleksiyon/niche filmler, .now'da yok |
| **ragnarscans.net** (CF) | ~18 | Cloudflare JS challenge |
| **asurascans.com.tr** (403) | ~5 | Anti-bot engeli |
| **turkanime** (525) | 1 | SSL hatası |
| **diğer** | ~30 | Çeşitli (dead/blocked) |

---

## Kullanılan Scriptler
- `_sohbet146_migrate.py` — Ana migrasyon: .now search ile doğru slug bulma
- `_verify_matches.py` — Doğrulama: yanlış eşleşen URL'leri geri alma
- `_fix_site_urls.py` — Site URL'lerini episode'daki doğru slug ile güncelleme
- `_fix_remaining2.py` — Kalan hdfilmcehennemi.site entry'lerini toplu düzeltme
- `_fix_www.py` — www.www. çiftleme hatasını düzeltme

---

## Temel Bulgular
1. hdfilmcehennemi.**now** HALA ÇALIŞIYOR — sadece URL yapısı değişmiş
2. .now film sayfaları `/film/{slug}/` formatına geçmiş (önceden direkt `/{slug}/`)
3. Slug'lar Türkçe ve yıl/sürüm numarası içeriyor (örn. `esaretin-bedeli-1994-izle-2`)
4. .now search API (`/?s={title}`) çalışıyor ve doğru sonuç döndürüyor
5. hdfilmcehennemi.**nl** farklı bir site — çoğu klasik film mevcut değil
6. .nl Cloudflare koruması altında (HEAD 403, GET 200)

---

## Sonuç
**HDFILMCEHENNEMİ 107 film hatası %100 çözülemedi ama %72'ye düşürüldü (107 → 30).**
Kalan 30 hdfilmcehennemi.now hatası collection/niche filmler — .now'da karşılıkları yok.
Genel başarı oranı %71.8 → %82.6'ya yükseldi.
