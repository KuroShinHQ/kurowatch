@echo off
REM ═══════════════════════════════════════════════════════════════════
REM KuroWatch Frontend SPA Launcher
REM   - Port 8099'da HTTP server baslatir (python -m http.server)
REM   - Varsayilan tarayicida acar
REM   - Backend hazir oldugunda backend/start_backend.bat ayri calistirilir
REM ═══════════════════════════════════════════════════════════════════
setlocal

set "KW_ROOT=%~dp0"
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
    echo  [HATA] Python PATH'te bulunamadi.
    echo  KuroWatch frontend icin Python 3 gereklidir.
    pause
    exit /b 1
)

REM Frontend klasor kontrol
if not exist "%KW_ROOT%frontend\index.html" (
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

:END
endlocal
