# KuroWatch — DESIGN.md (Stitch AI Final Prompt)

## Tüm Tasarım Kararları

| # | Karar | Seçim |
|---|---|---|
| 1 | Tema | Koyu dark #0d0d1a / #1a1a2e |
| 2 | Layout | Grid 2:3 dikey poster, Netflix/MAL stili |
| 3 | Tip ayrımı | Sol renkli şerit + ikon badge |
| 4 | Navigasyon | Mobil: alt bar / PC: sol sidebar |
| 5 | Puan | ★ + ondalıklı sayı (9.2) |
| 6 | Badge | "+N SiteAdı" + border glow |
| 7 | Progress | İnce bar + EP 87/139 |
| 8 | Arama | Ayrı ekran, 2 sekme: Kütüphanem / Keşfet |
| 9 | Vurgu | Cyan #00d4ff |
| 10 | Kart tık | Detay sayfası açılır |
| 11 | Süre | Otomatik: bölüm × ortalama süre |
| 12 | Çoklu site | Yeni bölüm olan site açılır |
| 13 | Oyun | Durum + isteğe bağlı % |
| 14 | Durum | 6: İzliyor / Tamamlandı / Askıda / Bıraktım / Planlıyorum / Yeniden İzliyor |
| 15 | Etiket | API türleri + kendi etiketleri |
| 16 | Keşfet | Arama + türe göre öneri |
| 17 | Import çakışma | Çakışanları listele, kullanıcı seçsin |
| 18 | Puan hassasiyet | Ondalıklı slider (7.3, 9.1) |
| 19 | Kapak | URL ile değiştirilebilir (dosya yok) |
| 20 | Notlar | Yorum + spoiler toggle |
| 21 | Telegram | Yok |
| 22 | Bildirim | Badge + ayrı "Güncellemeler" sayfası |
| 23 | Devam | "İzliyor" filtresi ile |
| 24 | Başlık dili | İngilizce her zaman |
| 25 | Varsayılan sıra | Puana göre (en yüksek önce) |
| 26 | Boş durum | Direkt boş liste + "Ekle" butonu |
| 27 | Logo | Göz ikonu + KuroWatch yazısı |
| 28 | Scraper | Genel altyapı, kullanıcı URL girer |
| 29 | Bölüm işaret | Slider (toplu) + tek tek checkbox |
| 30 | Bildirim türü | Tarayıcı push + uygulama içi |

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
  Group 4 — About:
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
