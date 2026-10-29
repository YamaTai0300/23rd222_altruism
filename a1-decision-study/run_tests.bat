@echo off
rem  A-1 decision study v0.5 : run the bot tests (6 cases x N participants) and export CSVs
rem  Usage: run_tests.bat [N]   (default N=24 = 6 cases x 4 order cells). Run run_dev.bat once first so the venv exists.
setlocal
set "DST=%LOCALAPPDATA%\a1-decision-study_v0.5"
set "N=24"
if not "%~1"=="" set "N=%~1"
if not exist "%DST%\.venv\Scripts\otree.exe" (
  echo [ERROR] Run run_dev.bat first to create the environment.
  pause
  exit /b 1
)
set "A1_GIT_COMMIT="
for /f "delims=" %%i in ('git -C "%~dp0." rev-parse --short=12 HEAD 2^>nul') do set "A1_GIT_COMMIT=%%i"
robocopy "%~dp0." "%DST%" /MIR /NFL /NDL /NJH /NJS /XD .venv __pycache__ __temp_bots _static_root .git shots docs /XF db.sqlite3 .env __demo_links.txt >nul
cd /d "%DST%"
set "OTREE_ADMIN_PASSWORD=admin"
set "PATH=%DST%\.venv\Scripts;%PATH%"
if exist __temp_bots rmdir /s /q __temp_bots
".venv\Scripts\otree.exe" test a1_ja %N% --export __temp_bots
if errorlevel 1 (
  echo [FAIL] bot test failed - read the message above.
  pause
  exit /b 1
)
".venv\Scripts\otree.exe" test a1_en %N%
if errorlevel 1 (
  echo [FAIL] bot test ^(a1_en^) failed - read the message above.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" tools\export_check.py __temp_bots\altruism_study.csv
".venv\Scripts\python.exe" tools\run_log.py __temp_bots\altruism_study.csv --purpose bot-test --log __temp_bots\run_log_bots.csv
echo.
echo   Exported CSV: %DST%\__temp_bots\altruism_study.csv
pause
