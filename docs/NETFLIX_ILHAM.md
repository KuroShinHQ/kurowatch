# KuroWatch — Netflix İlham Alma & Benzeme Kılavuzu

> Oluşturulma: 23 Haz 2026 · Araştırma kaynakları: GitHub Netflix klonları, DESIGN.md, FEATURE_MAP.md
> Bu dosya KuroWatch frontend'ini Netflix-like hale getirmek için tasarım kararlarını ve uygulama adımlarını belgeliyor.

---

## 1. Stitch AI ile Mevcut Frontend Nasıl Yapıldı

### 1.1 Prompt Stratejisi (2 generation, 8 ekran)

```
BATCH 1 — Standard Mode (1 generation):
  → HOME + DETAIL + SEARCH + UPDATES + STATS
  → 5 ekranı tek promptta ver, canvas gerçek zamanlı render

BATCH 2 — Experimental Mode (1 generation):
  → ADD MODAL + SETTINGS + CONFLICT MODAL
  → Experimental: daha iyi layout ve detay kalitesi

Sonrası (generation SIFIR — sadece canvas manual edit):
  → Renk düzeltmeleri, metin güncellemeleri, spacing tweaks
```

**Stitch dosya konumları:**
```
C:\Kuroshin\kuroshin-downloads\stitch_kurowatch_media_tracker\
  kurowatch_home_refined\code.html        ← HOME (221 KB)
  content_detail_refined\code.html        ← DETAIL
  search_discover_refined\code.html       ← SEARCH
  updates_refined\code.html              ← UPDATES
  library_stats_refined\code.html        ← STATS
  add_content_overlay\code.html           ← ADD MODAL
  archive\code.html                       ← ARCHIVE
  import_conflict_modal\code.html         ← CONFLICT MODAL
  ⚠️ SETTINGS → kurowatch_home_refined içinde gömülü (ayrı dosya yok)
```

### 1.2 Stitch Çıktısının Sorunları ve Çözümleri

| Sorun | Etki | Uygulanan Çözüm |
|---|---|---|
| CDN bağımlılığı (Tailwind CDN + Google Fonts) | Offline tamamen ölür | Local `tailwind.css?v=30` kullanıldı |
| 9 ayrı HTML dosyası | SPA değil, sayfa yenilenerek geçiş | Tek `index.html` — `<section id="screen-*">` |
| Renk tutarsızlığı (Material token drift) | Her ekran farklı bg rengi | `:root { --bg-primary: #0d0d1a; ... }` |
| JavaScript yok | Tüm butonlar statik | `app.js` — navigasyon + event handler |
| Material Icons → Google CDN | Offline çalışmaz | ⚠️ Hâlâ CDN (SVG geçişi bekliyor) |

### 1.3 Stitch Sonrası Yapılan Faz'lar (Faz A-D)

```
FAZ A — Birleştirme:
  ✅ 9 HTML → tek index.html + screen section'ları
  ✅ Tailwind CDN → local build

FAZ B — Navigasyon:
  ✅ app.js: showScreen(id), modal aç/kapat
  ✅ History API (popstate → geri butonu)
  ✅ Bottom nav + PC sidebar

FAZ C — Debug Logger:
  ✅ debug-logger.js: KuroLog overlay (?kurodev=1 veya logo triple-tap)
  ✅ Click/fetch/nav/error interceptor

FAZ D — UX İyileştirmeleri:
  ✅ Loading state + spinner (her async buton)
  ✅ Error banner (network offline algılama)
  ✅ Pull-to-refresh (Updates + Home)
  ✅ Swipe-to-dismiss (bottom sheet)
  ✅ Virtual scroll (Detail → Episodes, 1000+ bölüm için)

Stitch VERİLMEYEN ekranlar (JS-ağır → direkt Claude'la yapıldı):
  ✅ Video Player modal (ambient canvas, PiP, theater, skip intro)
  ✅ Manga Reader (webtoon + sayfa modu, swipe)
  ✅ Downloads ekranı (WS progress, floating UI)
```

---

## 2. Mevcut KuroWatch Renk & Tasarım Sistemi

```css
/* DESIGN.md'den referans — değiştirilmeden bırak */
--bg-primary:    #0d0d1a   /* Netflix: #141414 — bizimki daha koyu, OK */
--bg-card:       #1a1a2e
--accent:        #00d4ff   /* Netflix: #E50914 kırmızı — biz cyan kullanıyoruz */

/* Tip renkleri */
--color-anime:   #00d4ff   /* cyan */
--color-manga:   #ffd9a1   /* sarı-krem */
--color-manhwa:  #bbc5eb   /* açık mor */
--color-game:    #ffb4ab   /* pembe */
```

**KuroWatch kimliği:** Netflix kırmızısı değil — **derin koyu lacivert + cyan** paleti.
Netflix'e benzerken bu kimliği koruyacağız.

---

## 3. Netflix UI Pattern Kataloğu (GitHub Araştırması)

> Kaynak: github.com/Aj7Ay/Netflix-clone, github.com/prajjaldhar/netflix_clone, CSS-Tricks

### Pattern 1: Hero Banner (Billboard)

Netflix davranışı:
- Sayfa üstü tüm ekran (55vh) — son izlenen veya öne çıkan içerik
- Kapak görseli arka plan, ağır siyah gradient overlay (alt + yanlar)
- Büyük başlık + özet + 2 buton: "▶ Oynat" + "ℹ Daha Fazla"

KuroWatch uyarlaması:
```
Hedef: son my_progress > 0 olan içerik → Hero olarak göster
Başlık: "Kaldığın Yerden Devam Et"
Buton 1: "▶ Devam Et → Bölüm {N}" → openDetail(id, tab=episodes)
Buton 2: "ℹ Detay" → openDetail(id)

CSS:
  .hero-banner {
    height: 55vh;
    background: url({cover_url}) center/cover no-repeat;
    position: relative;
  }
  .hero-banner::after {
    content: '';
    position: absolute; inset: 0;
    background: linear-gradient(
      to top, #0d0d1a 0%, transparent 50%,
      rgba(13,13,26,0.4) 100%
    );
  }

Dikkat: cover_url dikey poster (2:3) → Hero için yatay/geniş görsel lazım.
Geçici çözüm: dikey poster kullan, object-position: top center ile kırp.
```

### Pattern 2: Yatay Kategori Row'ları

Netflix davranışı:
- Her kategori için ayrı yatay kaydırma satırı
- Başlık: "Devam Ettiğiniz" / "Sizin için" / "Popüler"
- Ok butonları (◀ ▶) veya swipe

KuroWatch uyarlaması:
```
Row listesi (öncelik sırasına göre):
  1. "Devam Ediyorum"   → status=watching, my_progress>0
  2. "Planlıyorum"      → status=planning
  3. "Anime"            → type=anime
  4. "Manga"            → type=manga
  5. "Manhwa"           → type=manhwa
  6. "Tamamlananlar"    → status=completed

CSS:
  .content-row {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scrollbar-width: none; /* Firefox */
    -ms-overflow-style: none;
    padding-bottom: 4px;
  }
  .content-row::-webkit-scrollbar { display: none; }

  .content-row .card {
    flex-shrink: 0;
    width: 140px;       /* mobil */
    scroll-snap-align: start;
  }
  @media (min-width: 768px) { .content-row .card { width: 180px; } }
  @media (min-width: 1280px) { .content-row .card { width: 220px; } }

API:
  GET /api/content?status=watching   → "Devam Ediyorum" row
  GET /api/content?type=anime        → "Anime" row
  (Tüm endpoint'ler mevcut — sadece UI değişecek)

Mevcut grid → row geçişi:
  Büyük mimari değişiklik: #home-library-grid CSS sınıfları değişmeli
  + renderHome() fonksiyonu her kategori için ayrı section render etmeli
```

### Pattern 3: Card Hover Preview (Expand)

Netflix davranışı:
- Hover → kart büyür (scale 1.15-1.25), overlay bilgi gösterir
- Komşu kartlar yanlamasına kayar
- Trailer otomatik oynar (opsiyonel)
- Expanded card: başlık, puan, özet (kısa), "▶ İzle" + "+ Liste" butonları

KuroWatch uyarlaması:
```
Mevcut: scale(1.02) + cyan border
Hedef: scale(1.15) + translateY(-10px) + shadow + bilgi overlay

CSS:
  .content-card:hover {
    transform: scale(1.15) translateY(-10px);
    z-index: 10;
    transition: transform 300ms ease, box-shadow 300ms ease;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6);
  }

  /* Hover'da görünen bilgi katmanı */
  .card-hover-info {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    background: linear-gradient(to top, #1a1a2e 0%, transparent 100%);
    padding: 12px 8px 8px;
    transform: translateY(100%);
    transition: transform 200ms ease;
    pointer-events: none;
  }
  .content-card:hover .card-hover-info {
    transform: translateY(0);
  }

  /* Komşu kart kayması (opsiyonel — layout shift risk) */
  .content-card:hover ~ .content-card {
    transform: translateX(25%);
  }

Hover bilgi içeriği:
  - Başlık (truncate)
  - ★X.X puan
  - İlerleme bar (my_progress / total_episodes)
  - "▶ Devam Et" butonu (küçük, primary)

Dikkat: overflow:hidden olan parent container hover'ı kırıyor.
Row'da overflow-x:auto varsa z-index overflow çalışmaz.
Çözüm: overflow:clip yerine clip-path kullan veya
        hover'da position:fixed portal ile render et.
```

### Pattern 4: "Devam Et" Row (Progress Row)

Netflix davranışı:
- "Kaldığın Yerden Devam Et" satırı
- Her kart alt kısmında renkli progress bar
- Son izlenen bölüm gösterir

KuroWatch uyarlaması:
```
Query: SELECT * FROM content WHERE my_progress > 0 AND status = 'watching'
API: GET /api/content?status=watching
Zaten mevcut → sadece UI değişecek

Kart üzerinde progress bar:
  .card-progress-bar {
    position: absolute; bottom: 0; left: 0; right: 0;
    height: 3px;
    background: rgba(255,255,255,0.1);
  }
  .card-progress-bar-fill {
    height: 100%;
    background: var(--accent); /* #00d4ff */
    width: calc(var(--progress-pct) * 1%);
  }
```

### Pattern 5: Dark Tema (Zaten Var)

```
Netflix:   #141414 bg, #E50914 kırmızı
KuroWatch: #0d0d1a bg (daha koyu), #00d4ff cyan

Değişiklik YOK — KuroWatch zaten Netflix'ten daha koyu ve aynı dark hissiyatta.
```

---

## 4. KuroWatch → Netflix Dönüşüm Aşamaları

### Aşama 1 — Card Hover Genişletme (Kolay, ~2 saat)

Değişen dosyalar: `frontend/style.css`, `frontend/index.html`
Risk: Düşük (sadece CSS değişikliği)

```
Mevcut: scale(1.02), cyan border
Hedef:  scale(1.15) + translateY(-10px) + bilgi overlay
- style.css: .content-card:hover güncelle
- index.html: her karta .card-hover-info div ekle
- Overflow çakışmasını çöz (clip-path veya z-index yönetimi)
```

### Aşama 2 — Yatay Row Sistemi (Orta, ~1 gün)

Değişen dosyalar: `frontend/app.js` → renderHome(), `frontend/style.css`
Risk: Orta (renderHome() büyük refactor)

```
Adımlar:
1. renderHome() → her kategori için renderRow(title, params) helper
2. Row sırası: Devam Ediyorum → Planlıyorum → Anime → Manga → Manhwa
3. .home-library-grid → .content-rows (flexbox yerine row stack)
4. Her row: başlık + yatay scroll container + kartlar
5. Filtre chip'leri kalsın (row'ların üstünde, type filtresi row'u gizler/gösterir)
```

### Aşama 3 — Hero Banner (Büyük, ~0.5 gün + tasarım kararı)

Değişen dosyalar: `frontend/index.html` (#screen-home), `frontend/app.js`, `frontend/style.css`
Risk: Orta (yeni API çağrısı + cover boyut sorunu)

```
Adımlar:
1. renderHero() → son watching içeriği çek (GET /api/content?status=watching&limit=1)
2. #home-hero section'ı ekle (index.html'nin üstüne)
3. CSS: 55vh, bg-cover, gradient overlay
4. CTA butonlar: "Devam Et" + "Detay"
5. Cover boyutu: dikey poster (2:3) → object-position: top center ile adapt

NOT: AniList'ten yatay/banner görsel alınabilir mi araştır.
     AniList bannerImage field'ı var → zaten çekiliyor mu kontrol et.
```

### Aşama 4 — Stitch ile Yeni HOME Tasarımı (İsteğe Bağlı)

```
Eğer Stitch'e tekrar gidilirse:
  Prompt: "Netflix-style dark media tracker, yatay row'lar, hero banner, 
           cyan accent #00d4ff, bg #0d0d1a, thumbnail kartlar 2:3 ratio"
  Mod: Experimental (tek ekran = daha kaliteli)
  Generation: 1 (sadece HOME)
  
Post-Stitch pipeline (aynı):
  1. Tailwind CDN → local tailwind.css
  2. JS yok → app.js entegrasyonu
  3. Renk drift → :root değişkenleriyle normalize
```

### Aşama 5 — Trailer Preview (İsteğe Bağlı, Düşük Öncelik)

```
AniList API: trailer { id, site } field'ı var (YouTube ID)
URL: https://www.youtube.com/embed/{id}?autoplay=1&muted=1

Hover'da video oynat:
  - Card expand sırasında <iframe> inject et
  - autoplay policy: muted + user gesture (hover yeterli DEĞİL olabilir)
  - Teknik risk: tarayıcı autoplay bloklayabilir
  - Fallback: trailer yoksa statik kapak göster
  
Şimdilik ATLA — Aşama 1-3 daha kritik.
```

---

## 5. GitHub Referansları

| Repo | Neden İlginç | URL |
|---|---|---|
| Aj7Ay/Netflix-clone | Portal hover preview tekniği, RTK Query | github.com/Aj7Ay/Netflix-clone |
| prajjaldhar/netflix_clone | Vanilla JS+CSS, framework bağımsız | github.com/prajjaldhar/netflix_clone |
| notramm/Netflix-UI-Clone | Pure CSS — hover expand CSS trick | github.com/notramm/Netflix-UI-Clone |
| CSS-Tricks makalesi | translateX(25%) siblings tekniği | css-tricks.com/netflix-animation-css |

---

## 6. Kritik Kararlar (Uygulamadan Önce Netleştir)

```
[?] Yatay row sistemi: Mevcut filtre chip'leri ile birlikte mi yoksa yerine mi?
    → Öneri: Row'lar varsayılan, filtre chip'leri ek (her ikisi kalsın)

[?] Hero banner görsel: Dikey poster mi, yoksa AniList bannerImage mı?
    → AniList bannerImage field'ı var, anime.bannerImage URL döndürüyor
    → Eğer DB'de saklanmıyorsa önce storage çözülmeli

[?] Grid → Row geçişi geri alınabilir mi?
    → Evet: CSS class toggle ile (--layout-mode: grid|rows) yapılabilir
    → Settings'e "Görünüm: Grid / Satır" toggle eklenebilir

[?] Overflow + z-index: hover expand'de kırılıyor mu?
    → Test et: yatay scroll container içinde scale hover'ı
    → Sorun varsa: hover'da card'ı fixed position'a al (portal pattern)
```

---

## 7. Öncelik Sırası

```
1. [YÜKSEK] Card hover genişletme (Aşama 1) — 2 saat, düşük risk
2. [ORTA]   Yatay row sistemi (Aşama 2) — 1 gün, renderHome refactor
3. [ORTA]   Hero banner (Aşama 3) — 0.5 gün, bannerImage araştırması şart
4. [DÜŞÜK]  Stitch ile yeni HOME (Aşama 4) — sadece büyük redesign kararı alınırsa
5. [ÇOK DÜŞÜK] Trailer preview (Aşama 5) — autoplay policy sorunları riski
```
