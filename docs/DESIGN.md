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

### Content Card (Home Grid)
```
aspect-[2/3]  relative  rounded-card  overflow-hidden
bg: cover resim veya initials kutu
Sol renk şeridi: 4px, tip rengi
Sağ üst: tip badge (TYPE_COLOR)
Sol üst: "+N Site" update badge (koşullu, cyan)
Alt gradient overlay:
  - başlık (truncate)
  - ★X.X puan
  - renkli progress bar
Hover: scale(1.02) + border-[#00d4ff]/50
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

### Video Player Modal
```
z-index: 200, full inset-0, bg-black
Header: flex butonlar (CC, Ambient, Theater, PiP, Mini, Fullscreen)
Video: HTML5 <video> controls, z-index:1
Canvas: ambient-canvas, absolute, blur(40px) saturate(1.8), z-index:0
Skip Intro btn: bottom-16 right-6, z-index:10
Auto-next overlay: bottom-16 left-6, progress bar + geri sayım
```

### Manga Reader Modal
```
z-index: 200, overflow-y-auto
Header (sticky): close + başlık + mode btn + TR/JP toggle + Çevir + Fullscreen
Sayfa modu: reader-nav (fixed bottom) ile ◀ Önceki / Sonraki ▶
Webtoon modu: dikey scroll, nav gizli
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
