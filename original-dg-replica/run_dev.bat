@echo off
rem ============================================================
rem  original-dg-replica : start the oTree dev server (Windows)
rem  Usage: run_dev.bat [port] [ja|de|en]   (language of oTree button texts)
rem  Double-click this file. See README.md section "動かし方".
rem
rem  1. copies the project to %LOCALAPPDATA%\original-dg-replica
rem     (runtime copy outside OneDrive; .venv and db.sqlite3 stay there)
rem  2. creates a Python 3.11 venv and installs requirements
rem  3. starts otree devserver and opens http://localhost:8000/demo
rem ============================================================
setlocal
set "SRC=%~dp0"
set "DST=%LOCALAPPDATA%\original-dg-replica"
set "PORT=8020"
if not "%~1"=="" set "PORT=%~1"
set "LANG=ja"
if not "%~2"=="" set "LANG=%~2"

py -3.11 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.11 was not found. Install it from https://www.python.org/downloads/
  echo         and tick "Add python.exe to PATH" / "py launcher". Python 3.13 does not work with oTree 5.
  pause
  exit /b 1
)

echo [1/3] Syncing project to %DST% ...
robocopy "%SRC%." "%DST%" /MIR /NFL /NDL /NJH /NJS /XD .venv __pycache__ __temp_bots _static_root .git shots docs /XF db.sqlite3 .env >nul
if errorlevel 8 (
  echo [ERROR] robocopy failed.
  pause
  exit /b 1
)
cd /d "%DST%"

echo [2/3] Preparing Python environment ...
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your network / proxy settings.
  pause
  exit /b 1
)

echo [3/3] Starting oTree dev server on port %PORT% ...
set "OTREE_ADMIN_PASSWORD=admin"
set "OTREE_LANGUAGE_CODE=%LANG%"
start "" cmd /c "timeout /t 6 >nul & start http://localhost:%PORT%/demo"
echo.
echo   Browser opens http://localhost:%PORT%/demo  (choose a session config)
echo   Admin: http://localhost:%PORT%/   user admin / password admin  (local only)
echo   Press Ctrl+C in this window to stop the server.
echo.
".venv\Scripts\otree.exe" devserver %PORT%
pause
