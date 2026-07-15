# SOHBET-156 Raporu: Tüm Türkçe Sitelerin Durum Keşfi + Alternatifler

**Tarih:** 2026-07-13
**Kapsam:** 37 domain, 1699 site kaydı, 714 içerik

## Özet

| Kategori | Durum |
|----------|-------|
| 37 domain tarandı | 9 alive, 7 CF blocked, 16 dead, 2 İngilizce, 3 bilinmiyor |
| 1699 site kaydı güncellendi | 202 alive, 1488 dead (yeni işaretlenen) |
| Alternatif siteler test edildi | 10 alive, 1 CF, 6 dead |

## Domain Discovery Sonuçları

### ✅ ALIVE (9 domain)
| Domain | HTTP Durumu | Not |
|--------|-------------|-----|
| dizipod.com | 200 | Site açık ama dizi içerikleri yok |
| golgebahcesi.com | 200 | Manga sitesi |
| mangatr.app | 200 | **Domain satılık** (içerik yok) |
| mangawow.org | 200 | Manga sitesi |
| monomanga.com.tr | 200 | Next.js manga (JS render gerekli) |
| tranimaci.com | 200 | CF PoW challenge (stream bypass başarısız) |
| www.hdfilmcehennemi.nl | 200 | Film sayfaları 404 (URL yapısı değişmiş) |
| www.majorscans.com | 200 | Manga sitesi |
| www.ruyamanga2.com | 200 | Manga sitesi |
| www.setfilmizle.uk | 200 | Dizi içerikleri kaldırılmış |

### 🔒 CF BLOCKED (7 domain)
| Domain | HTTP | Not |
|--------|------|-----|
| asurascans.com.tr | 403 | Cloudflare |
| hayalistic.blog | 403 | Cloudflare |
| manga-sehri.net | 403 | Cloudflare |
| mangasehri.net | 403 | Cloudflare |
| merlintoon.com | 403 | Cloudflare |
| ruyamanga.net | 403 | Cloudflare |
| www.ruyamanga.net | 403 | Cloudflare |

### ❌ DEAD (16 domain)
arcanescans.com, diziwatch.net, hayalistic.com.tr, mangakoleji.com, mangatepesi.com, mangatr.me, mangawow.com, manhwahentai.me, merlinscans.com, ragnarscans.net, tempestfansub.com, turkcemangaoku.com, turkmanga.com.tr, w2.thegreatestestatedeveloper.site, www.dizibox.so, www.tranimaci.com

## Alternatif Site Test Sonuçları

### Anime
| Site | Durum | URL |
|------|-------|-----|
| **Anizm (tranimeizle.org.tr)** | ✅ **ALIVE** | https://tranimeizle.org.tr/naruto-1-bolum-izle |
| **OpenAnime** | ✅ **ALIVE** | https://openani.me/ |
| **AniTurk** | ✅ **ALIVE** | https://www.aniturk.co/ |
| turkanime.co | ❌ HTTP 525 | Sunucu hatası |
| animexe.com | ❌ HTTP 500 | Sunucu hatası |

### Film
| Site | Durum | URL |
|------|-------|-----|
| **hdfilmcehennemi.io** | ✅ **ALIVE** | https://www.hdfilmcehennemi.io/ |
| **hdfilmcehennemi.sh** | ✅ **ALIVE** | https://www.hdfilmcehennemi.sh/ |
| **hdfilmcehennemi.net** | ✅ **ALIVE** | https://www.hdfilmcehennemi.net/ |

### Dizi
| Site | Durum | URL |
|------|-------|-----|
| **dizimag.com.tr** | ✅ **ALIVE** | https://www.dizimag.com.tr/ |
| dizibox.vip | 🔒 CF 403 | Cloudflare |
| netdizi.live | ❌ SSL | Geçersiz sertifika |
| roketdizi.com | ❌ Timeout | 10s yanıt yok |

### Manga/Manhwa
| Site | Durum | URL |
|------|-------|-----|
| **monomanga.com.tr** | ✅ **ALIVE** | https://monomanga.com.tr/ |
| **mangawow.org** | ✅ **ALIVE** | https://mangawow.org/ |
| majorscans.com | ⚠️ Kısa yanıt | HTTP 200 ama içerik yok |

## DB Güncelleme İstatistikleri

| İşlem | Sayı |
|-------|------|
| Dead DNS işaretlenen | 1.074 site |
| CF blocked işaretlenen | 326 site |
| Domain-for-sale işaretlenen | 80 site |
| **Toplam dead işaretlenen** | **1.480 site** |
| **Kalan alive site** | **202** |
| Toplam içerik | 714 |

## Kritik Bulgular

### 1. Anime: tranimaci.com CF PoW → Alternatif var
- `tranimaci.com` HTTP 200 ama CF PoW challenge → stream bypass edilemiyor
- **Alternatif:** `tranimeizle.org.tr` (Anizm) HTTP 200, 378KB HTML, full anime sitesi
- **Alternatif 2:** `openani.me` HTTP 200, 176KB HTML
- **Alternatif 3:** `aniturk.co` HTTP 200, 5KB HTML

### 2. Film: hdfilmcehennemi.nl URL yapısı değişmiş
- Eski pattern: `/film/{slug}-izle-2/` → 404
- Yeni pattern tespit edilemedi (test edilen 3 farklı pattern 404 döndü)
- **Alternatif:** `hdfilmcehennemi.io`, `.sh`, `.net` — hepsi HTTP 200, 213KB HTML

### 3. Dizi: setfilmizle.uk içeriksiz → Alternatif var
- setfilmizle.uk HTTP 200 ama tüm dizi içerikleri kaldırılmış
- **Alternatif:** `dizimag.com.tr` HTTP 200, 125KB HTML, Dexter sayfası var

### 4. Manga/Manhwa: Tüm Madara siteleri ölü/CF
- mangatr.app: domain satılık
- mangasehri.net, manga-sehri.net: CF 403
- merlintoon.com: CF 403
- ragnarscans.net: 404
- **Mevcut çalışan:** monomanga.com.tr (Next.js JS render), mangawow.org
- **MangaDex** (İngilizce) hâlâ en güvenilir kaynak

### 5. Cartoon: Tüm siteler ölü
- www.tranimaci.com (cartoon subdomain): DNS çözülmüyor
- yabancidizi.pro: timeout/unknown
- **Alternatif bulunamadı**

## Öneriler

### Kısa Vade (Hemen Yapılacak)
1. ~~Ölü siteleri DB'de işaretle~~ ✅ (1.480 site işaretlendi)
2. Anime içeriklere Anizm (tranimeizle.org.tr) ekle
3. Film içeriklere hdfilmcehennemi.io/.sh/.net ekle
4. Dizi içeriklere dizimag.com.tr ekle

### Orta Vade
5. monomanga.com.tr için downloader yaz (Next.js scraping)
6. MangaDex ID'lerini DB'ye ekle (birincil manga/manhwa kaynağı)
7. tranimaci.com CF bypass (Playwright selektor güncelleme)

### Uzun Vade
8. Yeni cartoon kaynağı bul
9. hdfilmcehennemi.nl yeni URL pattern'ini keşfet
10. Cloudflare siteleri için curl_cffi impersonate iyileştirmesi

## Scriptler

- `backend/scripts/sohbet156_discovery.py` — Domain HTTP check
- `backend/scripts/sohbet156_alt_finder.py` — Alternatif site test
- `backend/scripts/sohbet156_update_db.py` — DB güncelleme (is_dead)

## JSON Çıktılar

- `docs/sohbet156_discovery.json` — Tüm domain durumları
- `docs/sohbet156_alts.json` — Alternatif site test sonuçları
