# kurowatch — Changelog

## v1.2 (1 Ağustos 2026)

**GÖREV 2 — WSL backend düzeltmesi (kurowatch.bat/kurowatch.sh v1.2).**

- **Kök neden:** Eski `kurowatch.bat` backend'i **Windows python'uyla** başlatıyordu → Windows'ta `uvicorn` YOK → backend hiç açılmıyor (port 8099 boş). Çözüm: tüm backend menüleri **WSL tabanlı** yapıldı (`/opt/kuroshin/venv`, uvicorn orada).
- **:FRONTEND menüsü KALDIRILDI:** FastAPI zaten frontend'i `main.py`'de mount ediyor (`app.mount("/", StaticFiles(html=True))`) → ayrı `python -m http.server` gereksizdi. `kurowatch.bat` menüsü tek backend sürecine indirgendi.
- **Yeni menü (v1.2):**
  - `[1] Backend + Frontend Baslat (arka plan)` — `start_backend.sh` (WSL) + tarayıcı aç
  - `[2] Sadece Backend Baslat (arka plan)` — `start_backend.sh` (WSL)
  - `[3] Backend On Planda (Ctrl+C ile durdur)` — ön plan uvicorn (WSL)
  - `[4] Port Temizle` — WSL `pkill`/`fuser` + Windows `taskkill`
  - `[5] Cikis`
- **Argüman desteği:** `kurowatch.bat 2` gibi direkt menü seçimi (EOF'ta eski değeri korumaması için `:MENU` başında `choice=` sıfırlanıyor).
- **Düzeltilen buglar:**
  - `wsl wslpath` pipe'ının stdin'i yutması (menü seçimi boş kalıyordu) → `wslpath` kaldırıldı, sabit `/mnt/c/KuroshinHQ/kurowatch` kullanılıyor.
  - `%~1` argüman + `goto MENU` sonsuz döngü (yüzlerce log satırı) → `:CLEAN`'da argümanlıysa `goto END`.
- **Kanıt:** `start_backend.sh` → uvicorn PID, 8099 LISTENING, `/docs` 200, `/api/content` 200; WSL IP `172.25.89.7:8099` → 200.
- **Açık (wslrelay):** Windows'tan `localhost:8099` bazen 000 (wslrelay kararsız), WSL IP'den her zaman 200.
- Commit: `919ac4d` (feat: kurowatch v1.2 — WSL backend, :FRONTEND kaldirma, yeni menu, arguman destegi, wslrelay :PICK_URL toleransi + CHANGELOG v1.2). Önceki satırdaki "37e9249 (başlık referansı)" yalnızca Q5 venv taşıma commit'iydi — v1.2 değişiklikleri 919ac4d ile commit edildi.

## v1.1 (1 Ağustos 2026)

**GÖREV 1: Ortak launcher logger standardı (kuro_logger).**

- **Ortak logger:** `_hub/shared-scripts/kuro_logger.bat` + `kuro_logger.sh` entegre edildi
- **Log hedefi:** `_hub/shared-logs/kurowatch_launcher.log` (oturum başlıklı, zaman damgalı)
- **Launcher güncellemeleri:**
  - `kurowatch.bat` v1.0 → v1.1 — her menü dalında log (FULL/BACKEND/FRONTEND/CLEAN), exit code yakalama
  - `start.bat` v1.0 — başlık bloğu + logger + FATAL/WARN dalları
  - `kurowatch.sh` v1.0 → v1.1 — logger entegrasyonu (set -e uyumlu) + **Q5 venv düzeltmesi** (sistem python'u `idna` eksikti → `/opt/kuroshin/venv` aktive edildi, test ile doğrulandı: 8099 LISTENING)
  - `start_backend.sh` v1.0 — başlık bloğu + logger + **ölü yol düzeltmesi** (`/mnt/c/Kuroshin/kurowatch` → dinamik `KW_ROOT`)
- Log formatı: `YYYY-MM-DDTHH:MM:SS [SEVIYE] mesaj`
- Commit: v1.1 + v1.2 değişiklikleri birlikte `919ac4d` ile commit edildi (yukarıdaki v1.2 entry'sine bakın).

## v1.0 (30 Temmuz 2026)

**Faz F: Bağımsız repo taşıması.** GitHub'dan `C:\KuroshinHQ\kurowatch\`'a temiz clone.

- **İç hiyerarşi:** 325 dosya — Faz B subtree ile birebir eşleşiyor
- **Launcher yazıldı:** `kurowatch.bat` (Windows, menülü) + `kurowatch.sh` (WSL/Linux)
- **Versiyon başlığı:** Standart blok (repo adı, versiyon, commit hash, CHANGELOG linki)
- **Backend test:** uvicorn FastAPI başlatıldı, HTTP 200 doğrulandı
- **Önceki commit:** bfdd0cd ("chore: add pre-commit secret/PII scanner hook")
