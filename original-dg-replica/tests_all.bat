@echo off
rem  original-dg-replica : run the bot tests for every session config (4 cases each)
setlocal
set "DST=%LOCALAPPDATA%\original-dg-replica"
if not exist "%DST%\.venv\Scripts\otree.exe" (
  echo [ERROR] Run run_dev.bat first to create the environment.
  pause
  exit /b 1
)
robocopy "%~dp0." "%DST%" /MIR /NFL /NDL /NJH /NJS /XD .venv __pycache__ _static_root .git docs /XF db.sqlite3 .env >nul
cd /d "%DST%"
set "OTREE_ADMIN_PASSWORD=admin"
for %%c in (orig_study03_de orig_study09_en orig_study11_en orig_study13_de orig_study15_de orig_ja_demo) do (
  echo == %%c
  ".venv\Scripts\otree.exe" test %%c 4
  if errorlevel 1 ( echo [FAIL] %%c & pause & exit /b 1 )
)
echo All configs passed.
pause
