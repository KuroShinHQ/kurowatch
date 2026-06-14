# KuroWatch — DESIGN.md (Stitch AI Prompt)

## Tasarım Kararları (Soru-Cevap Özeti)

| # | Soru | Karar |
|---|---|---|
| 1 | Tema | Koyu dark — siyah/lacivert |
| 2 | Layout | Grid — dikey poster 2:3 (Netflix/MAL stili) |
| 3 | Tip renk ayrımı | Renkli aksan şeridi (sol kenar) + ikon badge |
| 4 | Navigasyon | Mobil: alt tab bar / PC: sol sidebar |
| 5 | Puan gösterimi | ★ yıldız + sayı (9.2) |
| 6 | Yeni bölüm badge | "+N SiteAdı" yazısı + kart border glow |
| 7 | Progress | İnce bar + sayı (EP 87/139) |
| 8 | Arama | Ayrı ekran — nav tab'ından gidilir |
| 9 | Vurgu rengi | Cyan #00d4ff |
| 10 | Grid detay | Dikey poster 2:3, başlık + puan overlay |

---

## Renk Paleti

```css
--bg-primary:    #0d0d1a;   /* Ana arka plan */
--bg-card:       #1a1a2e;   /* Kart arka planı */
--bg-card-hover: #22223b;   /* Kart hover */
--bg-surface:    #16213e;   /* Surface (sidebar, nav) */

--accent:        #00d4ff;   /* Cyan vurgu */
--accent-dim:    rgba(0, 212, 255, 0.15);  /* Cyan arka plan tonu */

--text-primary:  #e0e0ff;
--text-secondary:#9090b0;
--text-muted:    #5050708;

/* İçerik tipi şerit renkleri */
--anime-color:   #3b82f6;   /* Mavi */
--manga-color:   #f97316;   /* Turuncu */
--manhwa-color:  #a855f7;   /* Mor */
--game-color:    #22c55e;   /* Yeşil */

/* Puan renkleri */
--score-high:    #22c55e;   /* 8-10 */
--score-mid:     #eab308;   /* 5-7 */
--score-low:     #ef4444;   /* 0-4 */

--border:        rgba(255,255,255,0.07);
--border-glow:   rgba(0, 212, 255, 0.6);  /* Yeni bölüm glow */
```

---

## Stitch AI Final Prompt

```
Design a personal anime/manga/manhwa/game tracker web app called "KuroWatch".
It must be fully responsive: mobile-first with PWA support (offline capable).

━━━ VISUAL THEME ━━━
Dark theme. Deep navy/black backgrounds.
- Background: #0d0d1a
- Card background: #1a1a2e
- Surface (sidebar/nav): #16213e
- Primary accent: cyan #00d4ff
- Text: #e0e0ff (primary), #9090b0 (secondary)
- Font: system-ui, -apple-system, sans-serif (NO Google Fonts — must work offline)
- Subtle borders: rgba(255,255,255,0.07)
- Border radius: 12px for cards, 8px for buttons/inputs
- No heavy shadows — use subtle inner glow and border highlights instead

━━━ NAVIGATION ━━━
MOBILE (< 1024px): Fixed bottom tab bar, 5 tabs:
  🏠 Home | 🔍 Search | ➕ Add | 📊 Stats | ⚙ Settings
  Active tab: cyan accent color + small dot indicator below icon
  Tab bar background: #16213e with top border rgba(255,255,255,0.1)

DESKTOP (≥ 1024px): Fixed left sidebar, 240px wide:
  - App logo/name "KuroWatch" at top
  - Same 5 nav items (icon + label)
  - Active: left border cyan + bg rgba(0,212,255,0.08)
  Main content shifts right 240px

━━━ CONTENT TYPE SYSTEM ━━━
4 types, each with a colored left accent strip (4px wide) on cards:
  🎬 Anime   → #3b82f6 (blue)
  📖 Manga   → #f97316 (orange)
  📱 Manhwa  → #a855f7 (purple)
  🎮 Game    → #22c55e (green)
The icon badge (🎬/📖/📱/🎮) appears in the top-right corner of each card.

━━━ HOME SCREEN ━━━
Layout: Vertical poster grid (2:3 aspect ratio cards)
  Mobile: 2 columns
  Tablet (768px+): 3 columns
  Desktop (1280px+): 5 columns
  Grid gap: 12px
  Padding: 16px

Section at top: "🔔 New Updates" — horizontal scroll row of cards with glowing border
  These are content items where new chapters/episodes arrived.
  Each glowing card has a cyan border glow (box-shadow: 0 0 12px rgba(0,212,255,0.6))
  and a badge chip in top-left corner: "+2 Crunchyroll" (white text, dark bg, 10px font)

Below: Filter chips row (horizontally scrollable):
  [All] [🎬 Anime] [📖 Manga] [📱 Manhwa] [🎮 Game]
  [Watching] [Reading] [Completed] [On Hold] [Dropped]
  Active chip: cyan bg, dark text. Inactive: transparent, muted border.

Main grid below filter chips.

━━━ CONTENT CARD (Poster Style) ━━━
Size: fills grid column, 2:3 height-to-width ratio
Structure:
  - Poster image fills entire card (object-fit: cover)
  - Top-right corner: type icon badge (🎬/📖/📱/🎮) in small pill
  - Top-left corner (if new update): "+N SiteName" badge (red/cyan pill)
  - Left edge: 4px colored accent strip (type color)
  - Bottom overlay gradient (transparent → rgba(13,13,26,0.95)):
      Line 1: Title (bold, 13px, white, 2-line max, ellipsis)
      Line 2: ★ 9.2  |  EP 87/139
      Line 3: Thin progress bar (full width, colored by type, height 3px)
  - Hover state: slight scale(1.03) transform, brighter border

━━━ SEARCH SCREEN ━━━
Full screen when Search tab active.
Top: Search input (full width, dark bg, cyan focus border, 🔍 icon left)
Below: Filter section (collapsible):
  - Type filter (Anime/Manga/Manhwa/Game checkboxes)
  - Status filter (Watching/Completed/etc)
  - Score range slider
Results: same poster grid as home screen
Empty state: "No results found" with faded icon

━━━ ADD CONTENT SCREEN ━━━
When ➕ tab pressed, show a modal/bottom sheet (mobile) or centered modal (desktop):
  - Search field: "Search by title..."
  - Live results from API (AniList/IGDB) as you type
  - Each result: small poster + title + year + type badge
  - Tap result → expand to full add form:
      Type (auto-detected), Status, Score (0-10 slider), Sites (add multiple URLs)
  - "Add to Library" button (cyan, full width)

━━━ CONTENT DETAIL SCREEN ━━━
Full screen slide-in when card tapped.
Top: Large poster (40vh height) with gradient overlay
  Back button (←) top-left, Edit button top-right
Info section below poster:
  - Title (large, bold)
  - Type badge + Status badge (Watching / Completed / etc)
  - ★ score (large, cyan) | "My Rating: ★★★★★★★★★☆ 8.5/10"
  - Progress: "Episode 87 / 139" with large progress bar
  - "Mark Next Episode ✓" button (accent)
Tabs below: [Episodes] [Sites] [Notes]
  Episodes tab: scrollable list, each row: EP number + title + ✓ checkbox (mark watched)
  Sites tab: list of tracking sites, each with icon + site name + "Open →" button (primary site first)
  Notes tab: textarea for personal notes

━━━ STATS SCREEN ━━━
Cards layout showing:
  - Total time: "847 hours" broken down by type (donut chart)
  - Items by status (bar chart)
  - Average score by type
  - Most watched genres (tag cloud)
  Keep charts minimal — use CSS/SVG only, no heavy chart libraries

━━━ SETTINGS SCREEN ━━━
Simple list layout:
  - Export Data button (downloads JSON)
  - Import Data button (uploads JSON)
  - Update Check Interval (selector: 1h / 6h / 24h)
  - Manage Sites section

━━━ INTERACTIONS & ANIMATIONS ━━━
- Page transitions: fade (opacity 0→1, 150ms)
- Card hover: transform scale(1.03), 200ms ease
- Bottom sheet open: slide up from bottom, 300ms cubic-bezier(0.32,0.72,0,1)
- Progress bar fill: CSS transition width 600ms ease
- Badge pulse: new update cards get subtle pulse animation on the glow border
- Skeleton loaders: show gray animated shimmer while content loads

━━━ TECHNICAL REQUIREMENTS ━━━
- All API calls: fetch('/api/...') — relative URL, FastAPI backend on port 8099
- Static files served by FastAPI (frontend/ directory)
- PWA: include <link rel="manifest"> and register service worker in JS
- manifest.json: name="KuroWatch", theme_color="#00d4ff", background_color="#0d0d1a"
- No authentication needed — single user, local app
- CSS custom properties for all colors (easy theming)
- Mobile-first CSS (min-width breakpoints)
- No heavy JS frameworks — vanilla JS or minimal library
- Images: use <img loading="lazy"> for all cover images

━━━ FILE OUTPUT NEEDED ━━━
Please generate:
1. index.html — complete app shell, all screens as sections/views
2. style.css — complete styles, mobile-first, all variables
3. app.js — navigation logic, API calls, state management
4. manifest.json — PWA manifest
```

---

## Ekranlar Özeti

```
1. Home       → grid poster + yeni bölüm row + filtre chips
2. Search     → arama input + filtre + sonuç grid
3. Add        → modal/sheet, API arama, form
4. Stats      → donut + bar + istatistikler
5. Settings   → export/import + ayarlar
6. Detail     → full screen, EP listesi, siteler, notlar
```
