@echo off
:: ============================================
:: kurowatch.bat
:: Versiyon: v1.0
:: Aciklama: KuroWatch backend (uvicorn) + frontend baslatma
:: Repo: KuroShinHQ/kurowatch
:: Son guncelleme commit: bfdd0cd ("chore: add pre-commit secret/PII scanner hook")
:: Detay: docs/CHANGELOG.md
:: ============================================
setlocal enabledelayedexpansion

set "KW_ROOT=%~dp0"
set "KW_PORT=8099"
set "KW_URL=http://localhost:%KW_PORT%"

title KuroWatch Backend :%KW_PORT%

:MENU
cls
echo ================================================
echo   KUROWATCH v1.0
echo   Repo: KuroShinHQ/kurowatch
echo   Port: %KW_PORT%
echo ================================================
echo.
echo  1) Backend + Frontend Baslat
echo  2) Sadece Backend (uvicorn)
echo  3) Sadece Frontend (HTTP server)
echo  4) Port Temizle (taskkill)
echo  5) Cikis
echo.
set /p choice="Secim (1-5): "

if "%choice%"=="1" goto FULL
if "%choice%"=="2" goto BACKEND
if "%choice%"=="3" goto FRONTEND
if "%choice%"=="4" goto CLEAN
if "%choice%"=="5" goto END
goto MENU

:FULL
call :PORT_CLEANUP
echo [KuroWatch] Backend baslatiliyor...
start "KuroWatch-Backend" cmd /c "cd /d "%KW_ROOT%" && python -m uvicorn backend.main:app --port %KW_PORT% --host 0.0.0.0 --log-level warning 2>&1"
echo [KuroWatch] Backend baslatildi (PID: !ERRORLEVEL!)
timeout /t 3 /nobreak >nul
echo [KuroWatch] Frontend aciliyor...
start "" "%KW_URL%"
echo [KuroWatch] http://localhost:%KW_PORT%
goto END

:BACKEND
call :PORT_CLEANUP
echo [KuroWatch] Backend baslatiliyor (on planda, Ctrl+C ile durdur)...
cd /d "%KW_ROOT%"
python -m uvicorn backend.main:app --port %KW_PORT% --host 0.0.0.0 --log-level warning
goto END

:FRONTEND
echo [KuroWatch] Frontend HTTP server baslatiliyor...
start "" http://localhost:8099
cd /d "%KW_ROOT%"
python -m http.server 8099 --directory frontend
goto END

:CLEAN
call :PORT_CLEANUP
echo [KuroWatch] Port %KW_PORT% temizlendi.
pause
goto MENU

:PORT_CLEANUP
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%KW_PORT% " ^| findstr "LISTENING"') do (
    echo [KuroWatch] Eski process kill: PID %%a
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul
goto :eof

:END
endlocal
