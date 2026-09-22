@echo off
setlocal
cd /d "%~dp0"
set "WIN7_PY=%~dp0win7\venv\Scripts\python.exe"
if not exist "%WIN7_PY%" (
    echo.
    echo Build FAILED: Win7 Python not found: %WIN7_PY%
    exit /b 1
)
set PYTHONPATH=
set PYTHONNOUSERSITE=1
set "DIST_DIR=dist\PrayerMusicGuard"
echo Building ONE-DIR to %DIST_DIR%..."
"%WIN7_PY%" -m PyInstaller --noconfirm --clean --distpath "%DIST_DIR%" PrayerMusicGuard.spec
if errorlevel 1 (
    echo.
    echo Build FAILED.
    exit /b 1
)
echo.
echo Done: %DIST_DIR%\PrayerMusicGuard\
echo.
echo Output folder contents:"
dir "%DIST_DIR%\PrayerMusicGuard" /b
if /i not "%~1"=="nopause" pause
exit /b 0
