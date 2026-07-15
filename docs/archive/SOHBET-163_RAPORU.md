# SOHBET-163 — MCP Otomasyon Sistemi Test Raporu
**Tarih:** 14 Temmuz 2026
**Sistem:** OpenCode Skill MCP (kurowatch-automation)
**Test:** 714 içerik toplu HTTP test

---

## 1. Test Sonuçları (run_test_suite)

| Tür | Toplam | HTTP 200 | Hata | Başarı % |
|-----|--------|----------|------|----------|
| anime | 318 | 318 | 0 | **%100.0** |
| manga | 66 | 66 | 0 | **%100.0** |
| manhwa | 96 | 96 | 0 | **%100.0** |
| game | 19 | 19 | 0 | **%100.0** |
| series | 49 | 21 | 28 | **%42.9** |
| movie | 113 | 0 | 113 | **%0.0** |
| **TOPLAM** | **714** | **573** | **141** | **%80.3** |

## 2. Hata Sınıflandırması (classify_errors)

| Hata Türü | Sayı | Açıklama |
|-----------|------|----------|
| HTTP_403 | 107 | Cloudflare / erişim engeli |
| HTTP_404 | 34 | Sayfa bulunamadı |

### Domain Bazında

| Domain | Durum | Sayı | Tür |
|--------|-------|------|-----|
| hdfilmcehennemi.nl | HTTP 403/404 | 94 | movie |
| 720pizle.com | HTTP 403 | 15 | movie |
| hdfilmcehennemi.io | HTTP 403 | 4 | movie |
| setfilmizle.uk | HTTP 404 | 27 | series |
| dizibox.so | HTTP 403 | 1 | series |

## 3. Otomatik Düzeltme (auto_fix)

### CF_BLOCKED → stream_finder.py
- `.now` domain zaten `_CF_SITES` listesinde mevcut (line 55)
- Kod altyapısı hazır, DB verisi güncel değil

### GALLERY_DL_ERROR → manga.py
- manga/manhwa %100 çalışıyor, müdahale gerekmedi

### GAME_DETAIL_ERROR → app.js
- game %100 çalışıyor, müdahale gerekmedi

## 4. Kalan Hatalar (141)

### Film (113) — Çözüm Gerekiyor
- **hdfilmcehennemi.nl** (94 film): NL domain ölü (403). Alternatif `.now` domain'i çalışıyor ancak URL formatı farklı:
  - .nl: `/{english-slug}/`
  - .now: `/film/{turkish-slug}-{year}-izle-{n}/`
- **720pizle.com** (15 film): Domain HTTP 200 döndürüyor ancak film sayfaları 403
- **hdfilmcehennemi.io** (4 film): Domain 403

**Çalışan alternatif domain:**
- `hdfilmcehennemi.now` ✅ HTTP 200 (WordPress, JS-render)
- `hdfc.nl` ✅ HTTP 200 (sınırlı katalog)
- `fullhdfilmizlesene.life` ✅ HTTP 200

**Önerilen çözüm:** Film slug'larının `.now` domain'ine mapping'i için ayrı bir çalışma gerekli (SOHBET-164).

### Series (28) — Çözümsüz
- **setfilmizle.uk** (27): Site kaldırılmış, alternatif bulunamadı
- **dizibox.so** (1): Domain 403

## 5. MCP Sistem Değerlendirmesi

| Araç | Durum | Not |
|------|-------|-----|
| run_test_suite | ✅ Çalıştı | 573/714 sonuçlandı |
| classify_errors | ✅ Çalıştı | Regex tabanlı sınıflandırma |
| auto_fix | ⚠️ Kısmi | Sadece hint veriyor, kod düzeltmez |
| generate_report | ✅ Çalıştı | Bu rapor oluşturuldu |
| commit_and_update | ⏳ Yapılacak | — |

## 6. Sonuç

**Toplam başarı: %80.3 (573/714)**

- ✅ Anime, Manga, Manhwa, Game: %100
- ❌ Series: %42.9 (28 ölü site - setfilmizle.uk)
- ❌ Movie: %0.0 (113 film - domain migrasyonu gerekli)

**%100 hedefi için gerekenler:**
1. 113 filmin `.now` domain'ine taşınması (slug mapping)
2. 28 serinin alternatif kaynak bulunması (veya kaldırılması)

---

_Rapor otomatik oluşturuldu: 2026-07-14_
