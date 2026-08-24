"""Chromium cozumleyici — nodriver/Playwright icin platform-gercek yol (S-166 fix).

Eski bug: hardcode `~/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`
hem surum hem OS acisindan kiriktı (Windows'ta yok, WSL'de de 1208 vardi).
Simdiki siralama: env override -> ms-playwright glob -> sistem chrome'u -> None.
None donerse cagiran taraf browser_executable_path VERMEZ, nodriver kendi
otomatik algilamasina duser (crash yerine zarif dusus).
"""
import glob
import os
import shutil


def resolve_chromium_bin() -> str | None:
    # 1) acik override
    env = os.environ.get("KURO_CHROMIUM_BIN")
    if env and os.path.isfile(env):
        return env

    # 2) playwright cache (linux + windows konumlari, en yeni surum)
    patterns = []
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        patterns.append(os.path.join(local, "ms-playwright", "chromium-*", "chrome-win*", "chrome.exe"))
    else:
        patterns.append(os.path.expanduser("~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome"))
    for pat in patterns:
        hits = sorted(glob.glob(pat), reverse=True)
        if hits:
            return hits[0]

    # 3) sistem kurulumlari (WSL'de /usr/bin/chromium-browser mevcut)
    for name in ("chromium-browser", "chromium", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p

    return None
