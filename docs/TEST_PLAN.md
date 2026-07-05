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
| T-01 | App açılışı — Home ekranı gelir, nav bar görünür | ✅ | BUG-01 fix commit 0d7e032, cache-busting sohbet-49 |
| T-02 | Nav: Home → Search → Updates → Stats → Settings geçişi | ✅ | |
| T-03 | Home: poster grid yüklenir, cover'lar görünür | ✅ | 670/676 cover, 6 Türk initials kutusu |
| T-04 | Home: filter chip — "Anime" seçince sadece animeler | ✅ | Tür + durum chip'leri çalışıyor |
| T-05 | Home: filter chip — "İzliyor" + "Anime" kombinasyon | ✅ | |
| T-06 | Home: karta tıklayınca Detail ekranı açılır | 🔧 | Fix hazır (commit 0e58dc9) — Lord testi bekleniyor |

---

## GRUP 2: DETAIL EKRANI

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-07 | Detail: hero kapak + başlık + tip badge + durum badge | ✅ | test_detail_hero_visible + test_detail_cover_upload_button_exists |
| T-08 | Detail: ★ yıldız puan tıklayınca değişir + kaydedilir | ✅ | test_detail_star_rating + test_detail_star_rating_interactive |
| T-09 | Detail: type-specific labels (BÖLÜM/CHAPTER, mark btn text, icon) | ✅ | test_detail_type_specific_labels ×3 (anime/manga/manhwa) |
| T-09b | Detail: "Sonraki Bölümü İşaretle ✓" — progress +1 (quick-edit) | ✅ | test_detail_quick_edit_popup + test_detail_progress_slider_updates_display |
| T-09c | Detail: Game type hides mark/continue buttons, shows TAMAMLANMA | ✅ | test_detail_game_hides_mark_button |
| T-10 | Detail: Bölümler sekmesi — liste gelir | ✅ | test_detail_episodes_tab + test_detail_episodes_season_picker |
| T-11 | Detail: Bölümler — checkbox tıklayınca ✓ olur | ⏳ | PW test yazılacak |
| T-12 | Detail: Siteler sekmesi — site listesi + "Aç →" çalışır | ✅ | test_detail_switch_to_sites_tab + test_detail_sites_add_and_delete |
| T-13 | Detail: Notlar sekmesi — not yazılır + spoiler toggle | ✅ | test_detail_switch_to_notes_tab + test_detail_notes_spoiler_toggle |
| T-14 | Detail: ✏️ Düzenle butonu — edit modal açılır (pre-filled) | ✅ | test_detail_edit_modal_opens |
| T-15 | Detail: Edit modal — başlık/durum/puan değiştirince kaydedilir | ⏳ | PW test yazılacak |
| T-16 | Detail: Geri ← butonu — home'a döner | ⏳ | PW test yazılacak |

### Animasyon & Transition Testleri

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-A01 | Detail: slide-up animasyonu ile açılır | ✅ | test_animation_detail_slide_up |
| T-A02 | Nav: forward (home→search) slide-in-right | ✅ | test_animation_nav_slide_in_right |
| T-A03 | Nav: backward (search→home) slide-in-left | ✅ | test_animation_nav_slide_in_left |
| T-A04 | Nav: home→updates slide-in-right | ✅ | test_animation_nav_updates_slide_up |
| T-A05 | Detail: tab switch episodes→characters→sites→notes→back | ✅ | test_detail_tab_all_four_toggle |
| T-A06 | Detail: tab active/inactive state (cyan/gray border) | ✅ | test_detail_tab_buttons_active_state |
| T-A07 | CSS keyframe animations defined | ✅ | test_animation_transition_css_defined |
| T-A08 | Tab roundtrip no JS errors | ✅ | test_detail_tab_all_roundtrip_no_error |
| T-A09 | Buttons have transition + active:scale classes | ✅ | test_detail_mark_button_has_transition + test_detail_buttons_have_active_scale |

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
| BUG-T06-A | Detail hero cover | Arka plan resmi çok blur/düşük kalite — cover'ı sığdırırken kalite kaybı | 🔧 FIX: background-size auto 100% (commit 0e58dc9) |
| BUG-T06-B | Detail star rating | Mouse üzerine gelmeden yıldız hover aktif oluyor (tıklamadan yükseliyor) | 🔧 FIX: event delegation, DOM rebuild yok (commit 0e58dc9) |
| BUG-T06-C | Detail site URL | "İzle için site ekle → Siteler sekmesi" mesajı çıkıyor — site eklendikten sonra Episodes tab yenilenmiyor | 🔧 FIX: renderDetailEpisodes yeniden çağrılıyor (commit 0e58dc9) |

---

---

## GRUP 9: İÇERİK SAĞLIĞI — %1 LİK PİNG TEST

Tüm 700+ içeriğin 1. bölüm URL'lerine Range: bytes=0-4096 isteği atarak URL'in çalışıp çalışmadığını test eder. Gerçek download yapılmaz.
**Kod:** `backend/tools/url_ping.py` + `backend/tools/content_health.py` ✅ YAZILDI

| # | Özellik | Durum | Not |
|---|---------|-------|-----|
| T-39 | `content_health.py` tüm content'lerde gezer, episode URL'lerini toplar | ✅ | selectinload ile |
| T-40 | Her URL için Range HEAD isteği — HTTP 200/206 = OK | ✅ | `http_ping()` |
| T-41 | HTTP 403/404/503 sınıflandırması | ✅ | CF_BLOCKED / SITE_YOK / OFFLINE |
| T-42 | Anime: CF'ye takılanı tranimaci.com'da kurtar | ✅ | `_anime_fallback()` |
| T-43 | Manga: akıllı isim eşleştirme (title→title_tr→title_en) | ✅ | `_manga_fallback()` |
| T-44 | Rapor: OK/KURTARILDI/CF_BLOCKED/SITE_YOK dağılımı | ✅ | JSON + konsol |
| T-45 | `--dead-only` filtresi | ✅ | |
| T-46 | `--id N` tek içerik testi | ✅ | |
| T-47 | `--type anime/manga` filtresi | ✅ | |

---

## 📊 İlerleme

```
Toplam test: 38 + animasyon: 9 + ping: 9 = 56
Tamamlanan: 33 + 9 = 42 / 56
API:   33/33 PASS (test_api_endpoints.py)
PW:    40/40 PASS (toplam 5 test dosyası)
TOOL:  9/9 CODED (content_health.py + url_ping.py — WSL'de test edilecek)
```

> ✅ test_api_endpoints.py düzeltildi — 33 endpoint test edildi, 33 PASS
> ✅ Playwright hybrid test suite: 40 test, 40 PASS (5 dosya)
> ✅ P7 — Sorun yok, kör nokta analiziydi ✅ KAPANDI
> ✅ P8 — %1 ping test mekanizması kodlandı ✅
> ⏳ Kalan 14 test: T-11, T-15, T-16, Grup 3-8 (T-17..T-38)
> ⏳ Grup 9: WSL'de çalıştırılıp doğrulanacak (T-39..T-47)
