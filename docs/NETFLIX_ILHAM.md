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

---

## 8. Stitch AI Mega Prompt — TAM UYGULAMA REVİZYONU

> Oluşturulma: 23 Haz 2026 (sohbet-76) — tüm ekranları kapsayan tek büyük Stitch prompt.
> Bu prompt Stitch AI'ya yapıştırılacak, 12 ekran + overlay tek canvas'ta üretilecek.

```
══════════════════════════════════════════════════════════════════
KUROWATCH — NETFLIX-STYLE ANIME & MANGA TRACKER
Complete App Redesign — 7 Screens + 5 Overlays
══════════════════════════════════════════════════════════════════

DESIGN PHILOSOPHY:
KuroWatch is a personal media tracker (anime, manga, manhwa, games).
Visual identity: deep space darkness + electric cyan. NOT Netflix red.
Every screen feels premium, immersive, content-forward.
Inspiration: Netflix layout logic, with KuroWatch's dark space soul.

══════════════════════════════════════════════════════════════════
DESIGN SYSTEM
══════════════════════════════════════════════════════════════════

COLORS:
  App background:     #0d0d1a   (deep space black)
  Card/section bg:    #1a1a2e   (dark navy)
  Raised elements:    #16213e
  Input fields:       #1c1d37
  Modal bg:           #1a2123
  Reader bg:          #0a0a12

  Primary accent:     #00d4ff   (electric cyan)
  Accent dim:         rgba(0,212,255,0.1)
  Accent border:      rgba(0,212,255,0.3)

  Text primary:       #e1e0ff
  Text muted:         #9090b0
  Text on accent:     #0d0d1a

  Type colors:
    Anime:   #00d4ff   (cyan)
    Manga:   #ffd9a1   (warm cream)
    Manhwa:  #bbc5eb   (soft violet)
    Game:    #ffb4ab   (pink)

  Status colors:
    Watching:   #feb528   (amber)
    Completed:  #22c55e   (green)
    On Hold:    #9090b0   (grey)
    Dropped:    #ef4444   (red)
    Planning:   #00d4ff   (cyan)

TYPOGRAPHY:
  Font: System UI (sans-serif)
  App title: italic bold, cyan gradient
  Screen titles: 20px bold #e1e0ff
  Card titles: 11-13px truncated
  Meta text: 10-12px #9090b0

GLOBAL CHROME:
  TOP APP BAR (mobile, 64px, transparent→#0d0d1a gradient):
    Left: back arrow or hamburger (contextual)
    Center: "KuroWatch" italic bold, cyan gradient text, subtle glow
    Right: avatar 32px circle or context actions

  BOTTOM NAVIGATION (mobile, fixed, 64px, bg #0d0d1a, top border rgba(255,255,255,0.06)):
    6 tabs equally spaced:
    🏠 Home | 🔍 Keşfet | ➕ Ekle | 🔔 Güncel | 📥 İndir | ⚙️ Ayarlar
    Active: #00d4ff color + 3px top glow bar + label below icon
    Inactive: #9090b0 + label
    Ekle (center): slightly raised, cyan circle bg rgba(0,212,255,0.12)

  PC SIDEBAR (left, 240px, bg #0d0d1a, border-right rgba(255,255,255,0.06)):
    Top: KuroWatch logo with cyan glow
    Nav: same 6 items vertical, active has left border-l-4 cyan + bg rgba(0,212,255,0.08)

══════════════════════════════════════════════════════════════════
SCREEN 1 — HOME (#screen-home)
══════════════════════════════════════════════════════════════════

HERO BANNER (55vh, full-width):
  Background: anime cover image, object-fit cover, object-position: center top
  Overlays:
    Top: rgba(13,13,26,0.4) vignette (top 25%)
    Bottom: transparent (50%)→#0d0d1a (bottom edge), heavy gradient
    Left edge: subtle rgba(13,13,26,0.2)

  Content (absolute, bottom-left, padding 20px 20px 28px):
    Row 1: Status chip "● İZLİYORUM" — amber bg/15, amber text, pill, 11px uppercase
    Row 2: Series title — 28px bold white, shadow 0 2px 8px rgba(0,0,0,0.8)
            Example: "Solo Leveling"
    Row 3: "Anime · Sezon 1 · ★ 8.9 · 12/24 bölüm" — 12px #9090b0
    Row 4: Progress bar — 4px, full-width, bg rgba(255,255,255,0.15), fill #00d4ff 50%
    Row 5: Buttons (flex, gap 10px, mt-14px):
      "▶  Devam Et — B.13" — bg #00d4ff, text #0d0d1a, 14px bold, h-44px, rounded-full, px-22px, shadow 0 0 20px rgba(0,212,255,0.3)
      "ℹ  Detay" — border rgba(0,212,255,0.5), text #00d4ff, h-44px, rounded-full, px-18px, bg rgba(0,212,255,0.08)

FILTER CHIPS (horizontal scroll, py-12px px-16px):
  "Tümü" [active] | "İzliyorum" | "Planlıyorum" | "Tamamlandı"
  Active: bg rgba(0,212,255,0.12), border #00d4ff, text #00d4ff
  Inactive: bg #1c1d37, border rgba(255,255,255,0.05), text #9090b0
  No scrollbar, pill 36px height, px-14px

CATEGORY ROWS (vertical stack, gap 28px between rows):
  ROW HEADER (px-16px mb-10px):
    Left: colored dot 5px + title 13px semibold #e1e0ff uppercase letter-spacing
    Right: "Tümü ›" 11px #9090b0

  ROW CARDS (horizontal scroll, px-16px, gap 10px, no scrollbar):
    4 full cards + ~25% of 5th peeking (scroll hint)

  ROW 1 — "DEVAM EDİYORUM" — dot #feb528 amber
  ROW 2 — "PLANLIYORUm" — dot #00d4ff cyan
  ROW 3 — "ANİME" — dot #00d4ff cyan
  ROW 4 — "MANGA" — dot #ffd9a1 cream
  ROW 5 — "MANHWA" — dot #bbc5eb violet
  ROW 6 — "TAMAMLANANLAR" — dot #22c55e green

CONTENT CARD (140×210px, 2:3 ratio, all rows):
  Container: rounded-xl 10px, overflow-hidden, shadow 0 4px 12px rgba(0,0,0,0.4)

  Layers bottom-to-top:
    1. Cover image: bg-cover center
    2. Left edge strip: 4px vertical, type color
    3. Top-right type badge: "ANIME"/"MANGA"/"MANHWA" — 9px bold uppercase
       bg type-color/10, border type-color/25, rounded-full, px-6px py-2px
    4. Bottom gradient: #1a1a2e 0%→transparent 65%
       Inside: title 11px white (2 lines truncate) + "★ 8.9" 10px #ffd9a1
    5. Bottom edge: progress bar 3px, bg rgba(255,255,255,0.08), fill #00d4ff

  HOVER STATE (show 3rd card in expanded state):
    transform: scale(1.18) translateY(-14px), z-index 20
    box-shadow: 0 24px 48px rgba(0,0,0,0.75)
    Bottom overlay reveals: "Bölüm 12 / 24 · 50%" + small "▶ Devam Et" cyan button

══════════════════════════════════════════════════════════════════
SCREEN 2 — SEARCH / DISCOVER (#screen-search)
══════════════════════════════════════════════════════════════════

Show TWO states side by side:

STATE A — EMPTY SEARCH (no query):
  Search bar (full-width, h-48px, rounded-full, bg #1a1a2e, border rgba(255,255,255,0.06)):
    Left: 🔍 icon #9090b0 | Placeholder: "Anime, manga ara..." #9090b0 | Right: 🎤 mic

  TRENDING (below, label "TREND" uppercase #9090b0):
    5 rows: rank# (24px bold cyan) + thumbnail (48×64px 2:3 rounded) + title + type badge
    Odd rows: #1a1a2e bg tint

  BROWSE CATEGORIES (grid 2×3, label "KATEGORİLER" uppercase):
    6 tiles (160×100px rounded-xl each):
      "Anime" cyan gradient | "Manga" amber gradient | "Manhwa" violet gradient
      "Oyun" pink gradient | "Tamamlananlar" green tint | "İzleme Listesi" amber tint
    Each: bold 16px center white + icon above

STATE B — WITH RESULTS ("solo" typed):
  Search bar: filled, cyan border ring, text "solo", ✕ right
  Results: vertical list
  Each result row:
    Thumbnail 60×90px 2:3 rounded-md (left)
    Title 14px bold white | Meta 11px muted | Status badge cyan pill
    "+ Ekle" ghost button right-aligned

══════════════════════════════════════════════════════════════════
SCREEN 3 — CONTENT DETAIL (#screen-detail)
══════════════════════════════════════════════════════════════════

HERO (48vh, full-width):
  Cover image, heavy bottom gradient to #0d0d1a
  Top controls (absolute top-12px px-16px):
    "← Geri" ghost (rounded-full, bg rgba(22,33,62,0.8), backdrop-blur)
    "✏️" edit ghost (same, right)
  Bottom-left content:
    Badges row: type badge + status badge
    Title: 22px bold white
    Meta: year · studio · genres chips (small pills)
    "★ 9.1 AniList" (cyan star)
    Buttons: "▶ B.13'ten Devam Et" primary | "📌 Listeye Ekle" ghost

INFO TABS (sticky, h-48px, bg #0d0d1a, border-bottom rgba(255,255,255,0.06)):
  "BÖLÜMLER" [active, cyan underline] | "BİLGİ" | "SİTELER"

EPISODES TAB:
  Progress bar section (px-16px py-12px, bg #1a1a2e):
    "12 / 24 bölüm" + progress bar 6px cyan 50% + "+ İlerleme Güncelle" ghost button
  
  Episode list (virtual scroll):
    Each row: episode# (bold cyan if current) | title + meta center | "▶ İzle" right
    Watched row: bg rgba(34,197,94,0.04), ✓ green right
    Current row: bg rgba(0,212,255,0.06), cyan left border, "▶ DEVAM" cyan button

══════════════════════════════════════════════════════════════════
SCREEN 4 — UPDATES (#screen-updates)
══════════════════════════════════════════════════════════════════

Header: "YENİ BÖLÜMLER" + Refresh icon right
Filter pills: "Tümü" | "Anime" | "Manga" | "Manhwa"

Group label: "BUGÜN" / "DÜN" / "BU HAFTA" (11px uppercase #9090b0, px-16px py-8px)

UPDATE CARD (bg #1a1a2e, rounded-xl, mx-16px mb-10px, p-14px):
  Left: cover thumbnail 56×80px 2:3 rounded-md
  Right flex column:
    Line 1: type badge + "2 saat önce" right-aligned 10px #9090b0
    Line 2: series title 14px bold #e1e0ff
    Line 3: "Bölüm 47 yayınlandı" 12px #9090b0
    Line 4: site chips small "ragnarscans" "+2 site"
    Line 5: "▶ Oku/İzle" primary cyan 34px | "✓ Gördüm" ghost

  UNREAD: left border-l-3px cyan + slightly lighter bg
  READ: normal bg, no border

══════════════════════════════════════════════════════════════════
SCREEN 5 — DOWNLOADS (#screen-downloads)
══════════════════════════════════════════════════════════════════

Header: "İNDİRMELER" + storage chip "2.3 GB kullanıldı" right
Filter pills: "Aktif" [active] | "Tamamlandı" | "Hata"

STORAGE GAUGE (bg #1a1a2e, rounded-xl, mx-16px, p-16px):
  Bar 8px: Anime cyan 40% | Manga cream 25% | empty rest
  "4.2 GB / 20 GB · Anime: 1.7 GB · Manga: 1.0 GB" below

DOWNLOAD ITEM — ACTIVE:
  bg #1a1a2e, rounded-xl, mx-16px mb-10px, p-14px, flex
  Left: cover 48×64px rounded
  Right: title 13px bold | source "ragnarscans.com" 10px cyan
    Progress bar 6px cyan animated shimmer
    "3.4 MB / 8.1 MB · 2 sayfa kaldı" 10px muted | "420 KB/s ↓" 10px green right
  Far right: ⏸ pause | ✕ cancel icons 28px

DOWNLOAD ITEM — COMPLETED:
  ✓ green checkmark + "8.1 MB · Tamamlandı" 11px muted right

DOWNLOAD ITEM — ERROR:
  ⚠ red + "Bağlantı hatası" | "Tekrar Dene" ghost red button

══════════════════════════════════════════════════════════════════
SCREEN 6 — STATS (#screen-stats)
══════════════════════════════════════════════════════════════════

Header: "İSTATİSTİKLERİM"
Profile: 48px circle avatar (gradient cyan→violet, initials "YS") + "kuroshin_user" 18px bold + "146 seri · 3842 bölüm · 312 saat" 12px muted

HERO STAT CARDS (3 horizontal, px-16px gap-10px):
  Each: bg #1a1a2e rounded-xl flex-1 py-20px center
  Big number: 24px cyan bold (146 / 312h / 3842)
  Label: 11px #9090b0 (Seri / Saat / Bölüm)

DONUT CHART SECTION (bg #1a1a2e, rounded-xl, mx-16px, p-20px):
  Title: "TÜR DAĞILIMI" 13px uppercase muted
  Donut 160px: Anime cyan | Manga cream | Manhwa violet | Game pink segments
  Center: "146\nSeri" bold
  Legend below: colored dot + label + count for each type

MONTHLY BAR CHART:
  Title: "AYLIK AKTİVİTE — 2026"
  12 bars Jan-Dec, cyan gradient fill, active bar highlighted
  X-axis: month abbreviations #9090b0

TOP SERIES LIST:
  Title: "EN ÇOK TAKİP"
  Ranked 1-5: same format as search trending

══════════════════════════════════════════════════════════════════
SCREEN 7 — SETTINGS (#screen-settings)
══════════════════════════════════════════════════════════════════

PROFILE HEADER (gradient bg #16213e→#0d0d1a, py-32px, center-aligned):
  Avatar 72px: gradient bg cyan→violet, "YS" bold initials, glow ring
  Name: "kuroshin_user" 18px bold #e1e0ff
  Sub: "146 seri · 3842 bölüm · 312 saat" 12px #9090b0
  Link: "İstatistikler →" 13px cyan

SETTINGS GROUPS (bg #1a1a2e, rounded-xl, mx-16px, mb-16px):
  Row border-bottom: rgba(255,255,255,0.04) between rows

  GROUP 1 — GÖRÜNÜM:
    "Tema" → "Koyu" + chevron
    "Görünüm" → Grid/Satır custom toggle (cyan when Satır)
    "Dil" → "Türkçe" + chevron

  GROUP 2 — VERİ:
    "Dışa Aktar" → chevron
    "İçe Aktar" → chevron
    "Veritabanı Boyutu" → "12 MB" right

  GROUP 3 — BAĞLANTI:
    "AniList Senkron" → toggle ON cyan + "Bağlandı ✓" green badge
    "MAL Senkron" → toggle OFF

  GROUP 4 — HAKKINDA:
    "Sürüm" → "v1.0.0"
    "Cover Debugger" → chevron
    "Arşiv" → chevron

══════════════════════════════════════════════════════════════════
OVERLAY 1 — ADD MODAL (#modal-add)
══════════════════════════════════════════════════════════════════

Bottom sheet 85vh, slides up, backdrop rgba(0,0,0,0.75) blur(4px)
Container: bg #1a2123, rounded-t-2xl
Handle: w-12 h-1.5 bg #3c494e center

Header: "İçerik Ekle" bold + ✕ right
Search: full-width rounded-full h-44px bg #0d0d1a border rgba(255,255,255,0.08)
  "🔍 Anime, manga, manhwa ara..."

Type tabs: "Anime" [active cyan pill] | "Manga" | "Manhwa" | "Oyun"

Results list (scrollable):
  Row: thumbnail 52×75px + title + year + AniList score + "+ Ekle" button right
  Expanded row: synopsis, episode count, status selector, "Listeye Ekle" primary CTA

══════════════════════════════════════════════════════════════════
OVERLAY 2 — VIDEO PLAYER (#modal-player)
══════════════════════════════════════════════════════════════════

Full-screen z-200, bg #000

AMBIENT LAYER (absolute fill, behind video):
  Blurred saturated video frame: blur(60px) saturate(1.8) brightness(0.25)
  Creates cinema glow effect

VIDEO: 16:9 centered, max 90vh, black letterbox

TOP CONTROLS (hover/tap, absolute top-0, gradient rgba(0,0,0,0.7)→transparent 80px):
  Left: "← Geri" ghost rounded white
  Center: "Solo Leveling — Bölüm 13" 13px #e1e0ff
  Right: CC | 🎨 Ambient [cyan glow=ON] | 📺 Theater | ⊡ PiP | ⛶ Fullscreen
    Each: 30px circle bg rgba(255,255,255,0.1)

BOTTOM CONTROLS (absolute bottom-0, gradient transparent→rgba(0,0,0,0.85) 110px):
  Progress: 4px track rgba(255,255,255,0.2), cyan fill 60%, 14px playhead circle white
  Controls: ⏮ ⏪ ⏯(40px) ⏩ ⏭ white | "18:34 / 24:10" 12px muted center | 🔊 + volume 80px slim bar right

  SKIP INTRO BTN (absolute bottom-100px right-20px):
    "INTRO'YU ATLA →" — bg #00d4ff, text #0d0d1a, 13px bold, h-38px, rounded-lg, px-16px
    Pulsing: box-shadow 0 0 20px rgba(0,212,255,0.6) keyframe in/out

  AUTO-NEXT CARD (absolute bottom-110px left-20px, w-200px):
    bg rgba(26,26,46,0.9) blur, rounded-xl, p-14px
    "Sıradaki Bölüm" 10px #9090b0
    "Bölüm 14" 15px bold white
    Countdown bar: 4px cyan, animated shrink
    "5s içinde başlıyor · ✕ İptal" 10px muted

══════════════════════════════════════════════════════════════════
OVERLAY 3 — MANGA / WEBTOON READER (#modal-reader)
══════════════════════════════════════════════════════════════════

Full-screen z-200, bg #0a0a12

STICKY HEADER (64px, bg #0d0d1a, border-bottom rgba(255,255,255,0.06)):
  Left: "← Kapat" #9090b0
  Center: "A Returner's Magic — B.142" 13px bold + "143 sayfa" 10px muted below
  Right: Mode toggle pill "📖 Webtoon"↔"📄 Sayfa" (cyan=active) | "🇹🇷 TR" cyan pill | 🌐 | ⛶

WEBTOON MODE (main, vertical scroll):
  bg #0a0a12, images stacked full-width, no gaps
  Right scroll indicator: thin 4px cyan track, 35% position dot
  Chapter nav popup (tap, bottom-center):
    bg rgba(13,13,26,0.9) blur, rounded-xl, fixed bottom-80px
    "◀ B.141" | "Bölüm 142 / 409" | "B.143 ▶"

PAGE MODE (second state, right of canvas):
  Single page contained centered, bg #000
  Bottom bar (64px, #0d0d1a): "◀ Önceki" | "14 / 43" | "Sonraki ▶"
  Top-right chip: "14/43" bg #1a1a2e

══════════════════════════════════════════════════════════════════
OVERLAY 4 — EDIT MODAL (#modal-edit) — compact version of ADD
══════════════════════════════════════════════════════════════════

Bottom sheet 80vh, same style as ADD
Pre-filled form: cover image preview left | title + type right
Fields: Status (watching/planning/etc.), My Progress (number input), Score (1-10 slider, cyan)
Actions: "Kaydet" primary | "Sil" danger ghost

══════════════════════════════════════════════════════════════════
OVERLAY 5 — ADD MODAL SUCCESS STATE (animation frame)
══════════════════════════════════════════════════════════════════

Centered toast (bottom, above bottom nav):
  bg #1a1a2e, rounded-xl, px-20px py-14px, shadow
  "✓ Solo Leveling eklendi" — ✓ green icon + text 14px
  Fades out after 2s

══════════════════════════════════════════════════════════════════
CANVAS LAYOUT FOR STITCH (place in 3 rows):
  Row 1: HOME | SEARCH-empty | SEARCH-results | DETAIL
  Row 2: UPDATES | DOWNLOADS | STATS | SETTINGS
  Row 3: ADD MODAL | VIDEO PLAYER | MANGA READER (webtoon) | MANGA READER (page)
  All screens: 390×844px mobile dimensions, 24px gap between screens
══════════════════════════════════════════════════════════════════
```
