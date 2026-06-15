"""FFmpeg blackdetect filtresi ile outro sınırı tespiti."""
import asyncio
import re
from typing import Optional

_MIN_BLACK_DUR = 0.3    # en az 0.3sn siyah = sahne geçişi sayılır
_PIX_THRESHOLD = 0.05   # piksel parlaklık eşiği (0-1 arası)
_MIN_OUTRO_SEC = 30     # outro en az 30 saniye olmalı
_MAX_OUTRO_SEC = 480    # outro en fazla 8 dakika olabilir (uzun filmler için)
_SCAN_RATIO    = 0.40   # dosyanın son %40'ını tara


async def _get_duration(path: str) -> Optional[float]:
    """ffprobe ile video süresini al (saniye)."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "compact",
        "-show_entries", "format=duration",
        path,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
    except FileNotFoundError:
        return None

    if proc.returncode != 0 or not stdout:
        return None

    m = re.search(r"duration=([\d.]+)", stdout.decode("utf-8", errors="replace"))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


async def _detect_black_frames(path: str, seek_start: float) -> list[dict]:
    """
    FFmpeg blackdetect çıktısını parse eder.
    Dönen timestamp'lar seek_start'a GÖRECE değil, seek_start'tan
    itibaren geçen saniyelerdir → outro_detector _adjust eder.
    """
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "info",
        "-ss", str(seek_start),
        "-i", path,
        "-vf", f"blackdetect=d={_MIN_BLACK_DUR}:pix_th={_PIX_THRESHOLD}",
        "-an", "-f", "null", "-",
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
    except FileNotFoundError:
        return []

    pattern = re.compile(
        r"black_start:([\d.]+)\s+black_end:([\d.]+)\s+black_duration:([\d.]+)"
    )
    frames = []
    for m in pattern.finditer(stderr.decode("utf-8", errors="replace")):
        frames.append({
            "start":    float(m.group(1)),
            "end":      float(m.group(2)),
            "duration": float(m.group(3)),
        })
    return frames


async def detect_outro(path: str) -> Optional[dict]:
    """
    Returns:
        {"start": float, "end": float, "confidence": float}  — saniye cinsinden
        veya None (outro bulunamazsa)

    Algoritma:
    1. ffprobe ile video süresini al.
    2. Son %40 (min 3dk, max 8dk) kısmı ffmpeg blackdetect ile tara.
    3. Tespit edilen siyah kare geçişlerinden en sona yakın ve arkasında
       yeterli içerik (≥30sn) olan olanı bul.
    4. O geçişin BİTİŞ noktası = outro_start.
    """
    duration = await _get_duration(path)
    if not duration or duration < 90:
        return None

    scan_window = max(180.0, min(float(_MAX_OUTRO_SEC), duration * _SCAN_RATIO))
    seek_start  = max(0.0, duration - scan_window)

    raw_frames = await _detect_black_frames(path, seek_start)
    if not raw_frames:
        return None

    # Timestamp'ları dosya başından hesapla (seek_start offset ekle)
    frames = [
        {
            "start":    seek_start + f["start"],
            "end":      seek_start + f["end"],
            "duration": f["duration"],
        }
        for f in raw_frames
    ]

    # Outro adayı: geçişin bitişinden sonra en az _MIN_OUTRO_SEC kalan,
    # ve en az 0.5sn uzun bir siyah kare
    candidates = [
        f for f in frames
        if f["duration"] >= 0.5
        and (duration - f["end"]) >= _MIN_OUTRO_SEC
        and (duration - f["end"]) <= _MAX_OUTRO_SEC
    ]

    if not candidates:
        return None

    # En sona en yakın aday = outro başlangıcı
    best = max(candidates, key=lambda f: f["end"])
    outro_start  = round(best["end"], 1)
    outro_length = duration - outro_start

    if outro_length < _MIN_OUTRO_SEC or outro_length > _MAX_OUTRO_SEC:
        return None

    return {
        "start":      outro_start,
        "end":        round(duration, 1),
        "confidence": round(0.70 + min(0.25, best["duration"] / 4.0), 3),
    }
