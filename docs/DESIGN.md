# KuroWatch — DESIGN.md (Stitch AI Final Prompt)

---

## ⚠️ Stitch AI Dikkat Notları (Araştırma — 14 Haz 2026)

### Stitch'in Kısıtları
- **Generic output riski:** Prompt yeterince detaylı olmazsa generic Material/Tailwind çıktısı verir. Çözüm: hex renk, pixel değer, exact component açıklaması → bizim promptumuz bunu karşılıyor.
- **Vanilla JS desteği yok:** Stitch çıktısı HTML/CSS + React/JSX veya Tailwind. Biz vanilla JS istiyoruz → Stitch'ten HTML/CSS al, JS kısmı manuel yazılacak (app.js Claude ile).
- **Google tasarım token sistemi:** Stitch kendi token sistemi kullanır (Material You). Çıktıdan tüm `--md-*` değişkenlerini sil, `--kw-*` (KuroWatch) ile değiştir.
- **PWA yok:** Stitch manifest.json / service worker üretmez → manuel eklenecek.
- **Backend entegrasyonu yok:** Fetch call'lar placeholder olur → sonradan `/api/...` ile değiştirilecek.
- **Mart 2026 kalite düşüşü:** Stitch güncellemesinden sonra rapor var. İlk çıktı beğenilmezse yeniden dene, veya component bazlı ayrı ayrı üret.

### Kaç Panel Üretilecek? (Araştırma)
- Stitch 2.0: **max 5 ekran / üretim** (5 ekran = 1 generation)
- Standard mod (Gemini Flash): 350/ay → ideation
- Experimental mod (Gemini Pro): 50/ay → final polish
- **Bizim planımız: 2 batch**
  - **Batch 1** (Standard): Home + Detail + Search + Updates + Stats
  - **Batch 2** (Experimental): Add Modal + Settings + Conflict Modal
- Prompt: text olarak ver (screenshot/voice değil — hassas hex/layout için text daha iyi)
- Minor canvas düzeltmeleri generation saymaz → küçük fix'leri canvas'ta yap

### Stitch Sonrası Yapılacaklar (Checklist)
```
[ ] Google token sistemi temizle (--md-* → --kw-*)
[ ] Renk paletini kendi palette ile eşle (yukarıdaki CSS değişkenler)
[ ] app.js: navigation + state + fetch('/api/...') Manuel yaz
[ ] manifest.json + sw.js ekle (PWA)
[ ] navigator.vibrate() haptic noktalarını ekle
[ ] Spring animasyon curve'leri ekle (Stitch linear kullanır)
[ ] Skeleton loader'ları gerçek API ile bağla
[ ] Offline banner: navigator.onLine event
```

---

## 🎬 Premium Animasyon Sistemi (Netflix/Spotify Araştırma)

### Neden Önemli
Araştırma: Micro-animasyonlar perceived performance'ı %30-40 artırır. Day-1 retention'ı %18-28 etkiler. Ama aşırı animasyon = "oyuncak hissi". Netflix prensibi: **fonksiyonel animasyon** — kullanıcıya bir şey olduğunu söyle, dikkat dağıtma.

### Animasyon Eğri Kütüphanesi
```css
/* KuroWatch Spring Curves */
--ease-spring:    cubic-bezier(0.32, 0.72, 0, 1);     /* Modal, bottom sheet açılış */
--ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);       /* Kart hover, scale */
--ease-in-expo:   cubic-bezier(0.7, 0, 0.84, 0);       /* Kapanma animasyonları */
--ease-bounce:    cubic-bezier(0.34, 1.56, 0.64, 1);   /* Checkbox, badge pop */
--ease-standard:  cubic-bezier(0.2, 0, 0, 1);          /* Sayfa geçişleri */
```

### Animasyon Zamanlaması
```
Sayfa geçiş (fade):        150ms  ease-standard
Kart hover scale:          180ms  ease-out-expo
Bottom sheet açılış:       320ms  ease-spring
Modal backdrop:            200ms  ease-standard
Progress bar fill:         600ms  ease-out-expo
Badge pop (yeni bölüm):    400ms  ease-bounce
Skeleton shimmer:          1.5s   linear infinite
Checkbox check:            250ms  ease-bounce
Score slider thumb:        100ms  ease-standard
```

### Animasyon Kural Seti
- ❌ 3'ten fazla eş zamanlı animasyon
- ❌ 600ms üzerinde UI bloklaması
- ❌ Bounce animasyonu kritik işlemlerde (sadece dekoratif elemanlarda)
- ✅ `prefers-reduced-motion` media query: tüm animasyonları 0ms yap
- ✅ Her animasyonun görsel karşılığı olmalı (haptic ile eşleştir)

---

## 📳 Haptic Feedback Sistemi (Web Vibration API)

PWA'da `navigator.vibrate()` ile fiziksel geri bildirim. Sadece destekleyen cihazlarda.

```javascript
// kurowatch_haptics.js
const haptic = {
  light:    () => navigator.vibrate?.(10),   // Filtre chip seç
  medium:   () => navigator.vibrate?.(30),   // Bölüm işaretle ✓
  heavy:    () => navigator.vibrate?.(60),   // İçerik eklendi
  success:  () => navigator.vibrate?.([10, 50, 10]),  // Tamamlandı
  error:    () => navigator.vibrate?.([30, 20, 30]),  // Hata
  snap:     () => navigator.vibrate?.(15),   // Kart hover
};
```

### Haptic Eşleştirme
| Eylem | Haptic | Açıklama |
|---|---|---|
| Bölüm ✓ işaretle | `medium` (30ms) | Onay hissi |
| İçerik ekle | `heavy` (60ms) | Önemli eylem |
| Tamamlandı işaretle | `success` [10,50,10] | Başarı ritmi |
| Filtre seç | `light` (10ms) | Hafif geri bildirim |
| Swipe to dismiss | `snap` (15ms) | Snap hissi |
| Hata / bulunamadı | `error` [30,20,30] | Dikkat ritmi |
| Uzun basma başladı | `medium` (30ms) | Context menu açılıyor |

---

## 🎨 Premium Dark Theme Mimarisi

### Netflix'ten Alınan Prensipler
1. **Elevation hierarchy:** Yüzeylerin "yüksekliği" renk değil, şeffaflıkla ifade edilir.
   - Base: `#0d0d1a`  → Kart: `#1a1a2e`  → Modal: `#22223b`  → Tooltip: `#2d2d4e`
2. **Yalnızca accent vurgulanır:** Aksiyon alan her şey cyan. Pasif her şey gri/muted.
3. **Görüntü önceliği:** Kapak resmi en büyük eleman. Metin overlay, resmi öldürmez.
4. **OLED dostu:** Gerçek siyah (#000) yok — `#0d0d1a` kullanılıyor (AMOLED'de az pil ama saf siyah donuk görünür).

### Skeleton Loader Sistemi
```css
/* Görüntü yüklenene kadar shimmer */
.skeleton {
  background: linear-gradient(90deg, #1a1a2e 25%, #22223b 50%, #1a1a2e 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

### Image Error Fallback
```html
<!-- Her cover img için -->
<img src="..." loading="lazy" onerror="this.src='/assets/no-cover.svg'" />
```

---

## Tüm Tasarım Kararları (Sohbet-1 + Sohbet-2 soru-cevap)

| # | Karar | Seçim |
|---|---|---|
| 1 | Tema | Koyu dark #0d0d1a / #1a1a2e |
| 2 | Layout | Grid 2:3 dikey poster, Netflix/MAL stili |
| 3 | Tip ayrımı | Sol renkli şerit + ikon badge |
| 4 | Navigasyon | Mobil: alt bar / PC: sol sidebar |
| 5 | **Puan** | **Sadece ★ yıldız** (10 yarım yıldız interaktif) — slider YOK |
| 6 | Badge | "+N SiteAdı" + border glow |
| 7 | Progress | İnce bar + EP 87/139 |
| 8 | Arama | Ayrı ekran, 2 sekme: Kütüphanem / Keşfet |
| 9 | Vurgu | Cyan #00d4ff |
| 10 | Kart tık | Detay sayfası açılır |
| 11 | Süre hesabı | Tahmini: progress × duration + bölüm sayısı — Stats'ta ikisi ayrı gösterilir |
| 12 | Çoklu site | Yeni bölüm olan site açılır |
| 13 | Oyun | FAZ-2 (IGDB ertelendi) |
| 14 | Durum | 6: İzliyor / Tamamlandı / Askıda / Bıraktım / Planlıyorum / Yeniden İzliyor |
| 15 | Etiket | API türleri + kendi etiketleri |
| 16 | Keşfet | Arama + tür öneri; **offline → kendi kütüphanenden öner** |
| 17 | Import çakışma | Yeni item otomatik ekle, çakışanları listele kullanıcı seçsin |
| 18 | Puan yok gösterimi | **Boş yıldızlar ☆☆☆☆☆☆☆☆☆☆** |
| 19 | Kapak | URL ile değiştirilebilir (dosya yok) |
| 20 | Notlar | Yorum + spoiler toggle |
| 21 | Telegram | Yok |
| 22 | Bildirim MVP | **Web Push (VAPID) + in-app badge** — izin Settings'teki butonla |
| 23 | Devam | "İzliyor" filtresi ile |
| 24 | Başlık dili | İngilizce her zaman |
| 25 | Varsayılan sıra | **Sadece puana göre (en yüksek önce) — MVP** |
| 26 | Boş durum | Direkt boş liste + "Ekle" butonu |
| 27 | Logo | Göz ikonu + KuroWatch yazısı |
| 28 | Bölüm verisi | **AniList sayısı + chapter_check.py başlıkları** |
| 29 | Bölüm işaret | Slider (toplu) + tek tek checkbox; **virtual scroll (1000+ bölüm)** |
| 30 | Silme | **Soft delete / Arşiv** — Settings > Arşiv sayfasında geri yükleme |
| 31 | **Uzun bas menüsü** | Sonraki Bölüm ✓ / Durum Değiştir / Puan Güncelle / **Arşivle 🗄️** |
| 32 | Seri bitti | Durum otomatik 'Tamamlandı' + **puan sor mini modal** |
| 33 | **Dil (i18n)** | TR varsayılan + EN desteği; data-i18n attrs + JSON locale; Settings > dropdown |
| 34 | Filter chip'ler | **Tek kaydırır satır** (tip + durum birlikte) |
| 35 | Site açılış | **Yeni sekmede** (window.open '_blank') |
| 36 | Başlangıç sayfası | **Son sayfayı hatırla** (localStorage) |
| 37 | PWA install | **Sadece Settings'te buton** — otomatik prompt yok |
| 38 | MAL fallback | **FAZ-2'ye ertelendi** |
| 39 | IGDB / Oyun | **FAZ-2'ye ertelendi** |
| 40 | Keşfet öneri alg. | **Araştırma gerekli, askıya alındı** |
| 41 | İndirme kalitesi | **Global ayar** — 360p/480p/720p/1080p/best; tüm indirmeler bu kalitede (Netflix modeli) |
| 42 | Daisy chain tetik | **%50** — bölüm/chapter yarısında N+1 otomatik indir |
| 43 | Oto-sil | **config toggle** — false=modal; true=otomatik sil. Disk toplamı Settings'te |
| 44 | TR anime/dizi siteler | stream_finder.py + embed iframe → yt-dlp (resmi extractor yok) |
| 45 | TR manga siteler | Madara admin-ajax.php (tümü aynı endpoint) + mangadex-downloader |
| 46 | Crunchyroll | Ücretsiz ✅ / Premium DRM ❌ → "🔒 Tarayıcıda Aç" butonu |
| 47 | Manga çeviri | **Typesetting (B)** — YOLOv8+manga-ocr+LaMa+DeepL; **sadece PC+GPU** |
| 48 | Çeviri kalite | DeepL → Google Translate → LibreTranslate (fallback zinciri); sayfa bağlamı |
| 49 | Settings dil | TR varsayılan + EN; dropdown Settings Group 3'te |
| 50 | Web Push | VAPID; Settings Group 4'te buton; izin sonrası "Enabled ✓" |

---

## Renk Paleti

```css
--bg-primary:    #0d0d1a;
--bg-card:       #1a1a2e;
--bg-card-hover: #22223b;
--bg-surface:    #16213e;

--accent:        #00d4ff;
--accent-dim:    rgba(0,212,255,0.12);
--accent-glow:   rgba(0,212,255,0.6);

--text-primary:  #e0e0ff;
--text-secondary:#9090b0;
--text-muted:    #505070;

--anime-color:   #3b82f6;
--manga-color:   #f97316;
--manhwa-color:  #a855f7;
--game-color:    #22c55e;

--score-high:    #22c55e;
--score-mid:     #eab308;
--score-low:     #ef4444;

--border:        rgba(255,255,255,0.07);
--new-glow:      0 0 0 2px rgba(0,212,255,0.7), 0 0 16px rgba(0,212,255,0.3);
```

---

## Stitch AI Final Prompt

```
Design a personal anime/manga/manhwa/game tracker web app called "KuroWatch".
Single-user, local app. Must be fully responsive (mobile-first) and PWA-ready (offline capable).

━━━ BRAND / LOGO ━━━
Logo: an eye/watch icon (minimal line art) + "KuroWatch" text beside it.
"Kuro" in dim white, "Watch" in cyan (#00d4ff). Eye icon also cyan.
Show in sidebar header (desktop) and centered top (mobile).

━━━ VISUAL THEME ━━━
Dark theme, deep navy/black. NO light mode.
- BG: #0d0d1a
- Card BG: #1a1a2e  |  Card hover: #22223b
- Surface (sidebar/nav/modals): #16213e
- Accent: #00d4ff (cyan)
- Text: #e0e0ff primary, #9090b0 secondary
- Font: system-ui, -apple-system, "Segoe UI", sans-serif (NO Google Fonts — offline)
- Borders: rgba(255,255,255,0.07)
- Border radius: cards 12px, inputs/buttons 8px
- No heavy shadows — use border highlights and subtle inner glow

━━━ CSS VARIABLES ━━━
Define all colors as CSS custom properties at :root.
Type accent colors:
  --anime:   #3b82f6 (blue)
  --manga:   #f97316 (orange)
  --manhwa:  #a855f7 (purple)
  --game:    #22c55e (green)
Score colors: high(8+) #22c55e, mid(5-7) #eab308, low(<5) #ef4444

━━━ NAVIGATION ━━━
MOBILE (< 1024px):
Fixed bottom tab bar, 5 tabs with icon + small label:
  🏠 Home | 🔍 Search | ➕ Add | 🔔 Updates | ⚙ Settings
Active: icon + label in cyan. Inactive: muted gray.
Tab bar: #16213e bg, top border rgba(255,255,255,0.1), height 60px.
Safe-area padding bottom (for iPhone notch).

DESKTOP (≥ 1024px):
Fixed left sidebar, 240px wide, full height.
Top: eye logo + "KuroWatch" text.
Nav items (icon + label, vertical list):
  🏠 Home | 🔍 Search | ➕ Add | 🔔 Updates | ⚙ Settings
Active item: 3px left cyan border + rgba(0,212,255,0.08) bg.
Main content: margin-left 240px.

━━━ CONTENT TYPE SYSTEM ━━━
4 types, visually distinguished:
  🎬 Anime   → left accent strip: #3b82f6
  📖 Manga   → left accent strip: #f97316
  📱 Manhwa  → left accent strip: #a855f7
  🎮 Game    → left accent strip: #22c55e
Each card has: 4px wide colored left border strip + type icon badge (top-right corner, pill).

━━━ HOME SCREEN ━━━
Default sort: score descending (highest score first).
Top filter chip row (horizontal scroll, sticky):
  [All] [🎬 Anime] [📖 Manga] [📱 Manhwa] [🎮 Game]
  [Watching] [Completed] [On Hold] [Dropped] [Planning] [Rewatching]
  Active chip: cyan bg + dark text. Inactive: transparent + muted border.

Main content: vertical poster grid
  Mobile: 2 columns  |  Tablet 768px+: 3 columns  |  Desktop 1280px+: 5 columns
  Gap: 12px  |  Padding: 16px

Empty state (no items yet):
  Centered in grid area: dim eye icon (large) + "No content yet" + cyan "Add First" button.

━━━ CONTENT CARD (Poster) ━━━
Aspect ratio: 2:3 (width:height — tall poster shape)
Structure:
  - Cover image: fills card, object-fit cover
  - Left edge: 4px colored type accent strip
  - Top-right: type icon badge (🎬/📖/📱/🎮) in small pill (#16213e bg, 10px)
  - Top-left (conditional): update badge "+N SiteName" (red pill, white text, 10px bold)
    When badge present: card gets glow border: 0 0 0 2px rgba(0,212,255,0.7), 0 0 16px rgba(0,212,255,0.3)
  - Bottom gradient overlay (transparent → rgba(13,13,26,0.95), covers bottom 45%):
      → Title: bold 13px, white, max 2 lines, ellipsis
      → ★ 9.2  (star icon cyan + score text, color-coded)
      → Thin progress bar: 3px tall, full width, colored by type, shows EP/CH progress
      → "EP 87 / 139" or "CH 340 / ?" below bar in 10px muted text
  - Hover: scale(1.03) transform 200ms ease, brighter border

━━━ DETAIL SCREEN ━━━
Full-screen view (slides in from right on mobile, center panel on desktop wide).
Top section:
  - Cover image: 40vh height, full width, object-fit cover
  - Back arrow ← top-left (floating over image)
  - Edit pencil icon top-right (floating)
  - Bottom gradient over image: title + type badge + status badge

Info section:
  - Title (large bold, English)
  - Row: type icon badge + status badge (color-coded: Watching=cyan, Completed=green, etc.)
  - Score display: large ★ stars row (10 half-stars interactive) + "8.5 / 10" text in cyan
  - Progress row: "Episode 87 / 139" + large type-colored progress bar
  - "Mark Next ✓" button (accent cyan, full width on mobile)
  - Quick jump slider: "Mark up to episode: [slider 0–139]"

Tabs below info: [Episodes] [Sites] [Notes]

EPISODES TAB:
  Scrollable list. Each row:
    EP number + episode title (if available) + ✓ checkbox (right side)
    Watched rows: dimmed + checkmark. Unwatched: normal.

SITES TAB:
  List of tracking sites for this content.
  Each row: site favicon/icon + site name + latest episode on that site + "Open →" button
  Primary site: shown first with ★ or "Primary" label
  If site has newer episodes than user's progress: highlight row in accent color

NOTES TAB:
  Personal note textarea (plain text, dark bg, cyan focus border)
  Spoiler toggle: "🚨 Contains Spoilers" switch (when on, note is hidden behind blur on detail view)

━━━ SEARCH SCREEN ━━━
Full screen. Top: search input (full width, cyan focus).
Two tabs below search bar:
  [My Library] [Discover]

MY LIBRARY TAB:
  Filters: type chips + status chips (same as home)
  Results: same poster grid

DISCOVER TAB:
  Search input → live results from AniList/IGDB API
  Results list: small poster + title + year + type badge + "Add +" button
  Below search (when empty): genre chips row (Action, Romance, Isekai, RPG, etc.)
  Clicking genre chip → shows top results for that genre from AniList

━━━ ADD CONTENT (Modal / Bottom Sheet) ━━━
Triggered by ➕ tab.
Mobile: slides up as bottom sheet (60% screen height, draggable to dismiss)
Desktop: centered modal (500px wide)

Step 1: Search field "Search title..."
  Live results (from API) appear as rows: tiny poster + title + year + type
  "Can't find it? Add manually" link at bottom

Step 2 (after selecting): Edit form
  - Title (pre-filled, editable)
  - Type: segmented control [Anime][Manga][Manhwa][Game]
  - Status: dropdown (6 options)
  - Score: slider 0–10 with 0.1 step, shows value live (e.g. "8.5")
  - Cover URL: text input (optional override)
  - Sites: repeating rows [Site Name] [URL] [☆ Primary] [✕ Remove] + "+ Add Site" button
  - % Progress (game only): optional number input 0–100
  - Notes: textarea
  - "Add to Library" button (cyan, full width)

━━━ UPDATES SCREEN ━━━
Accessible via 🔔 nav tab.
Header: "Updates" + "Check Now" button (manual refresh)
List of recent updates (newest first):
  Each row: tiny cover + content title + "EP 1150 on gogoanime" + "2 hours ago"
  Unread: left cyan border, slightly brighter bg
  Read: dimmed
  Tap row → opens content detail
Empty state: "No updates yet. Check Now ↻"

━━━ STATS SCREEN ━━━
Page sections (vertical scroll):
  1. Summary cards row: "Total Hours Watched/Read" | "Items in Library" | "Avg Score"
  2. Donut chart: breakdown by type (Anime/Manga/Manhwa/Game hours)
  3. Bar chart: items by status (Watching/Completed/etc)
  4. Score distribution: simple bar histogram
  5. Top genres: horizontal tag cloud
  Use CSS/SVG charts only (no heavy chart libraries). Keep minimal and elegant.

━━━ SETTINGS SCREEN ━━━
Grouped list:
  Group 1 — Sync:
    "Export Library" → downloads kurowatch_backup.json
    "Import Library" → file picker, uploads JSON, shows conflict resolution if needed
    "Archive" → navigates to archived items list (soft-deleted content, restore button per item)
  Group 2 — API Credentials:
    IGDB Client ID: [input]
    IGDB Client Secret: [input]
    "Save" button
  Group 3 — Preferences:
    Default episode duration (Anime): number input (minutes)
    Default chapter duration (Manga): number input
    Default chapter duration (Manhwa): number input
    Default session duration (Game): number input
    Update check: on app open toggle
    Language: dropdown [Türkçe / English] (changes all UI text via i18n.js)
  Group 4 — Notifications:
    "Enable Push Notifications" button → requests browser push permission (VAPID)
    Status indicator: "Enabled ✓" or "Disabled" after permission granted/denied
  Group 5 — App:
    "Add to Home Screen" button → triggers PWA install prompt (navigator.standalone check)
    Show only if app not already installed (window.matchMedia standalone check)
  Group 6 — About:
    "KuroWatch v1.0.0" text

━━━ IMPORT CONFLICT RESOLUTION ━━━
When import finds conflicts (same item, different data on PC vs import):
Shows a modal list:
  Each conflict row: content title + "Your version (updated X ago)" vs "Import version (updated Y ago)"
  Two buttons per row: [Keep Mine] [Use Import]
  Bottom: "Apply All" button

━━━ INTERACTIONS & ANIMATIONS ━━━
- Page transitions: fade opacity 0→1, 150ms ease
- Card hover: scale(1.03), 200ms ease, border brightens
- Bottom sheet open: translateY 100%→0, 300ms cubic-bezier(0.32,0.72,0,1)
- Modal backdrop: rgba(0,0,0,0.7) fade in
- Badge pulse: new-update cards get 3s infinite subtle glow pulse animation
- Progress bar fill: transition width 600ms ease
- Score slider: shows value in real-time tooltip above thumb
- Skeleton loaders: gray shimmer animation while images/data load
- Checkbox check: quick scale bounce + color fill

━━━ PWA REQUIREMENTS ━━━
Include manifest.json reference in HTML:
  name: "KuroWatch"
  short_name: "KuroWatch"
  theme_color: "#00d4ff"
  background_color: "#0d0d1a"
  display: "standalone"
  icons: (placeholder 192x192 and 512x512)

Register service worker in app.js:
  Cache: index.html, style.css, app.js (app shell strategy)

━━━ TECHNICAL CONSTRAINTS ━━━
- All API calls: fetch('/api/...') relative URL (FastAPI backend port 8099)
- No authentication — single user local app
- Offline: cached shell, show "Offline" banner when no backend
- NO Google Fonts, NO CDN resources — must work fully offline
- CSS custom properties for all colors
- Vanilla JS (or very minimal library) — no React/Vue
- Mobile-first CSS, min-width breakpoints
- All images: loading="lazy" + fallback placeholder on error

━━━ FILES TO GENERATE ━━━
1. index.html  — full app shell, all screen sections
2. style.css   — complete styles, all components, CSS variables, animations
3. app.js      — navigation, state, API calls, PWA registration
4. manifest.json — PWA manifest
```
