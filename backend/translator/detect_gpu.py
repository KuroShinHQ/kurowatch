"""GPU + manga-image-translator kurulum tespiti."""
import subprocess
from typing import Optional


def _run(cmd: list[str], timeout: int = 10) -> Optional[str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def detect_gpu() -> dict:
    """
    Returns:
        {
          "available": bool,
          "name": str | None,
          "vram_mb": int | None,
          "translator_installed": bool,
          "recommended_translator": str,  # "m2m100" | "deepl"
        }
    """
    result: dict = {
        "available": False,
        "name": None,
        "vram_mb": None,
        "translator_installed": False,
        "recommended_translator": "m2m100",
    }

    # nvidia-smi kontrolü (WSL2'de NVIDIA sürücüsü varsa çalışır)
    out = _run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
    if out and out.strip():
        line = out.strip().split("\n")[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            result["available"] = True
            result["name"] = parts[0]
            try:
                result["vram_mb"] = int(parts[1])
            except ValueError:
                pass

    # manga-image-translator kurulum kontrolü
    out2 = _run(["python", "-c", "import manga_translator; print('ok')"])
    result["translator_installed"] = bool(out2 and "ok" in out2)

    return result
