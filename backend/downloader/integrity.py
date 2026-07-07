import glob
import json
import os
import shutil
import subprocess


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"}
MIN_IMAGE_BYTES = 256
MIN_VIDEO_BYTES = 64 * 1024
MIN_MANGA_PAGE_BYTES = 50 * 1024

_FFPROBE_BIN = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
_WSL_FFPROFE_CACHE: dict | None = None

_KNOWN_VIDEO_CODECS = frozenset({
    "h264", "h265", "hevc", "vp9", "vp8", "av1",
    "mpeg4", "msmpeg4v2", "msmpeg4v3", "wmv1", "wmv2", "wmv3",
    "mpeg2video", "theora", "flv1", "vp6", "vp7",
})


class DownloadIntegrityError(RuntimeError):
    pass


def _read_header(path: str, size: int = 32) -> bytes:
    with open(path, "rb") as fh:
        return fh.read(size)


def ensure_regular_file(path: str, min_bytes: int, label: str) -> int:
    if not path:
        raise DownloadIntegrityError(f"{label}: file path is empty")
    if not os.path.isfile(path):
        raise DownloadIntegrityError(f"{label}: file does not exist: {path}")
    size = os.path.getsize(path)
    if size < min_bytes:
        raise DownloadIntegrityError(
            f"{label}: file is too small ({size} bytes, min {min_bytes}): {path}"
        )
    return size


def validate_image_file(path: str) -> int:
    size = ensure_regular_file(path, MIN_IMAGE_BYTES, "image")
    ext = os.path.splitext(path)[1].lower()
    header = _read_header(path, 32)

    if ext in (".jpg", ".jpeg") and not header.startswith(b"\xff\xd8"):
        raise DownloadIntegrityError(f"image: invalid JPEG header: {path}")
    if ext == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise DownloadIntegrityError(f"image: invalid PNG header: {path}")
    if ext == ".webp" and not (header.startswith(b"RIFF") and header[8:12] == b"WEBP"):
        raise DownloadIntegrityError(f"image: invalid WEBP header: {path}")
    if ext == ".avif" and b"ftyp" not in header[:16]:
        raise DownloadIntegrityError(f"image: invalid AVIF header: {path}")

    return size


def validate_manga_page(path: str) -> int:
    """Manga sayfası için minimum boyut kontrolü (UI icon/reklam filtreleme)."""
    size = ensure_regular_file(path, MIN_MANGA_PAGE_BYTES, "manga page")
    validate_image_file(path)
    return size


def validate_manga_files(files: list[str]) -> int:
    if not files:
        raise DownloadIntegrityError("manga: no page image files were downloaded")

    total = 0
    bad: list[str] = []
    for path in files:
        try:
            total += validate_manga_page(path)
        except DownloadIntegrityError as exc:
            bad.append(str(exc))

    if bad:
        raise DownloadIntegrityError("manga: invalid downloaded pages: " + " | ".join(bad[:5]))
    return total


def validate_manga_dir(dir_path: str) -> tuple[list[str], int]:
    if not dir_path or not os.path.isdir(dir_path):
        raise DownloadIntegrityError(f"manga: directory does not exist: {dir_path}")
    files = sorted(
        os.path.join(dir_path, f)
        for f in os.listdir(dir_path)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTS
    )
    return files, validate_manga_files(files)


def validate_video_file(path: str) -> int:
    size = ensure_regular_file(path, MIN_VIDEO_BYTES, "video")
    ext = os.path.splitext(path)[1].lower()
    header = _read_header(path, 32)

    if ext in (".mp4", ".m4v", ".mov") and b"ftyp" not in header[:16]:
        raise DownloadIntegrityError(f"video: invalid MP4/MOV header: {path}")
    if ext in (".mkv", ".webm") and not header.startswith(b"\x1a\x45\xdf\xa3"):
        raise DownloadIntegrityError(f"video: invalid Matroska/WebM header: {path}")
    if ext == ".avi" and not (header.startswith(b"RIFF") and header[8:12] == b"AVI "):
        raise DownloadIntegrityError(f"video: invalid AVI header: {path}")

    return size


def _to_wsl_path(win_path: str) -> str:
    p = win_path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        return f"/mnt/{p[0].lower()}{p[2:]}"
    return p


def _resolve_ffprobe_cmd(target_path: str) -> list[str] | None:
    if _FFPROBE_BIN:
        return [
            _FFPROBE_BIN, "-v", "error", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", target_path,
        ]
    if os.name == "nt":
        global _WSL_FFPROFE_CACHE
        if _WSL_FFPROFE_CACHE is None:
            wsl_exe = shutil.which("wsl") or shutil.which("wsl.exe")
            _WSL_FFPROFE_CACHE = {"exe": wsl_exe} if wsl_exe else {"exe": None}
        wsl_exe = _WSL_FFPROFE_CACHE.get("exe")
        if not wsl_exe:
            return None
        return [
            wsl_exe, "--", "ffprobe", "-v", "error", "-print_format", "json",
            "-show_streams", "-select_streams", "v:0", _to_wsl_path(target_path),
        ]
    return None


def probe_video_codec(path: str) -> dict | None:
    cmd = _resolve_ffprobe_cmd(path)
    if not cmd:
        return None
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=20)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if proc.returncode != 0:
        return {}
    try:
        data = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except (ValueError, json.JSONDecodeError):
        return {}
    streams = data.get("streams") or []
    if not streams:
        return {}
    v = streams[0]
    return {
        "codec_name": (v.get("codec_name") or "").lower(),
        "codec_long_name": v.get("codec_long_name", ""),
        "width": v.get("width"),
        "height": v.get("height"),
        "duration": v.get("duration"),
    }


def validate_video_file_playable(path: str) -> int:
    size = validate_video_file(path)
    probe = probe_video_codec(path)
    if probe is None:
        return size
    if not probe:
        raise DownloadIntegrityError(
            f"video: ffprobe found no valid video stream: {path}"
        )
    codec = probe.get("codec_name", "")
    if codec and codec not in _KNOWN_VIDEO_CODECS:
        raise DownloadIntegrityError(
            f"video: unsupported codec '{codec}': {path}"
        )
    return size


def remove_path(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    return True


def remove_video_artifacts(file_path: str) -> bool:
    if not file_path:
        return False
    removed = False
    base, _ = os.path.splitext(file_path)
    candidates = [
        file_path,
        file_path + ".part",
        base + ".vtt",
        base + ".tr.vtt",
        base + ".srt",
        base + ".tr.srt",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            remove_path(candidate)
            removed = True
    return removed


def remove_output_base_artifacts(output_base: str) -> bool:
    removed = False
    for candidate in glob.glob(output_base + ".*"):
        if os.path.exists(candidate):
            remove_path(candidate)
            removed = True
    return removed
