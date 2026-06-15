"""fpcalc wrapper — audio fingerprint üretimi."""
import asyncio
import json
import os
from typing import Optional

_FPCALC = "fpcalc"
_LIMIT_SEC = 240  # sadece ilk 4 dakika analiz et


async def get_fingerprint(path: str) -> Optional[dict]:
    """
    Returns {"duration": float, "fingerprint": list[int], "fps": float}
    fps: fingerprint frames per second (chromaprint sabit ≈ 8 fps)
    """
    cmd = [_FPCALC, "-json", "-raw", "-length", str(_LIMIT_SEC), path]
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

    try:
        data = json.loads(stdout)
        fp: list = data.get("fingerprint", [])
        dur = float(data.get("duration", 0))
        dur = min(dur, float(_LIMIT_SEC))
        if not fp or dur <= 0:
            return None
        fps = len(fp) / dur
        return {"duration": dur, "fingerprint": fp, "fps": fps}
    except (json.JSONDecodeError, ZeroDivisionError, ValueError):
        return None


def load_cached(path: str) -> Optional[dict]:
    """Önceden hesaplanmış fingerprint'i JSON'dan yükle."""
    cache = path + ".fp.json"
    if not os.path.exists(cache):
        return None
    try:
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_cache(path: str, data: dict) -> None:
    """Fingerprint'i JSON'a kaydet."""
    cache = path + ".fp.json"
    try:
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass


async def fingerprint_file(path: str) -> Optional[dict]:
    """Cache'den yükle veya hesapla + kaydet."""
    cached = load_cached(path)
    if cached:
        return cached
    data = await get_fingerprint(path)
    if data:
        save_cache(path, data)
    return data
