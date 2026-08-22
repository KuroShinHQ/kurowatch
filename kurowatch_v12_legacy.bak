@echo off
:: ============================================
:: kurowatch.bat
:: Versiyon: v1.2
:: Aciklama: KuroWatch backend (uvicorn) + frontend baslatma
:: Repo: KuroShinHQ/kurowatch
:: Son guncelleme commit: 37e9249
:: Detay: docs/CHANGELOG.md
:: ============================================
setlocal enabledelayedexpansion

set "KW_ROOT=%~dp0"
set "ROOT=%~dp0..\"
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
if not "%ROOT:~-1%"=="\" set "ROOT=%ROOT%\"
set "KLOGGER=%ROOT%_hub\shared-scripts\kuro_logger.bat"
set "KLOG_FILE=%ROOT%_hub\shared-logs\kurowatch_launcher.log"
call "%KLOGGER%" "%KLOG_FILE%" init "kurowatch.bat v1.2"
set "KW_PORT=8099"
set "KW_URL=http://localhost:%KW_PORT%"
set "KW_ROOT_WSL="
for /f %%p in ('wsl wslpath -u "%KW_ROOT%" 2^>nul') do set "KW_ROOT_WSL=%%p"

set "WSLIP="
title KuroWatch Backend :%KW_PORT%

:MENU
set "choice="
if not "%~1"=="" set "choice=%~1"
cls
echo ================================================
echo   KUROWATCH v1.0
echo   Repo: KuroShinHQ/kurowatch
echo   Port: %KW_PORT%  (WSL backend)
echo ================================================
echo.
echo  1) Backend + Frontend Baslat (arka plan)
echo  2) Sadece Backend Baslat (arka plan)
echo  3) Backend On Planda (Ctrl+C ile durdur)
echo  4) Port Temizle (WSL + Windows)
echo  5) Cikis
echo.
set /p choice="Secim (1-5): "

if "%choice%"=="" goto END
if "%choice%"=="1" goto FULL
if "%choice%"=="2" goto BACKEND
if "%choice%"=="3" goto FOREGROUND
if "%choice%"=="4" goto CLEAN
if "%choice%"=="5" goto END
goto MENU

:FULL
call :PORT_CLEANUP
call "%KLOGGER%" "%KLOG_FILE%" INFO "Secim: 1 (backend + frontend, WSL)"
echo [KuroWatch] Backend (WSL) baslatiliyor...
call "%KLOGGER%" "%KLOG_FILE%" INFO "WSL yol: %KW_ROOT_WSL%"
start "KuroWatch-Backend" wsl bash -c "bash '%KW_ROOT_WSL%/start_backend.sh'"
call "%KLOGGER%" "%KLOG_FILE%" INFO "start_backend.sh baslatildi (port %KW_PORT%)"
timeout /t 5 /nobreak >nul
call :PICK_URL
echo [KuroWatch] Frontend + API: %USED_URL%
start "" "%USED_URL%"
call "%KLOGGER%" "%KLOG_FILE%" PASS "Backend + frontend baslatildi (WSL, url=%USED_URL%, exit 0)"
goto END

:BACKEND
call :PORT_CLEANUP
call "%KLOGGER%" "%KLOG_FILE%" INFO "Secim: 2 (sadece backend, WSL)"
echo [KuroWatch] Backend (WSL) arka planda baslatiliyor...
call "%KLOGGER%" "%KLOG_FILE%" INFO "WSL yol: %KW_ROOT_WSL%"
start "KuroWatch-Backend" wsl bash -c "bash '%KW_ROOT_WSL%/start_backend.sh'"
timeout /t 5 /nobreak >nul
call :PICK_URL
call "%KLOGGER%" "%KLOG_FILE%" PASS "Backend baslatildi (WSL, url=%USED_URL%, exit 0)"
echo [KuroWatch] Backend: %USED_URL%
goto END

:FOREGROUND
call :PORT_CLEANUP
call "%KLOGGER%" "%KLOG_FILE%" INFO "Secim: 3 (backend on planda, WSL)"
echo [KuroWatch] Backend on planda (Ctrl+C ile durdur)...
call "%KLOGGER%" "%KLOG_FILE%" INFO "WSL yol: %KW_ROOT_WSL%"
wsl bash -c "cd '%KW_ROOT_WSL%' && source /opt/kuroshin/venv/bin/activate && exec python -m uvicorn backend.main:app --port %KW_PORT% --host 0.0.0.0 --log-level warning"
set "RC=!ERRORLEVEL!"
call "%KLOGGER%" "%KLOG_FILE%" exitcode "uvicorn backend (on planda)" !RC!
goto END

:PICK_URL
:: localhost (wslrelay) calisiyorsa kullan, yoksa WSL IP'ye dus (wslrelay kararsiz).
set "USED_URL=http://localhost:%KW_PORT%"
curl.exe -s -o nul --max-time 2 "http://localhost:%KW_PORT%/docs" >nul 2>&1
if not errorlevel 1 goto :EOF
if not defined WSLIP for /f %%i in ('wsl -e bash -c "hostname -I"') do if not defined WSLIP set "WSLIP=%%i"
if defined WSLIP set "USED_URL=http://%WSLIP%:%KW_PORT%"
goto :EOF

:CLEAN
call "%KLOGGER%" "%KLOG_FILE%" INFO "Secim: 4 (port temizleme)"
call :PORT_CLEANUP
call "%KLOGGER%" "%KLOG_FILE%" PASS "Port %KW_PORT% temizlendi (exit 0)"
echo [KuroWatch] Port %KW_PORT% temizlendi.
if not "%~1"=="" goto END
pause
goto MENU

:PORT_CLEANUP
wsl bash -c "pkill -f 'uvicorn backend.main' 2>/dev/null; fuser -k %KW_PORT%/tcp 2>/dev/null; true" >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%KW_PORT% " ^| findstr "LISTENING"') do (
    echo [KuroWatch] Eski process kill: PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
goto :eof

:END
endlocal
