# KuroWatch — Design Reference

> Son güncelleme: 22 Haz 2026 — mevcut index.html kodu ile uyumlu

---

## 🎨 Renk Sistemi

```css
/* Ana Renkler */
--bg-primary:    #0d0d1a   /* App arka planı */
--bg-card:       #1a1a2e   /* Kart / bölüm arka planı */
--bg-raised:     #16213e   /* Yükseltilmiş öğe (progress kutusu vb.) */
--bg-input:      #1c1d37   /* Input, chip arka planı */
--bg-modal:      #1a2123   /* Modal / bottom sheet arka planı */
--bg-modal-head: #161d1f   /* Modal header arka planı */
--bg-overlay:    #0a0a12   /* Manga reader arka planı */

/* Vurgu Rengi */
--accent:        #00d4ff   /* Cyan — buton, active, progress */
--accent-dim:    #00d4ff1a /* %10 opaklık — chip arka planı */
--accent-border: #00d4ff4d /* %30 opaklık — border */

/* Tip Renkleri (TYPE_COLOR) */
--color-anime:   #00d4ff   /* Cyan */
--color-manga:   #ffd9a1   /* Sarı-krem */
--color-manhwa:  #bbc5eb   /* Açık mor */
--color-game:    #ffb4ab   /* Pembe-kırmızı */

/* Metin */
--text-primary:  #e1e0ff   /* Ana metin */
--text-muted:    #9090b0   /* İkincil metin */
--text-modal:    #dde3e7   /* Modal içi metin */
--text-on-accent:#0d0d1a   /* Accent buton üstündeki metin */

/* Durum Renkleri */
--status-watching:   #feb528   /* Sarı — İzliyor */
--status-completed:  #22c55e   /* Yeşil — Tamamlandı */
--status-on-hold:    #9090b0   /* Gri — Beklemede */
--status-dropped:    #ef4444   /* Kırmızı — Bırakıldı */
--status-planning:   #00d4ff   /* Cyan — Planlı */

/* Gölge / Sınır */
--border-subtle: rgba(255,255,255,0.05)
--border-card:   rgba(255,255,255,0.07)
--border-input:  #3c494e
```

---

## 📐 Tipografi

```
Aile: system-ui / sans-serif (Tailwind default)
İkon: Material Symbols Outlined (Google CDN — gerekli!)

Hiyerarşi (Tailwind class → görsel boyut):
  font-display-lg   → sayfa başlıkları (detail ekranı başlık)
  font-headline-md  → progress rakamı
  font-headline-sm  → kart üst metni, aktif bölüm
  font-body-lg      → genel içerik metni
  font-body-md      → ikincil metin, alt başlıklar
  font-label-caps   → KÜÇÜKharfle yazılan etiketler (uppercase)

Min dokunma hedefi: 44px (WCAG 2.5.5) — tüm butonlar min-h-[44px]
```

---

## 🧩 Navigasyon

### Mobil — Bottom Nav (#bottom-nav, fixed bottom-0)
```
[🏠 Home] [🔍 Keşfet] [➕ Ekle] [🔔 Güncelle] [📥 İndir] [⚙️ Ayarlar]
   6 ikon, eşit genişlik, h-[64px]
   Aktif: text-[#00d4ff] + top cyan çizgi (4px, box-shadow)
   Top AppBar ayrıca var (h-16, sadece mobile, logo ortada)
```

### PC — Sidebar (#sidebar-nav, fixed left-0, w-[240px])
```
KuroWatch logo
[🏠 Home] [🔍 Search] [➕ Add] [🔔 Updates] [📥 İndirmeler] [⚙️ Settings]
   Aktif: bg-[#00d4ff]/10 + sağ kenar border-r-4 cyan
   Nav item hover: text-white + bg-white/5
   lg: breakpoint'te sidebar görünür, bottom nav gizlenir
```

### Ekran Geçiş Animasyonları
```
slideInRight  → 0.28s (sağdan gelen ekran)
slideInLeft   → 0.28s (soldan gelen ekran)
slideUp       → 0.32s (Detail ekranı)
```

---

## 🃏 Bileşen Kataloğu

### Hero Banner (HOME üstü)
```
height: 55vh, full-width, bg-cover object-position: center top
Overlays:
  top: rgba(13,13,26,0.4) vignette (top 25%)
  bottom: transparent(50%) → #0d0d1a(100%), heavy gradient
Content (absolute bottom-left, p-20px):
  - status chip: "● İZLİYORUM" amber pill, 11px uppercase
  - series title: 28px bold white, text-shadow 0 2px 8px rgba(0,0,0,0.8)
  - meta: "Anime · ★8.9 · 12/24 bölüm" — 12px #9090b0
  - progress bar: 4px, rgba(255,255,255,0.15) bg, #00d4ff fill
  - buttons: "▶ Devam Et — B.13" (primary cyan) + "ℹ Detay" (ghost cyan)
```

### Category Row (HOME satır sistemi)
```
Row header (px-16px mb-10px):
  Left: 5px colored dot + title 13px semibold uppercase letter-spacing #e1e0ff
  Right: "Tümü ›" 11px #9090b0
Row cards:
  display: flex; gap: 10px; overflow-x: auto; scrollbar-width: none;
  padding: 0 16px; scroll-snap-type: x mandatory;
  4 tam kart + %25 beşinci kart (scroll hint)
Row dots: Devam=#feb528 | Planlıyorum=#00d4ff | Anime=#00d4ff | Manga=#ffd9a1 | Manhwa=#bbc5eb | Tamamlandı=#22c55e
```

### Content Card (Row & Grid)
```
width: 140px; aspect-ratio: 2/3; border-radius: 10px; overflow: hidden;
box-shadow: 0 4px 12px rgba(0,0,0,0.4)

Katmanlar (alt→üst):
  1. Cover image: bg-cover center
  2. Sol kenar şeridi: 4px dikey, tip rengi
  3. Sağ üst tip badge: "ANIME"/"MANGA"/"MANHWA"
     9px bold uppercase, bg: type/10, border: type/25, rounded-full, px-6px py-2px
  4. Alt gradient: #1a1a2e→transparent 65%
     İçinde: başlık 11px white (2 satır truncate) + ★X.X 10px #ffd9a1
  5. Alt kenar progress bar: 3px, bg rgba(255,255,255,0.08), fill #00d4ff

Hover (scale 1.18 Netflix-level, önceki: 1.02):
  transform: scale(1.18) translateY(-14px); z-index: 20;
  box-shadow: 0 24px 48px rgba(0,0,0,0.75);
  Alt overlay açılır: "B.12/24 · 50%" + "▶ Devam Et" küçük cyan buton

NOT: overflow:hidden parent hover'ı kırar → overflow:clip + clip-path kullan
     veya hover sırasında card'ı position:fixed portal'a al
Tıklama: openDetail(id)
```

### Buttons
```
Primary (action): bg-[#00d4ff] text-[#0d0d1a] font-bold h-[44px]
  active:scale-[0.97]  shadow-[0_0_15px_rgba(0,212,255,0.2)]

Secondary (ghost): border border-[#00d4ff]/30 text-[#00d4ff]
  bg-[#00d4ff]/10  hover:bg-[#00d4ff]/20

Danger: border border-red-500/50 text-red-400 hover:bg-red-500/10

Nav button: rounded-full bg-[#16213e]/80 backdrop-blur border border-white/10
  (Detail ekranı ← ve ✏️ butonları)
```

### Filter Chips
```
Aktif:    bg-[#00d4ff]/15 border-[#00d4ff] text-[#00d4ff]
Pasif:    bg-[#1c1d37] border-white/5 text-[#9090b0]
Hover:    text-white
Boyut:    px-4 min-h-[44px] rounded
Caps:     font-label-caps uppercase
```

### Badge'ler
```
Tip badge: px-2 py-1 | background: tip rengi %10, border: %30
Durum badge: aynı stil + sol ikon (play_circle, check, pause...)
Update badge: cyan, sol üst köşe
```

### Cards / Sections
```
bg-[#1a1a2e] rounded-xl inner-glow border border-white/5
inner-glow = box-shadow: inset 0 1px 0 rgba(255,255,255,0.07)
```

### Input Fields
```
h-[44px] px-3 bg-[#0d0d1a] (veya #1a1a2e)
border border-white/5 (veya #3c494e modal içinde)
rounded-lg text-[14px] text-[#e1e0ff]
focus: outline-none + border-[#00d4ff]/50 + ring-1 ring-[#00d4ff]/30
```

### Toggle Switches
```
Track: w-10 h-6 rounded-full bg-[#31324d] border border-white/10
Dot: absolute w-4 h-4 rounded-full
  OFF: bg-[#9090b0] left-1
  ON:  bg-[#00d4ff]/80 translate-x-4
```

---

## 📱 Modaller & Overlay'ler

### Bottom Sheet (ADD, EDIT)
```
height: 85vh (add) / 80vh (edit)
bg-[#1a2123] rounded-t-xl
Tutma çubuğu: w-12 h-1.5 bg-[#3c494e] rounded-full
Backdrop: bg-black/75 backdrop-blur-[4px]
```

### Centered Modal (CONFLICT, COVER DEBUGGER)
```
max-w-md, max-h-[80vh], rounded-2xl
bg-[#1a2123] border border-white/5 ring-1 ring-white/10
Backdrop: bg-black/75 backdrop-blur-sm
```

### Video Player Modal (Netflix-level spec)
```
z-index: 200, full inset-0, bg-black

Ambient canvas (absolute fill, z-index:0):
  Video frame blurred: filter blur(60px) saturate(1.8) brightness(0.25)
  Cinema glow effect

Video (center, 16:9 max-h-90vh, z-index:1)

Top controls (hover/tap, absolute top-0, gradient rgba(0,0,0,0.7)→transparent, 80px):
  Left: "← Geri" ghost rounded white
  Center: "Serie — Bölüm N" 13px #e1e0ff
  Right: CC | Ambient[active=cyan] | Theater | PiP | Fullscreen (30px circles bg rgba(255,255,255,0.1))

Bottom controls (absolute bottom-0, gradient transparent→rgba(0,0,0,0.85), 110px):
  Progress: 4px track rgba(255,255,255,0.2), cyan fill, 14px white playhead
  Controls: ⏮ ⏪ ⏯(40px) ⏩ ⏭ | "18:34/24:10" center | volume + quality + fullscreen

Skip Intro: bottom-100px right-20px
  "INTRO'YU ATLA →" — bg #00d4ff, text #0d0d1a, 13px bold, h-38px, rounded-lg
  pulse animation: box-shadow 0 0 20px rgba(0,212,255,0.6) in/out

Auto-next card: bottom-110px left-20px, w-200px
  bg rgba(26,26,46,0.9) blur, rounded-xl, p-14px
  "Sıradaki Bölüm" 10px muted + title 15px bold + countdown bar 4px cyan + "✕ İptal"
```

### Manga Reader Modal (Netflix-level spec)
```
z-index: 200, bg #0a0a12

Sticky header (64px, bg #0d0d1a, border-bottom rgba(255,255,255,0.06)):
  Left: "← Kapat" muted
  Center: title + "N sayfa" sub
  Right: Mode pill toggle (Webtoon/Sayfa, cyan=active) | TR pill | Translate | Fullscreen

Webtoon mode:
  Images stacked full-width, no gaps, bg #0a0a12
  Right: 4px cyan scroll indicator track
  Chapter nav popup (tap): "◀ B.N" | "Bölüm N/M" | "B.N+1 ▶" — rgba(13,13,26,0.9) blur pill

Page mode:
  Single page contained centered, bg #000
  Fixed bottom bar 64px: "◀ Önceki" | "N/M" | "Sonraki ▶"
```

### Update Card (UPDATES ekranı)
```
bg #1a1a2e, rounded-xl, mx-16px mb-10px, p-14px
Layout: flex row
  Left: cover 56×80px 2:3 rounded-md
  Right:
    type badge + time "2 saat önce" right-aligned 10px muted
    title 14px bold #e1e0ff
    "Bölüm N yayınlandı" 12px muted
    site chips small
    "▶ Oku/İzle" primary 34px | "✓ Gördüm" ghost
Unread: border-l-3px #00d4ff + slightly lighter bg
Read: no border
```

### Download Item (DOWNLOADS ekranı)
```
bg #1a1a2e, rounded-xl, mx-16px mb-10px, p-14px, flex row
Left: cover 48×64px rounded
Right: title 13px bold | source 10px cyan | progress bar 6px cyan shimmer
  "N MB / M MB · X kaldı" 10px muted | speed "420 KB/s ↓" 10px green right
Far right: ⏸ | ✕ icons 28px

Completed: ✓ green large + "Tamamlandı" muted
Error: ⚠ red + "Bağlantı hatası" + "Tekrar Dene" ghost red button
```

### Search Result Card (SEARCH ekranı)
```
flex row, py-12px px-16px, border-bottom rgba(255,255,255,0.04)
Left: cover 60×90px 2:3 rounded-md
Right:
  title 14px bold white
  meta "Manhwa · 179 bölüm · ★ 9.1" 11px muted
  status badge cyan pill
  "+ Ekle" ghost cyan button right-aligned
```

### Read Overlay (Iframe)
```
z-index: 9999, fixed inset-0, bg-#000
Header: geri butonu + başlık + "Yeni Sekme" linki
<iframe> fill-height, border:none
```

---

## 🗂️ Ekran ID Referansı

| Ekran / Modal | HTML ID | Nav Yolu |
|---|---|---|
| Ana Sayfa | `#screen-home` | Bottom nav 1 |
| Arama | `#screen-search` | Bottom nav 2 |
| Detail | `#screen-detail` | Kart tıklama |
| Güncellemeler | `#screen-updates` | Bottom nav 4 |
| İndirmeler | `#screen-downloads` | Bottom nav 5 |
| İstatistikler | `#screen-stats` | Settings kısayolu |
| Ayarlar | `#screen-settings` | Bottom nav 6 |
| Arşiv | `#screen-archive` | Settings → Arşiv |
| İçerik Ekle | `#modal-add` | Bottom nav 3 (modal-open) |
| İçerik Düzenle | `#modal-edit` | Detail ✏️ butonu |
| Import Çakışma | `#modal-conflict` | Settings → İçe Aktar |
| Cover Debugger | `#modal-cover-debug` | Settings → Cover Debugger |
| Video Player | `#modal-player` | Bölüm İzle butonu |
| Manga Reader | `#modal-reader` | Manga bölüm butonu |
| Read Overlay | `#read-overlay` | Site iframe açılır |

---

## ⚠️ Teknik Notlar

- **CDN:** Material Symbols Outlined Google CDN'den yükleniyor (offline çalışmaz)
- **Tailwind:** yerel `tailwind.css?v=30` (CDN yok, iyimser)
- **Safe Area:** `pb-safe` / `pt-safe` / `pb-safe-nav` CSS custom props ile
- **Scrollbar:** 4px genişlik, #3c494e renk, webkit-only
- **Hover:** Desktop hover efektleri var; mobilde `active:scale-[0.97]`
- **Animasyon:** chart-path (donut), bar-rect (bar chart) CSS keyframe
