"""
manga-image-translator subprocess sarmalayıcı.
Tüm chapter'ı tek süreçte çevirir (model her sayfada yeniden yüklenmez).
Çıktı dizini izlenerek sayfa sayfa progress callback çağrılır.
"""
import asyncio
import os
from typing import Callable, Awaitable, Optional

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

ProgressCB = Callable[[int, int], Awaitable[None]]


def list_pages(chapter_dir: str) -> list[str]:
    """Sıralı sayfa dosya listesi (sadece isimler, tam yol değil)."""
    if not os.path.isdir(chapter_dir):
        return []
    return sorted(
        f for f in os.listdir(chapter_dir)
        if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
    )


def translated_dir(chapter_dir: str) -> str:
    """Çevrilmiş sayfa dizini → chapter_dir + "_tr" """
    return chapter_dir.rstrip("/\\") + "_tr"


async def translate_chapter(
    chapter_dir: str,
    target_lang: str = "TRK",
    translator: str = "m2m100",
    progress_cb: Optional[ProgressCB] = None,
) -> tuple[bool, str]:
    """
    Tüm chapter'ı çevirir.
    Returns: (success: bool, output_dir: str)
    """
    pages = list_pages(chapter_dir)
    if not pages:
        return False, ""

    out_dir = translated_dir(chapter_dir)
    os.makedirs(out_dir, exist_ok=True)
    total = len(pages)

    cmd = [
        "python", "-m", "manga_translator",
        "--target-lang", target_lang,
        "--translator", translator,
        "--mode", "local",
        "-i", chapter_dir,
        "-o", out_dir,
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        return False, ""

    async def _monitor():
        last = 0
        while True:
            await asyncio.sleep(2)
            if os.path.isdir(out_dir):
                count = sum(
                    1 for f in os.listdir(out_dir)
                    if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
                )
                if count != last:
                    last = count
                    if progress_cb:
                        try:
                            await progress_cb(min(count, total), total)
                        except Exception:
                            pass

    monitor = asyncio.create_task(_monitor())
    await proc.wait()
    monitor.cancel()
    try:
        await monitor
    except asyncio.CancelledError:
        pass

    # Son ilerleme bildirimi
    if progress_cb:
        done = sum(
            1 for f in os.listdir(out_dir)
            if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
        ) if os.path.isdir(out_dir) else 0
        try:
            await progress_cb(done, total)
        except Exception:
            pass

    return proc.returncode == 0, out_dir
