"""
KUROWATCH - IZLEME KULESI
Rich TUI Menu v2.3 - BAT_OLUSTURMA_REHBERI standardi (15.10 3-ekran + 12a i18n)
v2.3: ekran-2 KULE AURA v2 (donen huzme + radar kubbe + kirpan gozcu + pencere
      flicker + deniz ufku radar taramasi/blip flash; programatik SCENE_W canvas).
v2.1: kule AURA animasyonu (ekran-2) + mini radar chibi ust serit (ekran-3) +
      canli menu (kaizoku v2.1 reader-thread deseni) + TR/EN L10N ([L], default EN).
Eski kurowatch.bat v1.2 mantigi birebir korunmus; otomasyon arg yolu ayni.
"""
import os, sys, subprocess, time, random, math, webbrowser, urllib.request
import threading, queue
from datetime import datetime
from pathlib import Path

# S-166 encoding fix (BAT-REHBER: pencere yonetimi Python'da): stdio UTF-8'e
# zorlanir — cp1254/1252 konsollarinda tower/radar arti 'â–ˆ' mojibake oluyordu.
os.environ.setdefault("PYTHONUTF8", "1")
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pyfiglet
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.color import Color
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box

console = Console()
ROOT = Path(__file__).parent.resolve()
HQ = ROOT.parent
HUB = HQ / "_hub"
KLOGGER = HUB / "shared-scripts" / "kuro_logger.bat"
LOG_FILE = HUB / "shared-logs" / "kurowatch_launcher.log"
LANG_FILE = ROOT / ".lang"

KW_PORT = 8099
KW_URL = f"http://localhost:{KW_PORT}"
WIDTH = min(console.width, 100)  # PANEL-WRAP kurali (15.10 k9): sabit sinir

SUBTITLE = "Izleme Kulesi - Backend/Frontend Orkestrasyon"
VERSION = "v2.3"
NOW = lambda: datetime.now().strftime("%H:%M:%S")


# ---------------------------------------------------------------- L10N (12a / 15.6)
L10N = {
    "en": {
        "subtitle": "Watch Tower - Backend/Frontend Orchestration",
        "port_lbl": "Port", "live": "LIVE", "idle": "idle",
        "prompt": "Watcher's choice?", "prompt_ask": "Choice",
        "invalid": "Invalid choice!", "err_pre": "ERROR:",
        "lang_row": "[L] Language / Dil",
        "m1": "BACKEND+FRONTEND", "m1_d": "WSL backend + browser",
        "m2": "BACKEND ONLY", "m2_d": "Browser not opened",
        "m3": "FOREGROUND", "m3_d": "Logs in this window (Ctrl+C)",
        "m4": "PORT CLEANUP", "m4_d": "{p} WSL+Windows purge",
        "m0": "EXIT", "m0_d": "Leave the tower",
        "boot_title": "TOWER CHECK",
        "steps": [
            "Reading port {p} state",
            "Preparing WSL bridge",
            "Checking backend pulse",
            "Connecting logger",
            "Tower ready for duty!",
        ],
        "chk_port": "Port {p}", "open": "open", "free": "free",
        "chk_wsl": "WSL bridge", "none": "none",
        "chk_logger": "Logger", "ok": "OK",
        "p_full": "START BACKEND + FRONTEND",
        "p_backend": "START BACKEND ONLY",
        "p_fg": "FOREGROUND BACKEND (Ctrl+C to stop)",
        "p_clean": "PORT CLEANUP",
        "starting": "Starting backend (WSL)...",
        "fail_wsl": "FAIL: WSL path could not be resolved.",
        "alive": "PASS Backend LIVE ({s}s): {u}",
        "browser": "Browser opened (frontend + API).",
        "dead": "FAIL Backend did not rise - see the KuroWatch-Backend window.",
        "pulse": "Backend pulse...", "pulse_ok": "Backend ALIVE!",
        "pulse_fail": "NO PULSE!", "pulse_wait": "Listening pulse... ({s}s)",
        "fg_exit": "uvicorn exit: rc=",
        "clean_ok": "PASS Port {p} clean (was {w}).",
        "was_busy": "busy", "was_free": "free",
        "clean_fail": "FAIL Port {p} still busy.",
        "closing": "Closing in {n}s...",
        "bye": "The tower kept watch. Watchman out!",
        "press_enter": "Press Enter to continue...",
        "quotes": [
            "Tower eyes on, signal strong.",
            "Radar clean - no blips on the horizon.",
            "Pulse detected: the tower stands.",
            "Watcher in place, records flowing.",
        ],
    },
    "tr": {
        "subtitle": "Izleme Kulesi - Backend/Frontend Orkestrasyon",
        "port_lbl": "Port", "live": "CANLI", "idle": "sessiz",
        "prompt": "Gozcunun secimi?", "prompt_ask": "Seciminiz",
        "invalid": "Gecersiz secim!", "err_pre": "HATA:",
        "lang_row": "[L] Dil / Language",
        "m1": "BACKEND+FRONTEND", "m1_d": "WSL backend + tarayici",
        "m2": "SADECE BACKEND", "m2_d": "Tarayici acilmaz",
        "m3": "ON PLANDA", "m3_d": "Loglar bu pencerede (Ctrl+C)",
        "m4": "PORT TEMIZLIK", "m4_d": "{p} WSL+Windows purge",
        "m0": "CIKIS", "m0_d": "Kuleden in",
        "boot_title": "KULE KONTROL",
        "steps": [
            "Liman/port durumu okunuyor",
            "WSL koprusu hazirlaniyor",
            "Backend nabzi kontrol ediliyor",
            "Logger baglaniyor",
            "Kule goreve hazir!",
        ],
        "chk_port": "Liman {p}", "open": "ACIK", "free": "bos",
        "chk_wsl": "WSL kopru", "none": "yok",
        "chk_logger": "Logger", "ok": "OK",
        "p_full": "BACKEND + FRONTEND BASLAT",
        "p_backend": "SADECE BACKEND BASLAT",
        "p_fg": "ON PLANDA BACKEND (Ctrl+C ile durdur)",
        "p_clean": "PORT TEMIZLIK",
        "starting": "Backend (WSL) baslatiliyor...",
        "fail_wsl": "FAIL: WSL yol cozumlenemedi.",
        "alive": "PASS Backend CANLI ({s}s): {u}",
        "browser": "Tarayici acildi (frontend + API).",
        "dead": "FAIL Backend kalkmadi - KuroWatch-Backend penceresine bak.",
        "pulse": "Backend nabzi...", "pulse_ok": "Backend CANLI!",
        "pulse_fail": "NABIZ ALINAMADI!", "pulse_wait": "Nabiz dinleniyor... ({s}s)",
        "fg_exit": "uvicorn cikisi: rc=",
        "clean_ok": "PASS Port {p} temiz (onceden {w}).",
        "was_busy": "doluydu", "was_free": "bostu",
        "clean_fail": "FAIL Port {p} hala dolu.",
        "closing": "{n} saniye sonra bu pencere kapanacak...",
        "bye": "Kule gozetimde kaldi. Gozcun!",
        "press_enter": "Devam icin Enter'a basin...",
        "quotes": [
            "Kule gozde, sinyal guclu.",
            "Radar temiz - ufukta girinti yok.",
            "Nabiz atiyor: kule ayakta.",
            "Gozcu yerinde, kayitlar akiyor.",
        ],
    },
}


def _detect_lang():
    try:
        v = LANG_FILE.read_text(encoding="utf-8").strip().lower()
        return v if v in ("tr", "en") else "en"
    except Exception:
        return "en"


_LANG = _detect_lang()


def T(key):
    return L10N[_LANG].get(key, L10N["en"].get(key, key))


def toggle_lang():
    global _LANG
    _LANG = "tr" if _LANG == "en" else "en"
    try:
        LANG_FILE.write_text(_LANG, encoding="utf-8")
    except Exception:
        pass
    log("DIL", f"lang={_LANG}")
    return _LANG


def log(level, msg):
    try:
        if KLOGGER.exists():
            subprocess.run([str(KLOGGER), str(LOG_FILE), level, msg],
                           capture_output=True, timeout=10, stdin=subprocess.DEVNULL)
        else:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with LOG_FILE.open("a", encoding="utf-8") as f:
                f.write(f"[{NOW()}] {level} {msg}\n")
    except Exception:
        pass


# ---------------------------------------------------------------- gorsel yardimcilar
def _lerp(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def gradient_text(s, c1=(40, 220, 130), c2=(70, 200, 255)):
    t = Text()
    n = max(len(s) - 1, 1)
    for i, ch in enumerate(s):
        r, g, b = _lerp(c1, c2, i / n)
        t.append(ch, style=Style(color=Color.from_rgb(r, g, b), bold=True))
    return t


def gradient_banner():
    for line in pyfiglet.figlet_format("KUROWATCH", font="slant").splitlines():
        if line.strip():
            console.print(gradient_text(line))
    console.print()


def radar_row(t, width):
    """Taranan radar seridi: hareketli parlak blok + noktalar."""
    width = max(min(width, WIDTH - 4), 40)
    txt = Text()
    head = int((t * 14) % width)
    for x in range(width):
        d = (x - head) % width
        if d == 0:
            txt.append("|", style="bold white")
        elif d < 6:
            txt.append(".", style="bold green")
        elif d < 18:
            txt.append("'", style="green")
        elif x % 7 == 0:
            txt.append("-", style="bright_black")
        else:
            txt.append(" ", style="bright_black")
    return txt


def signal_lines(t, rows=2):
    return [radar_row(t * 0.8, WIDTH - 6) for _ in range(rows)]


# ---------------------------------------------------------------- KULE AURA (ekran-2 + mini chibi)
RADAR_PHASES = ["\\|/", "-|-", "/|\\", "-|-"]
BEACON_PHASES = [".", "o", "*", "o"]
EYE_OPEN, EYE_BLINK = "(o o)", "(- -)"
# donen fener huzmesi: (sol kol, sag kol) uzunlugu — lamba etrafinda donus hissi
BEAM_PHASES = [(9, 0), (6, 0), (3, 0), (0, 3), (0, 6), (0, 9), (0, 6), (0, 3), (3, 0), (6, 0)]
STAR_XS = (4, 14, 24, 34, 62, 70, 78)
STAR_CHR = ("*", "+", ".")
BLIP_XS = (8, 21, 74, 88)
SCENE_W = max(min(WIDTH - 2, 96), 60)
TC = SCENE_W // 2  # kule merkezi sutunu


def mini_radar(t):
    """Ekran-3 ust serit chibi'si: deniz feneri kulesi + donen radar (tek satir)."""
    txt = Text()
    txt.append(BEACON_PHASES[int(t * 3) % 4], style="bold magenta")
    txt.append(RADAR_PHASES[int(t * 3) % 4], style="bold cyan")
    txt.append(BEACON_PHASES[int(t * 3) % 4], style="bold magenta")
    return txt


def tower_scene(f):
    """Ekran-2 AURA v2: izleme kulesi — donen huzme, donen radar kubbesi, kirpan
    gozcu, yanan pencereler ve deniz ufku radar taramasi (blip flash'li).
    Tum satirlar programatik SCENE_W genisliginde (deep-smoke assert uyumlu)."""
    q = f % 4
    bl, br = BEAM_PHASES[f % len(BEAM_PHASES)]

    def render(m):
        t = Text()
        for x in range(SCENE_W):
            ch, st = m.get(x, (" ", None))
            t.append(ch, style=st)
        return t

    def place(m, col, s, st):
        for i, ch in enumerate(s):
            m[col + i] = (ch, st)

    def span(col_l, col_r, ch, st, m):
        for x in range(col_l, col_r + 1):
            m[x] = (ch, st)

    # gokyuzu: parildayan yildizlar + hilal
    sky = [{}, {}]
    for si, sx in enumerate(STAR_XS):
        if sx < SCENE_W - 12:
            sky[si % 2][sx] = (STAR_CHR[(sx + f) % 3], "dim white")
    sky[0][SCENE_W - 8] = ("\u263e", "bold yellow")
    rows = [render(sky[0]), render(sky[1])]

    # donen huzme + lamba
    m = {}
    if bl:
        place(m, TC - bl, "\u2500" * bl, "bold cyan")
    if br:
        place(m, TC + 1, "\u2500" * br, "bold cyan")
    m[TC] = ("\u25c9", "bold magenta")
    rows.append(render(m))

    # direk + kubbe (icinde donen radar)
    rows.append(render({TC: ("\u2502", "cyan")}))
    m = {}
    place(m, TC - 3, "\u256d" + "\u2500" * 6 + "\u256e", "cyan")
    rows.append(render(m))
    m = {}
    m[TC - 3] = ("\u2502", "cyan")
    m[TC + 3] = ("\u2502", "cyan")
    place(m, TC - 1, RADAR_PHASES[q], "bold cyan")
    rows.append(render(m))

    # balkon + gozcu (arada kirpar)
    m = {}
    place(m, TC - 7, "\u250c" + "\u2500" * 13 + "\u2510", "green")
    rows.append(render(m))
    m = {}
    m[TC - 7] = ("\u2502", "green")
    m[TC + 7] = ("\u2502", "green")
    place(m, TC - 2, EYE_BLINK if f % 8 == 7 else EYE_OPEN, "bold white")
    rows.append(render(m))

    # korkuluk
    m = {}
    m[TC - 7] = ("\u2502", "green")
    m[TC + 7] = ("\u2502", "green")
    span(TC - 6, TC + 6, "\u254c", "dim green", m)
    rows.append(render(m))

    # kat + yanip sonen pencereler
    m = {}
    m[TC - 7] = ("\u2502", "green")
    m[TC + 7] = ("\u2502", "green")
    for wi in range(4):
        wx = TC - 6 + wi * 3
        lit = ((f >> 1) + wi) % 3 != 0
        place(m, wx, "[*]" if lit else "[ ]", "yellow" if lit else "dim green")
    rows.append(render(m))

    # govde dokusu + genis temel
    m = {}
    m[TC - 7] = ("\u2502", "green")
    m[TC + 7] = ("\u2502", "green")
    span(TC - 6, TC + 6, "\u2593", "green", m)
    rows.append(render(m))
    m = {}
    m[TC - 8] = ("\u2571", "bold green")
    m[TC + 8] = ("\u2572", "bold green")
    span(TC - 7, TC + 7, "\u2588", "bold green", m)
    rows.append(render(m))

    # deniz ufku: radar taramasi + blip flash
    head = int((f * 3) % SCENE_W)
    m = {}
    for x in range(SCENE_W):
        d = (x - head) % SCENE_W
        if d == 0:
            m[x] = ("\u25a0", "bold white")
        elif d < 5:
            m[x] = ("'", "bold green")
        elif d < 14:
            m[x] = ("\u2500", "green")
        elif any(abs(x - b) <= 1 for b in BLIP_XS if b < SCENE_W - 2):
            flashed = (head - x) % SCENE_W < 40
            m[x] = ("\u25c6", "magenta") if flashed else ("\u00b7", "dim magenta")
        else:
            m[x] = ("~", "dim cyan")
    rows.append(render(m))

    # dalga satiri
    m = {}
    for x in range(SCENE_W):
        if (x + (f >> 1)) % 7 == 0:
            m[x] = ("^", "cyan")
        elif x % 5 == 2:
            m[x] = ("~", "dim cyan")
    rows.append(render(m))

    return rows


def _skip_pressed():
    try:
        import msvcrt
        return msvcrt.kbhit()
    except Exception:
        return False


# ---------------------------------------------------------------- boot (ekran-2)
def boot_animation():
    console.clear()
    console.print()
    title_lines = [ln for ln in pyfiglet.figlet_format("KUROWATCH", font="slant").splitlines()]

    steps = [T("steps")[i].replace("{p}", str(KW_PORT)) for i in range(5)]

    with Live(console=console, refresh_per_second=10) as live:
        # FAZ A: kule sahnesi + wordmark reveal
        n_frames = 18
        for f in range(n_frames):
            if _skip_pressed():
                break
            reveal = min(len(title_lines), int((f / (n_frames - 1)) * len(title_lines)) + 1)
            parts = tower_scene(f)
            parts.append(Text(""))
            parts.extend(gradient_text(ln) if ln.strip() else Text("") for ln in title_lines[:reveal])
            parts.append(Text(""))
            parts.extend(signal_lines(f * 0.5, rows=1))
            live.update(Group(*parts))
            time.sleep(0.12)

        # FAZ B: kontrol listesi + gercek veriler
        wsl_ip = get_wsl_ip()
        checks = [
            (T("chk_port").replace("{p}", str(KW_PORT)),
             T("open") if port_in_use() else T("free")),
            (T("chk_wsl"), wsl_ip or T("none")),
            (T("chk_logger"), T("ok") if KLOGGER.exists() else "fallback"),
        ]
        tbl2 = Table.grid(padding=(0, 2))
        tbl2.add_column(style="cyan", justify="right")
        tbl2.add_column(style="white")
        for name, val in checks:
            tbl2.add_row(name + ":", str(val))

        for i in range(len(steps)):
            if _skip_pressed():
                break
            rows = []
            for j, desc in enumerate(steps):
                mark = "[green]v[/]" if j < i else ("[..]" if j == i else "")
                icon = "*" if j == i else "+"
                rows.append((icon, desc, mark))
            t2 = Table.grid(padding=(0, 2))
            t2.add_column(width=2, justify="center", style="yellow")
            t2.add_column(style="white")
            t2.add_column(width=4, justify="center")
            for ic, d, mk in rows:
                t2.add_row(ic, d, mk)
            live.update(Group(
                Panel(tbl2, title=f"[bold]{T('boot_title')}[/]", border_style="green",
                      box=box.HEAVY, width=WIDTH),
                Text(""),
                t2,
                Text(""),
            ))
            time.sleep(0.28)

    console.print()
    console.print(Align.center(Text(f"[{NOW()}] " + random.choice(T("quotes")),
                                    style="italic bright_black")))
    console.print()
    time.sleep(0.3)


# ---------------------------------------------------------------- yardimcilar (eski bat mantigi)
def port_in_use():
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"if (Get-NetTCPConnection -LocalPort {KW_PORT} -State Listen -EA 0) {{ 'Y' }} else {{ 'N' }}"],
        capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL)
    return "Y" in (r.stdout or "")


_WSL_IP_CACHE = {"ip": None, "ts": 0.0}


def get_wsl_ip():
    now = time.time()
    if _WSL_IP_CACHE["ip"] and now - _WSL_IP_CACHE["ts"] < 300:
        return _WSL_IP_CACHE["ip"]
    try:
        r = subprocess.run(["wsl", "-e", "bash", "-c", "hostname -I"],
                           capture_output=True, text=True, timeout=15,
                           stdin=subprocess.DEVNULL)  # S-166: wsl pipe stdin'i YIYORDU
        ip = (r.stdout or "").split()
        _WSL_IP_CACHE["ip"] = ip[0] if ip else None
        _WSL_IP_CACHE["ts"] = now
        return _WSL_IP_CACHE["ip"]
    except Exception:
        return None


def wsl_root():
    # wsl.exe arguman zinciri backslash'i yutar (C:\K -> C:K) -
    # forward-slash dene, olmazsa deterministik /mnt/<surucu> cevrimi.
    fwd = str(ROOT).replace("\\", "/")
    try:
        r = subprocess.run(["wsl", "wslpath", "-u", fwd],
                           capture_output=True, text=True, timeout=15,
                           stdin=subprocess.DEVNULL)
        out = (r.stdout or "").strip()
        if out.startswith("/mnt/"):
            return out
    except Exception:
        pass
    p = str(ROOT)
    if len(p) >= 2 and p[1] == ":":
        return "/mnt/" + p[0].lower() + p[2:].replace("\\", "/")
    return ""


def _alive(url):
    try:
        req = urllib.request.urlopen(f"{url}/docs", timeout=2)
        return req.status == 200
    except Exception:
        return False


def backend_alive():
    # wslrelay kararsiz: localhost relay'i iletmezse WSL IP'den dene (pick_url felsefesi)
    urls = [KW_URL]
    ip = get_wsl_ip()
    if ip:
        urls.append(f"http://{ip}:{KW_PORT}")
    return any(_alive(u) for u in urls)


def pick_url():
    """localhost relay calisiyorsa onu kullan; yoksa WSL IP'ye dus."""
    if _alive(KW_URL):
        return KW_URL
    ip = get_wsl_ip()
    if ip:
        u = f"http://{ip}:{KW_PORT}"
        if _alive(u):
            return u
    return KW_URL


def port_cleanup():
    subprocess.run(
        ["wsl", "bash", "-c",
         "pkill -f 'uvicorn backend.main' 2>/dev/null; fuser -k "
         f"{KW_PORT}/tcp 2>/dev/null; true"],
        capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Get-NetTCPConnection -LocalPort {KW_PORT} -State Listen -EA 0 | "
         "ForEach-Object{Stop-Process -Id $_.OwningProcess -Force -EA 0}"],
        capture_output=True, timeout=20, stdin=subprocess.DEVNULL)
    time.sleep(1)


def wait_backend(max_s=60):
    """Canli veriyle beklerken animasyonlu health-check dongusu."""
    start = time.time()
    with Live(console=console, refresh_per_second=8, transient=True) as live:
        prog = Progress(
            SpinnerColumn("dots", style="bold cyan"),
            TextColumn("[bold cyan]{task.description}[/]"),
            BarColumn(bar_width=44, complete_style="bold cyan"),
            TimeElapsedColumn(),
            console=console,
        )
        t = prog.add_task(T("pulse"), total=max_s)
        while True:
            elapsed = time.time() - start
            if backend_alive():
                prog.update(t, completed=max_s, description=T("pulse_ok"))
                live.update(Group(prog, *signal_lines(elapsed)))
                return True, int(elapsed)
            if elapsed >= max_s:
                prog.update(t, description=T("pulse_fail"))
                live.update(Group(prog))
                return False, int(elapsed)
            prog.update(t, completed=int(elapsed),
                        description=T("pulse_wait").replace("{s}", str(int(elapsed))))
            live.update(Group(prog, *signal_lines(elapsed)))
            time.sleep(2)


def sfx(kind):
    if os.environ.get("KURO_SILENT"):
        return
    try:
        import winsound
        if kind == "select":
            winsound.Beep(700, 35)
        elif kind == "pass":
            winsound.Beep(880, 50); winsound.Beep(1175, 70)
        elif kind == "fail":
            winsound.Beep(200, 140)
    except Exception:
        pass


def auto_close():
    for i in range(5, 0, -1):
        console.print(T("closing").replace("{n}", str(i)), end="\r")
        time.sleep(1)
    sys.exit(0)


# ---------------------------------------------------------------- eylemler
def start_backend(open_browser=False):
    port_cleanup()
    root_wsl = wsl_root()
    log("INFO", f"menu: backend baslatiliyor (wsl={root_wsl})")
    console.print(f"  [cyan]>>[/] {T('starting')}")
    if not root_wsl:
        sfx("fail")
        console.print(f"  [red]{T('fail_wsl')}[/]")
        log("FAIL", "wslpath cozumlemedi")
        pause_enter()
        return
    # cmd 'start' baslik/tirnak tuzagina dusmeden yeni konsol penceresi:
    # wsl dogrudan CREATE_NEW_CONSOLE ile acilir (pencere basligi WSL tarafinda set edilir)
    subprocess.Popen(
        ["wsl", "bash", "-c",
         f"printf '\\033]0;KuroWatch-Backend\\007'; bash '{root_wsl}/start_backend.sh'"],
        creationflags=subprocess.CREATE_NEW_CONSOLE, stdin=subprocess.DEVNULL)
    ok, secs = wait_backend(60)
    url = pick_url()
    if ok:
        sfx("pass")
        log("PASS", f"backend canli ({secs}s, url={url})")
        console.print(f"  [green]{T('alive').replace('{s}', str(secs)).replace('{u}', url)}[/]")
        if open_browser:
            webbrowser.open(url)
            console.print(f"  [green]>>[/] {T('browser')}")
            log("PASS", f"backend+frontend acildi (url={url}, exit 0)")
    else:
        sfx("fail")
        log("FAIL", f"backend 60s icinde kalkmadi (url denendi={url})")
        console.print(f"  [red]{T('dead')}[/]")


def action_full():
    console.print(Panel(f"[bold green]{T('p_full')}[/]", border_style="green", width=WIDTH))
    start_backend(open_browser=True)
    auto_close()


def action_backend():
    console.print(Panel(f"[bold cyan]{T('p_backend')}[/]", border_style="cyan", width=WIDTH))
    start_backend(open_browser=False)
    auto_close()


def action_foreground():
    console.print(Panel(f"[bold yellow]{T('p_fg')}[/]", border_style="yellow", width=WIDTH))
    root_wsl = wsl_root()
    log("INFO", f"menu: foreground backend (wsl={root_wsl})")
    cmd = (f"cd '{root_wsl}' && source /opt/kuroshin/venv/bin/activate && "
           f"exec python -m uvicorn backend.main:app --port {KW_PORT} --host 0.0.0.0 --log-level warning")
    rc = subprocess.call(["wsl", "bash", "-c", cmd])
    log("EXITCODE", f"uvicorn foreground rc={rc}")
    console.print(f"  [dim]{T('fg_exit')}{rc}[/]")
    pause_enter()


def action_clean():
    console.print(Panel(f"[bold red]{T('p_clean')}[/]", border_style="red", width=WIDTH))
    was = port_in_use()
    port_cleanup()
    still = port_in_use()
    if still:
        sfx("fail")
        log("FAIL", f"port {KW_PORT} temizlenemedi")
        console.print(f"  [red]{T('clean_fail').replace('{p}', str(KW_PORT))}[/]")
    else:
        sfx("pass")
        w = T("was_busy") if was else T("was_free")
        log("PASS", f"port 8099 temizlendi (once={'doluydu' if was else 'bostu'}, exit 0)")
        console.print(f"  [green]{T('clean_ok').replace('{p}', str(KW_PORT)).replace('{w}', w)}[/]")
    auto_close()


def pause_enter():
    try:
        input(f"  {T('press_enter')}")
    except (EOFError, OSError):
        time.sleep(1)


# ------------------------------------------------- menu-9: URL yonetimi (S-166)
import json as _json
import urllib.error


def _api(method: str, path: str, body=None):
    """Backend HTTP cagrisi â€” (status, dict) doner, hicbir sekilde patlamaz."""
    base = pick_url()
    req = urllib.request.Request(base + path, method=method)
    data = None
    if body is not None:
        data = _json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            raw = r.read().decode() or "{}"
            return r.status, _json.loads(raw)
    except urllib.error.HTTPError as e:
        raw = ""
        try:
            raw = e.read().decode()[:300]
        except Exception:
            pass
        try:
            j = _json.loads(raw)
            msg = j.get("detail") if isinstance(j, dict) else None
        except Exception:
            msg = None
        return e.code, {"detail": msg or raw or f"HTTP {e.code}"}
    except Exception as e:
        return 0, {"detail": str(e)}


def _ask(prompt: str = ""):
    """Tek kuyruktan oku â€” live_menu reader-thread'i ile yarÄ±s YOK (S-166)."""
    if prompt:
        console.print(prompt, end="")
    line = _get_line()
    return "" if line == "EOF" else line


def _prov_url(ext: str, ctype: str = "") -> str:
    if not ext:
        return "-"
    p, _, v = ext.partition(":")
    if p == "anilist":
        kind = "manga" if ctype in ("manga", "manhwa") else "anime"
        return f"https://anilist.co/{kind}/{v}"
    if p == "mal":
        kind = "manga" if ctype in ("manga", "manhwa") else "anime"
        return f"https://myanimelist.net/{kind}/{v}"
    if p == "tmdb":
        kind = "tv" if ctype == "series" else "movie"
        return f"https://www.themoviedb.org/{kind}/{v}"
    if p == "imdb":
        return f"https://www.imdb.com/title/{v}/"
    if p == "mangadex":
        return f"https://mangadex.org/title/{v}"
    return ext


_TYPE_ORDER = {"anime": 0, "manga": 1, "manhwa": 2, "series": 3, "movie": 4, "cartoon": 5, "game": 6}


def _score_of(it):
    s = it.get("my_score") or it.get("external_score") or 0
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0


def _saved_box(it):
    """Sag panel: kayitli bilgi kutusu (dinamik)."""
    my = it.get("my_score")
    ext = it.get("external_score")
    score = f"{my:.1f}" if my else (f"{ext:.1f} (ext)" if ext else "-")
    pct = it.get("my_progress_pct")
    prog = f"{it.get('my_progress') or 0}"
    if it.get("total_episodes") and it["type"] not in ("game", "movie"):
        prog += f"/{it['total_episodes']}"
    return Panel(
        f"[bold]{it.get('title_tr') or it.get('title','')}[/]\n"
        f"[dim]#{it['id']}[/] [cyan]{it.get('type','')}[/] "
        f"{it.get('status') or 'planning'}\n\n"
        f"{T('u_puan')}: [yellow]{score}[/]  {T('u_prog')}: [cyan]{prog}[/]"
        + (f" (%{pct})" if pct else "") + "\n"
        f"{T('u_col_cover')}: "
        + (f"[green]{T('u_cov_ok')}[/]" if it.get("cover_url") else f"[red]{T('u_cov_no')}[/]")
        + "\n\n"
        f"[bright_black]{_prov_url(it.get('external_id'), it.get('type',''))}[/]",
        title=f"[bold green] {T('u_saved')} [/]",
        border_style="green", box=box.DOUBLE, width=(WIDTH - 4) // 2)


def _urls_list():
    """Sirali pager (Lord istegi): kategori sirasi + puan desc; sagda kayitli bilgi."""
    st, items = _api("GET", "/api/content")
    if st != 0 and st != 200:
        sfx("fail")
        console.print(f"[red]{T('err_pre')}[/] {items.get('detail', st)}")
        return
    total = len(items)
    if not total:
        console.print(f"[yellow]{T('u_none')}[/]")
        return
    items.sort(key=lambda x: (_TYPE_ORDER.get(x.get("type", ""), 9), -_score_of(x), x["id"]))
    log("INFO", f"menu5.1 pager: {total} kayit ({T('u_sort')})")
    half = (WIDTH - 4) // 2
    for idx, it in enumerate(items, 1):
        cover = f"[green]{T('u_cov_ok')}[/]" if it.get("cover_url") else f"[red]{T('u_cov_no')}[/]"
        left = Panel(
            f"[bold white]{it.get('title_tr') or it.get('title','')}[/]\n"
            f"[dim]#{it['id']}[/]  [cyan]{it.get('type','')}[/]\n"
            f"{T('u_puan')}: {_score_of(it) or '-'}  {T('u_col_cover')}: {cover}\n"
            f"[bright_black]{_prov_url(it.get('external_id'), it.get('type',''))}[/]",
            title=f"[bold cyan] {idx}/{total} [/]",
            border_style="cyan", box=box.DOUBLE, width=half)
        duo = Table.grid(padding=(0, 2))
        duo.add_column(ratio=1)
        duo.add_column(ratio=1)
        duo.add_row(left, _saved_box(it))
        console.clear()
        console.print(duo)
        console.print(f"\n  [dim]{T('u_next_hint')}[/]")
        ch = _ask("")
        if not ch:
            continue
        low = ch.lower()
        if low in ("q", "x", "cik", "exit"):
            return
        # URL yapistirildi -> bu kartin kaynagini guncelle (Lord akisi)
        if "://" in ch:
            st2, res2 = _api("POST", "/api/content/from-url",
                             {"url": ch, "content_id": it["id"]})
            if st2 == 200 and res2.get("updated"):
                it["external_id"] = res2["external_id"]
                sfx("ok")
                console.print(f"  [green]{T('u_src_upd')}[/] #{it['id']} -> "
                              f"{_prov_url(it['external_id'], it.get('type',''))}")
                log("INFO", f"menu5.1 kaynak guncel: #{it['id']} {res2['external_id']}")
            else:
                sfx("fail")
                console.print(f"[red]{T('err_pre')}[/] {res2.get('detail', st2)}")
            _ask(f"  {T('press_enter')}")
        # diger tuslar: yok say, ayni kart kalir
    console.print(f"\n  [green]{T('u_end')} ({total})[/]")
    _ask(f"  {T('press_enter')}")


def _urls_add():
    """Bekleyen akis (Lord istegi): prompt seni bekler; 0=kayitli dogru devam,
    URL yapistirilirsa mevcut kayit etiketlenir ('GUNCEL BILGI ARTIK BU') veya
    yeni kayit acilir ('YENI EKLENDI')."""
    last = ""
    while True:
        ctx = Table.grid(padding=(0, 2))
        ctx.add_column(style="bright_black")
        ctx.add_column(style="white")
        ctx.add_row("0:", T("u_keep"))
        ctx.add_row("URL:", T("u_ask2"))
        if last:
            ctx.add_row("", "")
            ctx.add_row(T("u_son"), last)
        console.print(Panel(ctx, border_style="cyan", box=box.ROUNDED, width=WIDTH))
        s = _ask(f"\n  {T('u_ask2')} ").strip()
        if s == "0":
            console.print(f"  [green]{T('u_keep')}[/]")
            return
        if not s:
            continue
        st, res = _api("POST", "/api/content/from-url", {"url": s})
        if st == 201:
            sfx("ok")
            tag = f"[bold green]- {T('u_tag_new')} -[/]"
            log("INFO", f"menu5.2 eklendi: #{res['id']} {res['title']}")
        elif st == 409:
            import re as _re
            mnum = _re.search(r"#(\d+)", str(res.get("detail", "")))
            if mnum:
                sid = int(mnum.group(1))
                std, det = _api("GET", f"/api/content/{sid}")
                if std == 200:
                    res = det
                else:
                    res = {"id": sid, "title": str(res.get("detail"))[:60], "type": "",
                           "external_id": ""}
            sfx("ok")
            tag = f"[bold yellow]= {T('u_tag_cur')} =[/]"
            log("INFO", f"menu5.2 guncel etiket: #{res.get('id')}")
        else:
            sfx("fail")
            console.print(f"[red]{T('err_pre')}[/] {res.get('detail', st)}")
            log("ERROR", f"menu5.2: {res.get('detail')}")
            last = f"[red]{str(res.get('detail'))[:70]}[/]"
            continue
        last = Panel(
            f"{tag}\n\n"
            f"[bold white]{res.get('title','')}[/]  [dim]#{res.get('id')}[/]\n"
            f"[cyan]{res.get('type','')}[/]  {res.get('external_id','')}\n"
            f"[bright_black]{_prov_url(res.get('external_id'), res.get('type',''))}[/]",
            border_style="green" if st == 201 else "yellow",
            box=box.DOUBLE, width=WIDTH)
        console.clear()
        console.print(last)


def _urls_sites():
    flt = _ask(f"  {T('s_filter')}").lower()
    st, sites = _api("GET", "/api/sites")
    if st != 200:
        sfx("fail")
        console.print(f"[red]{T('err_pre')}[/] {sites.get('detail', st)}")
        return
    rows = [s for s in sites
            if not flt or flt in (s.get("site_url") or "").lower()
            or flt in (s.get("site_name") or "").lower()]
    shown = rows[:50]
    tbl = Table(box=box.SIMPLE_HEAVY, width=WIDTH, title=T("s_title"))
    tbl.add_column("ID", justify="right", style="cyan", width=6)
    tbl.add_column("DURUM", justify="center", width=7)
    tbl.add_column(T("s_col_site"), ratio=2, overflow="fold")
    tbl.add_column(T("s_col_content"), ratio=2, overflow="fold", style="bright_black")
    for s in shown:
        durum = "[red]OLU[/]" if s.get("is_dead") else "[green]CANLI[/]"
        tbl.add_row(str(s["id"]), durum, s.get("site_url") or "",
                    s.get("content_title") or "")
    extra = len(rows) - len(shown)
    if extra > 0:
        console.print(f"[dim]... +{extra} {T('s_more')}[/]")
    dead_n = sum(1 for s in rows if s.get("is_dead"))
    console.print(f"  [green]CANLI:[/] {len(rows) - dead_n}   [red]OLU:[/] {dead_n}")
    sid = _ask(f"  {T('s_toggle_ask')}")
    if not sid:
        return
    srow = next((s for s in rows if str(s["id"]) == sid), None)
    if not srow:
        console.print(f"[red]{T('invalid')}[/]")
        return
    act = "mark-alive" if srow.get("is_dead") else "mark-dead"
    st2, _r = _api("PATCH", f"/api/sites/{sid}/{act}")
    if st2 == 200:
        sfx("ok")
        console.print(f"  [bold green]{T('s_done')}[/] #{sid} -> "
                      f"{'CANLI' if act == 'mark-alive' else 'OLU'}")
        log("INFO", f"menu5.3 site {act}: #{sid}")
    else:
        sfx("fail")
        console.print(f"[red]{T('err_pre')}[/] {_r.get('detail', st2)}")


def action_urls():
    while True:
        console.print(Panel(
            f"  [bold cyan][1][/] {T('u_m1')}\n"
            f"  [bold cyan][2][/] {T('u_m2')}\n"
            f"  [bold cyan][3][/] {T('u_m3')}\n"
            f"  [bold red][0][/] {T('u_back')}",
            title=f"[bold white on cyan] {T('u_panel')} [/]",
            border_style="cyan", box=box.DOUBLE_EDGE, width=WIDTH))
        ch = _ask(f"\n  {T('prompt_ask')}: ")
        if ch in ("", "0"):
            return
        console.clear()
        if ch == "1":
            _urls_list()
        elif ch == "2":
            _urls_add()
        elif ch == "3":
            _urls_sites()
        else:
            console.print(f"[red]{T('invalid')}[/]")
        if _ask(f"\n  {T('press_enter')}"):
            pass
        console.clear()


L10N["en"].update({
    "m9": "URL MANAGER", "m9_d": "Media list / add from URL / downloader sites",
    "m_tower": "WATCH TOWER",
    "u_m1": "List saved media (name + source URL)",
    "u_m2": "Add content from scratch (paste URL)",
    "u_m3": "Downloader sites (dead / alive)",
    "u_back": "Back",
    "u_filter": "Filter by name (Enter=all):",
    "u_list_title": "SAVED MEDIA",
    "u_col_name": "NAME", "u_col_cover": "COV",
    "u_ask_url": "Content URL (anilist/mal/tmdb/imdb/mangadex):",
    "u_empty": "No URL given.",
    "u_added": "ADDED!",
    "s_filter": "Filter by domain (Enter=all):",
    "s_title": "DOWNLOADER SITES",
    "s_col_site": "SITE URL", "s_col_content": "CONTENT", "s_more": "more rows",
    "s_toggle_ask": "Site ID to toggle dead/alive (Enter=skip):",
    "s_done": "Updated:",
    "u_none": "No records.",
    "u_cov_ok": "cover OK", "u_cov_no": "no cover",
    "u_puan": "score", "u_prog": "progress",
    "u_next_hint": "[Enter/Space] next - [q] back to menu",
    "u_end": "End of list",
    "u_panel": "URL MANAGER", "u_saved": "SAVED INFO", "u_tag_new": "NEW - ADDED!", "u_tag_cur": "CURRENT INFO IS THIS NOW",
    "u_ask2": "Paste URL (0=back):", "u_keep": "Kept saved info.", "u_sort": "sorted: category + score desc", "u_son": "Last:", "u_src_upd": "SOURCE UPDATED:",
})

try:
    L10N["tr"].update({
        "m9": "URL YONETIMI", "m9_d": "Medya listesi / URL'den ekle / indirici siteler",
        "m_tower": "IZLEME KULESI",
        "u_m1": "Kayitli medya listesi (isim + kaynak URL)",
        "u_m2": "Sifirdan icerik ekle (URL yapistir)",
        "u_m3": "Indirici siteler (olu / canli)",
        "u_back": "Geri",
        "u_filter": "Isme gore filtrele (Enter=tumu):",
        "u_list_title": "KAYITLI MEDYA",
        "u_col_name": "ISIM", "u_col_cover": "KAPAK",
        "u_ask_url": "Icerik URL'si (anilist/mal/tmdb/imdb/mangadex):",
        "u_empty": "URL girilmedi.",
        "u_added": "EKLENDI!",
        "s_filter": "Domain'e gore filtrele (Enter=tumu):",
        "s_title": "INDIRICI SITELER",
        "s_col_site": "SITE URL", "s_col_content": "ICERIK", "s_more": "satir daha",
        "s_toggle_ask": "Olu/canli cevrilecek Site ID (Enter=gec):",
        "s_done": "Guncellendi:",
        "u_none": "Kayit yok.",
        "u_cov_ok": "kapak OK", "u_cov_no": "kapak yok",
        "u_puan": "puan", "u_prog": "ilerleme",
        "u_next_hint": "[Enter/Space] sonraki - [q] menuye don",
        "u_end": "Listenin sonu",
        "u_panel": "URL YONETIMI", "u_saved": "KAYITLI BILGI",
        "u_tag_new": "YENI EKLENDI!", "u_tag_cur": "GUNCEL BILGI ARTIK BU",
        "u_ask2": "URL yapistir (0=geri):", "u_keep": "Kayitli bilgi korundu.",
        "u_sort": "sirali: kategori + puan desc", "u_son": "Son islem:", "u_src_upd": "KAYNAK GUNCELLENDI:",
    })
except KeyError:
    pass

try:
    import urllib.parse
except ImportError:
    pass

ACTIONS = {
    "1": ("m1", "m1_d", action_full),
    "2": ("m2", "m2_d", action_backend),
    "3": ("m3", "m3_d", action_foreground),
    "4": ("m4", "m4_d", action_clean),
    "5": ("m9", "m9_d", action_urls),
}


# ---------------------------------------------------------------- ekran-3: canli menu (kaizoku v2.1 reader-thread)
def menu_frame(t):
    frame = Table.grid(padding=(0, 1))
    frame.add_column(justify="left", ratio=3)
    frame.add_column(justify="center", ratio=2)
    frame.add_column(justify="right", ratio=1)

    status = f"[bold green]{T('live')}[/]" if port_in_use() else f"[bright_black]{T('idle')}[/]"
    chibi = mini_radar(t)
    left = Table.grid(padding=(0, 1))
    left.add_column(justify="left")
    left.add_row(Text.assemble(chibi, ("  ", ""),
                               (f"{T('subtitle')} ", "bold white"),
                               (VERSION, "dim")))
    frame.add_row(left,
                  f"[bold yellow]{T('port_lbl')}:[/] [cyan]{KW_PORT}[/] {status}",
                  f"[bold white]{NOW()}[/]")

    items = Table(show_header=False, box=None, padding=(0, 2))
    items.add_column("No", style="bold cyan", width=4, justify="center")
    items.add_column("Islem", style="bold white", min_width=26)
    items.add_column("Aciklama", style="bright_black")
    for key in ("1", "2", "3", "4", "5"):
        name, desc, _ = ACTIONS[key]
        color = {"1": "bold green", "2": "bold cyan", "3": "bold yellow",
                 "4": "bold red", "5": "bold blue"}[key]
        items.add_row(f"[{key}]", f"[{color}]{T(name)}[/]",
                      T(desc).replace("{p}", str(KW_PORT)))
    items.add_row("[L]", f"[bold magenta]{T('lang_row')}[/]", "tr/en")
    items.add_row("[0]", f"[bold red]{T('m0')}[/]", T("m0_d"))

    return Group(
        Text(""),
        Panel(frame, border_style="green", box=box.HEAVY, width=WIDTH),
        Text(""),
        Panel(items, title=f"[bold white on green] {T('m_tower')} [/]",
              border_style="green", box=box.DOUBLE_EDGE, width=WIDTH),
        Text(""),
                Align.center(Text(f"{T('prompt')}", style="bold green")),
    )


def _reader(out_q):
    try:
        while True:
            line = sys.stdin.readline()
            if line == "":
                out_q.put(None)
                return
            out_q.put(line)
    except Exception:
        out_q.put(None)


# S-166 fix: TEK kalici reader-thread + TEK kuyruk. Eski desen live_menu'dan
# donunce thread'i birakip input()'a kacirdigi icin sonraki prompt'lar stdin'i
# asla alamiyordu ("1'e bastim cevap yok" dersi). Artik _ask() da ayni kuyruktan
# okur â€” yarÄ±s yok, kimse kimsenin satirini yutmaz.
_stdin_q: queue.Queue = queue.Queue()
_stdin_thread = None
_stdin_eof = False


def _ensure_reader():
    global _stdin_thread
    if _stdin_thread is None or not _stdin_thread.is_alive():
        _stdin_thread = threading.Thread(target=_reader, args=(_stdin_q,), daemon=True)
        _stdin_thread.start()


def _get_line(timeout=None):
    """Kuyruktan satir; timeout'ta None-olmayan bos sinyal. EOF -> ('EOF',)."""
    global _stdin_eof
    _ensure_reader()
    if _stdin_eof:
        return "EOF"
    try:
        line = _stdin_q.get() if timeout is None else _stdin_q.get(timeout=timeout)
    except queue.Empty:
        return None
    if line is None:
        _stdin_eof = True
        return "EOF"
    return line.strip()


def live_menu():
    """Canli menu: animasyon secim beklerken DONMEZ (reader-thread, kaizoku v2.1).
    Donus: '0'..'5', 'l', None (EOF -> zarif dusus)."""
    _ensure_reader()
    t0 = time.time()
    with Live(console=console, refresh_per_second=6, transient=False) as live:
        while True:
            live.update(menu_frame(time.time() - t0))
            line = _get_line(timeout=0.12)
            if line is None:
                continue
            if line == "EOF":
                return None
            line = line.strip().lower()
            if line == "":
                continue
            return line


def _banner_texts():
    return [gradient_text(ln) for ln in
            pyfiglet.figlet_format("KUROWATCH", font="slant").splitlines() if ln.strip()]


def sail_away():
    banner = _banner_texts()
    with Live(console=console, refresh_per_second=12) as live:
        for f in range(10):
            live.update(Group(
                *tower_scene(f),
                Text(""),
                *banner,
                Text(""),
                *signal_lines(f * 0.6, rows=1),
            ))
            time.sleep(0.09)
    console.print(Align.center(Text(T("bye"), style="italic green")))
    console.print(Align.center(Text(f"KUROWATCH - {VERSION}", style="dim bright_black")))


def main():
    # otomasyon destegi: kurowatch_menu.py 4 -> dogrudan eylem
    if len(sys.argv) > 1 and sys.argv[1].strip() in "12345":
        choice = int(sys.argv[1])
        console.clear()
        ACTIONS[str(choice)][2]()
        return
    boot_animation()
    while True:
        choice = live_menu()
        # S-166: "5" artik URL YONETIMI — cikis sadece 0/EOF
        if choice is None or choice in ("0", "q", "exit"):
            console.clear()
            sail_away()
            log("INFO", "menu cikis (exit 0)")
            break
        if choice == "l":
            toggle_lang()
            continue
        if choice in ACTIONS:
            sfx("select")
            console.clear()
            name, desc, fn = ACTIONS[choice]
            console.print(Panel(f"[bold] {T(name)} [/]", border_style="cyan",
                                box=box.HEAVY, width=WIDTH))
            console.print()
            try:
                fn()
            except SystemExit:
                raise
            except Exception as e:
                sfx("fail")
                console.print(f"[bold red]{T('err_pre')}[/] {e}")
                log("ERROR", f"hata [{choice}]: {e}")
                time.sleep(2)
        else:
            console.print(f"[red]{T('invalid')}[/]")
            time.sleep(1)


if __name__ == "__main__":
    main()

