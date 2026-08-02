@echo off
REM ═══════════════════════════════════════════════════════════════════
REM start.bat
REM Versiyon: v1.0
REM Aciklama: KuroWatch Frontend SPA Launcher
REM   - Port 8099'da HTTP server baslatir (python -m http.server)
REM   - Varsayilan tarayicida acar
REM   - Backend hazir oldugunda backend/start_backend.bat ayri calistirilir
REM Repo: KuroShinHQ/kurowatch
REM Son guncelleme commit: 37e9249
REM Detay: docs/CHANGELOG.md
REM ═══════════════════════════════════════════════════════════════════
setlocal enabledelayedexpansion

set "KW_ROOT=%~dp0"
set "ROOT=%~dp0..\"
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
if not "%ROOT:~-1%"=="\" set "ROOT=%ROOT%\"
set "KLOGGER=%ROOT%_hub\shared-scripts\kuro_logger.bat"
set "KLOG_FILE=%ROOT%_hub\shared-logs\kurowatch_launcher.log"
call "%KLOGGER%" "%KLOG_FILE%" init "start.bat v1.0 (frontend)"
set "KW_PORT=8099"
set "KW_URL=http://localhost:%KW_PORT%"

title KuroWatch Frontend :%KW_PORT%

echo ================================================================
echo  KuroWatch Frontend SPA
echo  Port: %KW_PORT%
echo  URL : %KW_URL%
echo  Dir : %KW_ROOT%frontend
echo ================================================================
echo.

REM Port halihazirda kullaniliyor mu kontrol et
netstat -ano | findstr ":%KW_PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    call "%KLOGGER%" "%KLOG_FILE%" WARN "Port %KW_PORT% zaten kullaniliyor — mevcut sunucu aciliyor"
    echo  [UYARI] Port %KW_PORT% halihazirda kullaniliyor.
    echo  Mevcut sunucu kullaniliyor olabilir. Tarayici aciliyor...
    echo.
    timeout /t 2 /nobreak >nul
    start "" "%KW_URL%"
    goto :END
)

REM Python kontrolu
where python >nul 2>&1
if errorlevel 1 (
    call "%KLOGGER%" "%KLOG_FILE%" FATAL "Python PATH'te bulunamadi"
    echo  [HATA] Python PATH'te bulunamadi.
    echo  KuroWatch frontend icin Python 3 gereklidir.
    pause
    exit /b 1
)

REM Frontend klasor kontrol
if not exist "%KW_ROOT%frontend\index.html" (
    call "%KLOGGER%" "%KLOG_FILE%" FATAL "frontend\index.html bulunamadi"
    echo  [HATA] frontend\index.html bulunamadi.
    echo  Beklenen yol: %KW_ROOT%frontend\index.html
    pause
    exit /b 1
)

echo  Sunucu baslatiliyor...
echo  Durdurmak icin bu pencerede Ctrl+C
echo.

REM Tarayiciyi 2sn sonra ac (sunucu hazir olsun)
start "" /b cmd /c "timeout /t 2 /nobreak >nul && start """" ""%KW_URL%"""

REM HTTP server (foreground, Ctrl+C ile durdurulur)
cd /d "%KW_ROOT%"
python -m http.server %KW_PORT% --directory frontend
set "RC=!ERRORLEVEL!"
call "%KLOGGER%" "%KLOG_FILE%" exitcode "http.server frontend" !RC!

:END
endlocal
