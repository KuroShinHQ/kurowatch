/*
 * KuroWatch Mono Charts v1.0 - vanilla port
 * Estetik ilham: Amicro "Mono Charts" (MIT, Syed Subhan - github.com/Subhan-code)
 *   -> yuvarlatilmis kose geometrisi + monokrom palet + minimalist tipografi
 * Bagimsizdir: app.js'e DOKUNMAZ. screen-stats gorunur oldugunda kendini cizer.
 * Veri: backend yoksa deterministik demo veri + "DEMO" rozeti; gercek veri
 *       icin window.KuroMono.setData(obj) hook'u hazirdir.
 */
(function () {
  "use strict";
  const CYAN = "#00d4ff";
  const TONES = ["#00d4ff", "#00b8e6", "#009cc4", "#0080a0", "#00647c"];

  let DATA = null; // { spark:{label,value,unit,series[]}, bullets:[{label,pct,target}], funnel:[{label,pct}] }

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
    (children || []).forEach(c => n.appendChild(c));
    return n;
  }

  function svg(tag, attrs) {
    const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const k in (attrs || {})) n.setAttribute(k, attrs[k]);
    return n;
  }

  function card(title, subtitle) {
    const c = el("div", { class: "mc-card" });
    const head = el("div", { class: "mc-card-head" });
    const t = el("div");
    t.appendChild(el("p", { class: "mc-title" })).textContent = title;
    t.appendChild(el("p", { class: "mc-sub" })).textContent = subtitle;
    head.appendChild(t);
    head.appendChild(el("span", { class: "mc-badge" })).textContent = DATA ? "" : "DEMO";
    c.appendChild(head);
    return c;
  }

  function smoothPath(pts) {
    // Catmull-Rom -> bezier, yumusak spline (mono-rounded-line tarzi)
    if (pts.length < 2) return "";
    let d = `M ${pts[0][0]},${pts[0][1]}`;
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
      const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
      d += ` C ${c1x},${c1y} ${c2x},${c2y} ${p2[0]},${p2[1]}`;
    }
    return d;
  }

  // ---- 1) SPARKLINE KPI KARTI (Mono Stat KPI Card) --------------------
  function sparklineKpi(d) {
    const s = d.spark;
    const c = card("TELEMETRI", s.label);
    const val = el("div", { class: "mc-kpi-value" });
    val.textContent = s.value + (s.unit || "");
    c.appendChild(val);
    const W = 260, H = 56, max = Math.max(...s.series), min = Math.min(...s.series);
    const rng = max - min || 1;
    const pts = s.series.map((v, i) => [8 + (i * (W - 16)) / (s.series.length - 1),
                                        H - 10 - ((v - min) / rng) * (H - 20)]);
    const svgs = svg("svg", { viewBox: `0 0 ${W} ${H}`, width: "100%", height: H });
    const gid = "mc-sg-" + Math.random().toString(36).slice(2, 7);
    const defs = svg("defs"); const grad = svg("linearGradient", { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 });
    grad.appendChild(svg("stop", { offset: "0%", "stop-color": CYAN, "stop-opacity": .35 }));
    grad.appendChild(svg("stop", { offset: "100%", "stop-color": CYAN, "stop-opacity": 0 }));
    defs.appendChild(grad); svgs.appendChild(defs);
    const area = svg("path", { d: smoothPath(pts) + ` L ${pts[pts.length - 1][0]},${H} L ${pts[0][0]},${H} Z`,
                               fill: `url(#${gid})` });
    const line = svg("path", { d: smoothPath(pts), fill: "none", stroke: CYAN,
                               "stroke-width": 2.5, "stroke-linecap": "round",
                               "stroke-linejoin": "round" });
    const dot = svg("circle", { cx: pts[pts.length - 1][0], cy: pts[pts.length - 1][1],
                                r: 3.5, fill: CYAN });
    svgs.appendChild(area); svgs.appendChild(line); svgs.appendChild(dot);
    c.appendChild(svgs);
    return c;
  }

  // ---- 2) BULLET TARGET (Mono Performance Bullet Target) --------------
  function bulletTarget(d) {
    const c = card("HEDEF KARSILASTIRMA", "benchmark marker'li performans");
    const list = el("div", { class: "mc-bullets" });
    d.bullets.forEach(b => {
      const row = el("div", { class: "mc-bullet-row" });
      const lbl = el("div", { class: "mc-bullet-lbl" });
      lbl.textContent = `${b.label}`;
      lbl.innerHTML += ` <span class="mc-pct">${Math.round(b.pct * 100)}% <em>/ %${Math.round(b.target * 100)}</em></span>`;
      const track = el("div", { class: "mc-bullet-track" });
      track.appendChild(el("div", { class: "mc-bullet-fill", style: `width:${Math.min(100, b.pct * 100)}%` }));
      const mark = el("div", { class: "mc-bullet-mark", style: `left:${Math.min(100, b.target * 100)}%` });
      track.appendChild(mark);
      row.appendChild(lbl); row.appendChild(track);
      list.appendChild(row);
    });
    c.appendChild(list);
    return c;
  }

  // ---- 3) STAGE FUNNEL (Mono Stage Funnel) ----------------------------
  function funnel(d) {
    const c = card("ASAMA HUNISI", "donusum hattı");
    const top = d.funnel[0].pct;
    d.funnel.forEach((st, i) => {
      const row = el("div", { class: "mc-funnel-row" });
      const bar = el("div", { class: "mc-funnel-bar",
                              style: `width:${(st.pct / top) * 100}%;background:${TONES[i % TONES.length]}`
                            });
      bar.appendChild(el("span")).textContent = st.label;
      const pct = el("span", { class: "mc-pct mc-funnel-pct" });
      pct.textContent = `%${Math.round(st.pct)}`;
      row.appendChild(bar); row.appendChild(pct);
      c.appendChild(row);
    });
    return c;
  }

  // ---- demo veri -------------------------------------------------------
  function demoData() {
    const wave = Array.from({ length: 24 }, (_, i) =>
      50 + 28 * Math.sin(i / 3.2) + 12 * Math.sin(i / 1.4) + (i % 5));
    return {
      spark: { label: "Haftalik izleme dakikasi", value: "1,284", unit: "dk", series: wave },
      bullets: [
        { label: "Tamamlanan seri", pct: .82, target: .75 },
        { label: "Guncelleme kapsama", pct: .65, target: .80 },
        { label: "Indirme basari", pct: .95, target: .90 },
      ],
      funnel: [
        { label: "Kesfedilen", pct: 100 },
        { label: "Izlenceye eklenen", pct: 62 },
        { label: "Baslanan", pct: 38 },
        { label: "Tamamlanan", pct: 21 },
      ],
    };
  }

  function stylesOnce() {
    if (document.getElementById("kuro-mono-style")) return;
    const st = document.createElement("style");
    st.id = "kuro-mono-style";
    st.textContent = `
#mono-charts-panel{padding:0 16px 96px}
#mono-charts-panel .mc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.mc-card{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:16px;padding:16px}
.mc-card-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.mc-title{font-size:10px;letter-spacing:.18em;font-weight:700;color:#9090b0;margin:0;text-transform:uppercase}
.mc-sub{font-size:11px;color:#6a6a86;margin:2px 0 0}
.mc-badge{font-size:9px;letter-spacing:.14em;border:1px solid rgba(0,212,255,.35);color:#00d4ff;border-radius:999px;padding:2px 8px}
.mc-kpi-value{font-size:26px;font-weight:800;color:#e1e0ff;margin:2px 0 10px}
.mc-bullets{display:flex;flex-direction:column;gap:12px;margin-top:10px}
.mc-bullet-row{display:flex;flex-direction:column;gap:5px}
.mc-bullet-lbl{font-size:11px;color:#b9b8d8;display:flex;justify-content:space-between}
.mc-pct{color:#00d4ff;font-weight:700}.mc-pct em{color:#6a6a86;font-style:normal}
.mc-bullet-track{position:relative;height:10px;background:rgba(255,255,255,.05);border-radius:999px;overflow:visible}
.mc-bullet-fill{height:100%;border-radius:999px;background:#00d4ff;opacity:.85}
.mc-bullet-mark{position:absolute;top:-3px;width:3px;height:16px;border-radius:999px;background:#e1e0ff;box-shadow:0 0 8px rgba(225,224,255,.5)}
.mc-funnel-row{display:flex;align-items:center;gap:10px;margin-top:10px}
.mc-funnel-bar{height:26px;border-radius:999px;display:flex;align-items:center;padding:0 12px;min-width:64px}
.mc-funnel-bar span{font-size:11px;font-weight:700;color:#0d0d1a;white-space:nowrap}
.mc-funnel-pct{flex-shrink:0}
.mc-enter{animation:mcEnter .45s cubic-bezier(.22,1,.36,1) both}
.mc-card:nth-child(2).mc-enter{animation-delay:.07s}.mc-card:nth-child(3).mc-enter{animation-delay:.14s}
@keyframes mcEnter{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
`;
    document.head.appendChild(st);
  }

  function renderAll() {
    const host = document.getElementById("screen-stats");
    let panel = document.getElementById("mono-charts-panel");
    if (!panel) {
      panel = el("div", { id: "mono-charts-panel" });
      host.appendChild(panel);
    }
    stylesOnce();
    panel.innerHTML = "";
    const src = DATA || demoData();
    const head = el("div", { style: "margin:6px 0 10px" });
    head.appendChild(el("h2", { class: "text-[13px] font-bold tracking-widest uppercase", style: "color:#6a6a86" }))
        .textContent = "MONO CHARTS · Telemetri";
    panel.appendChild(head);
    const grid = el("div", { class: "mc-grid" });
    [sparklineKpi(src), bulletTarget(src), funnel(src)].forEach(cardEl => {
      cardEl.classList.add("mc-enter");
      grid.appendChild(cardEl);
    });
    panel.appendChild(grid);
  }

  // ---- baglanti: app.js'e DOKUNMADEN screen-stats gorunurlugunu izle ---
  function forceShow() {
    const host = document.getElementById("screen-stats");
    if (!host) return;
    document.querySelectorAll(".screen").forEach(s => {
      s.classList.toggle("active", s.id === "screen-stats");
      s.classList.toggle("hidden", s.id !== "screen-stats");
    });
    renderAll();
  }

  function bind() {
    const host = document.getElementById("screen-stats");
    if (!host) return;
    const mo = new MutationObserver(() => {
      if (!host.classList.contains("hidden")) renderAll();
    });
    mo.observe(host, { attributes: true, attributeFilter: ["class"] });
    // Derin link: #screen-stats ile dogrudan acilis (test + paylasim yolu)
    window.addEventListener("hashchange", () => {
      if (location.hash === "#screen-stats") forceShow();
    });
    if (!host.classList.contains("hidden")) renderAll();
    else if (location.hash === "#screen-stats") forceShow();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bind);
  } else { bind(); }

  window.KuroMono = { renderAll, setData(d) { DATA = d; } };
})();
