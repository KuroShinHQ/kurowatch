import glob
import os
import shutil


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
VIDEO_EXTS = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".m4v"}
MIN_IMAGE_BYTES = 256
MIN_VIDEO_BYTES = 64 * 1024


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


def validate_manga_files(files: list[str]) -> int:
    if not files:
        raise DownloadIntegrityError("manga: no page image files were downloaded")

    total = 0
    bad: list[str] = []
    for path in files:
        try:
            total += validate_image_file(path)
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
