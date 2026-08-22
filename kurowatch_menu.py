"""
KUROWATCH - IZLEME KULESI
Rich TUI Menu v2.0 - BAT_OLUSTURMA_REHBERI standardi
Eski kurowatch.bat v1.2 mantigi birebir korunmus; gorsel katman ship_menu v2 sablonu.
"""
import os, sys, subprocess, time, random, math, webbrowser, urllib.request
from datetime import datetime
from pathlib import Path

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
from rich.prompt import IntPrompt
from rich import box

console = Console()
ROOT = Path(__file__).parent.resolve()
HQ = ROOT.parent
HUB = HQ / "_hub"
KLOGGER = HUB / "shared-scripts" / "kuro_logger.bat"
LOG_FILE = HUB / "shared-logs" / "kurowatch_launcher.log"

KW_PORT = 8099
KW_URL = f"http://localhost:{KW_PORT}"

SUBTITLE = "Izleme Kulesi - Backend/Frontend Orkestrasyon"
VERSION = "v2.0"

WATCH_QUOTES = [
    "Kule gozde, sinyal guclu.",
    "Radar temiz - ufukta girinti yok.",
    "Nabiz atiyor: kule ayakta.",
    "Gozcu yerinde, kayitlar akiyor.",
]
NOW = lambda: datetime.now().strftime("%H:%M:%S")


def log(level, msg):
    try:
        if KLOGGER.exists():
            subprocess.run([str(KLOGGER), str(LOG_FILE), level, msg],
                           capture_output=True, timeout=10)
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
    return [radar_row(t * 0.8, max(console.width - 6, 50)) for _ in range(rows)]


def boot_animation():
    console.clear()
    console.print()
    title_lines = [ln for ln in pyfiglet.figlet_format("KUROWATCH", font="slant").splitlines()]

    steps = [
        ("Liman/port durumu okunuyor", KW_PORT),
        ("WSL koprusu hazirlaniyor", None),
        ("Backend nabzi kontrol ediliyor", None),
        ("Logger baglaniyor", None),
        ("Kule goreve hazir!", None),
    ]
    steps_tbl = Table.grid(padding=(0, 2))
    steps_tbl.add_column(width=3, justify="center", style="yellow")
    steps_tbl.add_column(style="white")
    steps_tbl.add_column(width=4, justify="center")

    with Live(console=console, refresh_per_second=10) as live:
        # FAZ A: banner + radar
        n_frames = 12
        for f in range(n_frames):
            reveal = min(len(title_lines), int((f / (n_frames - 1)) * len(title_lines)) + 1)
            parts = [gradient_text(ln) if ln.strip() else Text("") for ln in title_lines[:reveal]]
            parts.append(Text(""))
            parts.extend(signal_lines(f * 0.5))
            live.update(Group(*parts))
            time.sleep(0.13)

        # FAZ B: kontrol listesi + gercek veriler
        wsl_ip = get_wsl_ip()
        checks = [
            (f"Liman {KW_PORT}", "ACIK" if port_in_use() else "bos"),
            ("WSL kopru", wsl_ip or "yok"),
            ("Logger", "OK" if KLOGGER.exists() else "fallback"),
        ]
        tbl2 = Table.grid(padding=(0, 2))
        tbl2.add_column(style="cyan", justify="right")
        tbl2.add_column(style="white")
        for name, val in checks:
            tbl2.add_row(name + ":", str(val))

        for i in range(len(steps)):
            rows = []
            for j, (desc, _) in enumerate(steps):
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
                Panel(tbl2, title="[bold]KULE KONTROL[/]", border_style="green", box=box.HEAVY),
                Text(""),
                t2,
                Text(""),
                *signal_lines(i * 0.7),
            ))
            time.sleep(0.28)

    console.print()
    console.print(Align.center(Text(f"[{NOW()}] " + random.choice(WATCH_QUOTES),
                                    style="italic bright_black")))
    console.print()
    time.sleep(0.4)


# ---------------------------------------------------------------- yardimcilar (eski bat mantigi)
def port_in_use():
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"if (Get-NetTCPConnection -LocalPort {KW_PORT} -State Listen -EA 0) {{ 'Y' }} else {{ 'N' }}"],
        capture_output=True, text=True, timeout=15)
    return "Y" in (r.stdout or "")


def get_wsl_ip():
    try:
        r = subprocess.run(["wsl", "-e", "bash", "-c", "hostname -I"],
                           capture_output=True, text=True, timeout=15)
        ip = (r.stdout or "").split()
        return ip[0] if ip else None
    except Exception:
        return None


def wsl_root():
    try:
        r = subprocess.run(["wsl", "wslpath", "-u", str(ROOT)],
                           capture_output=True, text=True, timeout=15)
        return (r.stdout or "").strip()
    except Exception:
        return ""


def backend_alive():
    try:
        req = urllib.request.urlopen(f"{KW_URL}/docs", timeout=2)
        return req.status == 200
    except Exception:
        return False


def pick_url():
    """localhost relay calisiyorsa onu kullan; yoksa WSL IP'ye dus."""
    if backend_alive():
        return KW_URL
    ip = get_wsl_ip()
    if ip:
        return f"http://{ip}:{KW_PORT}"
    return KW_URL


def port_cleanup():
    subprocess.run(
        ["wsl", "bash", "-c",
         "pkill -f 'uvicorn backend.main' 2>/dev/null; fuser -k "
         f"{KW_PORT}/tcp 2>/dev/null; true"],
        capture_output=True, timeout=30)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Get-NetTCPConnection -LocalPort {KW_PORT} -State Listen -EA 0 | "
         "ForEach-Object{Stop-Process -Id $_.OwningProcess -Force -EA 0}"],
        capture_output=True, timeout=20)
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
        t = prog.add_task("Backend nabzi...", total=max_s)
        while True:
            elapsed = time.time() - start
            if backend_alive():
                prog.update(t, completed=max_s, description="Backend CANLI!")
                live.update(Group(prog, *signal_lines(elapsed)))
                return True, int(elapsed)
            if elapsed >= max_s:
                prog.update(t, description="NABIZ ALINAMADI!")
                live.update(Group(prog))
                return False, int(elapsed)
            prog.update(t, completed=int(elapsed),
                        description=f"Nabiz dinleniyor... ({int(elapsed)}s)")
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
    console.print("  [dim]5 saniye sonra bu pencere kapanacak...[/]")
    for i in range(5, 0, -1):
        console.print(f"  [dim]{i}...[/]", end="\r")
        time.sleep(1)
    sys.exit(0)


# ---------------------------------------------------------------- eylemler
def start_backend(open_browser=False):
    port_cleanup()
    root_wsl = wsl_root()
    log("INFO", f"menu: backend baslatiliyor (wsl={root_wsl})")
    console.print(f"  [cyan]>>[/] Backend (WSL) baslatiliyor...")
    if not root_wsl:
        sfx("fail")
        console.print("  [red]FAIL[/] WSL yol cozumlenemedi (wslpath).")
        log("FAIL", "wslpath cozumlemedi")
        pause_or_close()
        return
    subprocess.Popen(
        ["start", "KuroWatch-Backend",
         "wsl", "bash", "-c", f"bash '{root_wsl}/start_backend.sh'"],
        shell=True)
    ok, secs = wait_backend(60)
    url = pick_url()
    if ok:
        sfx("pass")
        log("PASS", f"backend canli ({secs}s, url={url})")
        console.print(f"  [green]PASS[/] Backend canli ({secs}s): {url}")
        if open_browser:
            webbrowser.open(url)
            console.print("  [green]>>[/] Tarayici acildi (frontend + API).")
            log("PASS", f"backend+frontend acildi (url={url}, exit 0)")
    else:
        sfx("fail")
        log("FAIL", f"backend 60s icinde kalkmadi (url denendi={url})")
        console.print("  [red]FAIL[/] Backend kalkmadi - KuroWatch-Backend penceresine bak.")


def action_full():
    console.print(Panel("[bold green]BACKEND + FRONTEND BASLAT[/]", border_style="green"))
    start_backend(open_browser=True)
    auto_close()


def action_backend():
    console.print(Panel("[bold cyan]SADECE BACKEND BASLAT[/]", border_style="cyan"))
    start_backend(open_browser=False)
    auto_close()


def action_foreground():
    console.print(Panel("[bold yellow]ON PLANDA BACKEND (Ctrl+C ile durdur)[/]", border_style="yellow"))
    root_wsl = wsl_root()
    log("INFO", f"menu: foreground backend (wsl={root_wsl})")
    cmd = (f"cd '{root_wsl}' && source /opt/kuroshin/venv/bin/activate && "
           f"exec python -m uvicorn backend.main:app --port {KW_PORT} --host 0.0.0.0 --log-level warning")
    rc = subprocess.call(["wsl", "bash", "-c", cmd])
    log("EXITCODE", f"uvicorn foreground rc={rc}")
    console.print(f"  [dim]uvicorn cikisi: rc={rc}[/]")
    pause_enter()


def action_clean():
    console.print(Panel("[bold red]PORT TEMIZLIK[/]", border_style="red"))
    was = port_in_use()
    port_cleanup()
    still = port_in_use()
    if still:
        sfx("fail")
        log("FAIL", f"port {KW_PORT} temizlenemedi")
        console.print(f"  [red]FAIL[/] Port {KW_PORT} hala dolu.")
    else:
        sfx("pass")
        log("PASS", f"port {KW_PORT} temizlendi (once={'dolu' if was else 'bostu'}, exit 0)")
        console.print(f"  [green]PASS[/] Port {KW_PORT} temiz (onceden {'doluydu' if was else 'bostu'}).")
    auto_close()


def pause_enter():
    try:
        input("  Devam icin Enter'a basin...")
    except (EOFError, OSError):
        time.sleep(1)


ACTIONS = {
    1: ("BACKEND+FRONTEND", action_full),
    2: ("SADECE BACKEND", action_backend),
    3: ("ON PLANDA BACKEND", action_foreground),
    4: ("PORT TEMIZLIK", action_clean),
}


def show_menu():
    console.clear()
    console.print()
    gradient_banner()
    header = Table.grid(expand=True, padding=(0, 1))
    header.add_column(justify="left", ratio=2)
    header.add_column(justify="center", ratio=1)
    header.add_column(justify="right", ratio=1)
    status = "[green]CANLI[/]" if port_in_use() else "[bright_black]sessiz[/]"
    header.add_row(
        f"[bold white]{SUBTITLE}[/] [dim]{VERSION}[/]",
        f"[bold yellow]Port:[/] [cyan]{KW_PORT}[/] {status}",
        f"[bold white]{NOW()}[/]",
    )
    console.print(Panel(header, border_style="green", box=box.HEAVY))
    console.print()

    items = Table(show_header=False, box=None, padding=(0, 2))
    items.add_column("No", style="bold cyan", width=4, justify="center")
    items.add_column("Islem", style="bold white", min_width=26)
    items.add_column("Aciklama", style="bright_black")
    items.add_row("[1]", "[bold green]BACKEND+FRONTEND[/]", "WSL backend + tarayici")
    items.add_row("[2]", "[bold cyan]SADECE BACKEND[/]", "Tarayici acilmaz")
    items.add_row("[3]", "[bold yellow]ON PLANDA[/]", "Loglar bu pencerede (Ctrl+C)")
    items.add_row("[4]", "[bold red]PORT TEMIZLIK[/]", f"{KW_PORT} WSL+Windows purge")
    items.add_row("[0]", "[bold red]CIKIS[/]", "Kuleden in")
    console.print(Panel(items, title="[bold white on green] IZLEME KULESI [/]",
                        border_style="green", box=box.DOUBLE_EDGE))
    console.print()
    for row in signal_lines(time.time() % 5, rows=1):
        console.print(row)
    console.print()
    console.print(Align.center(Text("Gozcunun secimi?", style="bold green")))


def _banner_texts():
    return [gradient_text(ln) for ln in
            pyfiglet.figlet_format("KUROWATCH", font="slant").splitlines() if ln.strip()]


def sail_away():
    banner = _banner_texts()
    with Live(console=console, refresh_per_second=12) as live:
        for f in range(10):
            live.update(Group(
                *banner,
                Text(""),
                *signal_lines(f * 0.6, rows=2),
            ))
            time.sleep(0.09)
    console.print(Align.center(Text("Kule gozetimde kaldi. Gozcun!", style="italic green")))
    console.print(Align.center(Text(f"KUROWATCH - {VERSION}", style="dim bright_black")))


def main():
    # otomasyon destegi: kurowatch_menu.py 4 -> dogrudan eylem
    if len(sys.argv) > 1 and sys.argv[1].strip() in "1234":
        choice = int(sys.argv[1])
        console.clear()
        ACTIONS[choice][1]()
        return
    boot_animation()
    while True:
        show_menu()
        try:
            choice = IntPrompt.ask("  Seciminiz", choices=["0","1","2","3","4"], show_choices=False)
            sfx("select")
        except KeyboardInterrupt:
            choice = 0
        except EOFError:
            choice = 0
        if choice in (0, 5):
            console.clear()
            sail_away()
            log("INFO", "menu cikis (exit 0)")
            break
        if choice in ACTIONS:
            console.clear()
            name, fn = ACTIONS[choice]
            console.print(Panel(f"[bold] {name} [/]", border_style="cyan", box=box.HEAVY))
            console.print()
            try:
                fn()
            except SystemExit:
                raise
            except Exception as e:
                sfx("fail")
                console.print(f"[bold red]HATA:[/] {e}")
                log("ERROR", f"hata [{choice}]: {e}")
                time.sleep(2)
        else:
            console.print("[red]Gecersiz secim![/]")
            time.sleep(1)


if __name__ == "__main__":
    main()
