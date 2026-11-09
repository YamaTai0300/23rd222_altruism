@echo off
rem ============================================================
rem  A-1 decision study v0.6 : start the oTree dev server (Windows)
rem  Double-click this file. See README.md section "動かし方".
rem
rem  1. copies the project to %LOCALAPPDATA%\a1-decision-study_v0.6
rem     (runtime copy outside OneDrive; .venv and db.sqlite3 stay there; v0.4 uses a different folder)
rem  2. finds Python 3.10-3.12 (A1_PYTHON / py launcher / conda env "a1" / python on PATH), creates a venv, installs requirements
rem  3. starts otree devserver; tools\ensure_room.py then creates a session in room "demo" and opens the REUSABLE link
rem     http://localhost:8000/join/<code>  (a new participant every time you open it; up to 100 times per server start)
rem     The fixed link http://localhost:8000/room/demo also works (same browser resumes the same run).
rem  Options:  run_dev.bat [port] [a1_ja|a1_en]      e.g.  run_dev.bat 8001 a1_en
rem ============================================================
setlocal
set "SRC=%~dp0"
set "DST=%LOCALAPPDATA%\a1-decision-study_v0.6"
set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"
set "CONFIG=a1_ja"
if not "%~2"=="" set "CONFIG=%~2"

rem  ---- find a Python interpreter: 3.11 preferred, 3.12 or 3.10 also work; 3.13 does not (v0.4) ----
rem   order: A1_PYTHON (full path to python.exe)  >  py -3.11 / -3.12 / -3.10 (py launcher)
rem          >  conda env "a1" (conda create -n a1 python=3.11 -y)  >  "python" on PATH if it is 3.10-3.12
set "PYEXE="
if defined A1_PYTHON if exist "%A1_PYTHON%" set "PYEXE=%A1_PYTHON%"
if not defined PYEXE call :try_py 3.11
if not defined PYEXE call :try_py 3.12
if not defined PYEXE call :try_py 3.10
if not defined PYEXE if exist "%USERPROFILE%\miniconda3\envs\a1\python.exe" set "PYEXE=%USERPROFILE%\miniconda3\envs\a1\python.exe"
if not defined PYEXE if exist "%USERPROFILE%\anaconda3\envs\a1\python.exe" set "PYEXE=%USERPROFILE%\anaconda3\envs\a1\python.exe"
if not defined PYEXE call :try_path_python
if not defined PYEXE (
  echo [ERROR] No usable Python was found. oTree 5 needs Python 3.10, 3.11 or 3.12 ^(3.13 does not work^).
  echo.
  echo   Option A: install Python 3.11 from https://www.python.org/downloads/windows/
  echo             and tick "Add python.exe to PATH" and "py launcher" in the installer. Then run this file again.
  echo   Option B: if you use Miniconda/Anaconda, open "Anaconda Prompt" and run
  echo             conda create -n a1 python=3.11 -y
  echo             then run this file again ^(the env "a1" is found automatically^).
  echo   Option C: set A1_PYTHON to the full path of a python.exe ^(3.10-3.12^) before running this file.
  echo.
  pause
  exit /b 1
)
echo Using Python: %PYEXE%
goto :found_python

:try_py
py -%1 --version >nul 2>&1
if not errorlevel 1 set "PYEXE=py -%1"
goto :eof

:try_path_python
set "PYVER="
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
if not defined PYVER goto :eof
if "%PYVER:~0,4%"=="3.10" set "PYEXE=python"
if "%PYVER:~0,4%"=="3.11" set "PYEXE=python"
if "%PYVER:~0,4%"=="3.12" set "PYEXE=python"
if defined PYEXE echo Found python %PYVER% on PATH
goto :eof

:found_python
rem  v0.3: record the git commit of the source folder (unknown when not under git)
set "A1_GIT_COMMIT="
for /f "delims=" %%i in ('git -C "%SRC%." rev-parse --short=12 HEAD 2^>nul') do set "A1_GIT_COMMIT=%%i"

echo [1/3] Syncing project to %DST% ...
robocopy "%SRC%." "%DST%" /MIR /NFL /NDL /NJH /NJS /XD .venv __pycache__ __temp_bots _static_root .git shots docs /XF db.sqlite3 .env __demo_links.txt >nul
if errorlevel 8 (
  echo [ERROR] robocopy failed.
  pause
  exit /b 1
)
cd /d "%DST%"

echo [2/3] Preparing Python environment (first time: 2-3 minutes, please wait) ...
if not exist ".venv\Scripts\python.exe" (
  if "%PYEXE:~0,3%"=="py " ( %PYEXE% -m venv .venv ) else if "%PYEXE%"=="python" ( python -m venv .venv ) else ( "%PYEXE%" -m venv .venv )
)
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] Could not create the virtual environment with %PYEXE%
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed. Check your network / proxy settings.
  pause
  exit /b 1
)

echo [3/3] Starting oTree dev server on port %PORT% ...
set "OTREE_ADMIN_PASSWORD=admin"
rem  devserver re-launches itself as "otree devserver_inner" by name, so the venv must be on PATH (WinError 2 otherwise)
set "PATH=%DST%\.venv\Scripts;%PATH%"
rem  v0.5: once the server answers (up to 5 minutes), create a session in room "demo" and open the reusable link.
rem        The links are also written to %DST%\__demo_links.txt
start "" /min ".venv\Scripts\python.exe" tools\ensure_room.py --port %PORT% --config %CONFIG% --open --wait 300 --log __demo_links.txt
echo.
echo   When the server is ready, the browser opens the REUSABLE demo link (config %CONFIG%):
echo     every time you open that link you start again as a new participant (no need to go back to /demo).
echo   Fixed link (same form as the real study):  http://localhost:%PORT%/room/demo
echo     same browser = continue the same run; private window / phone / other browser = new participant.
echo   All links:  %DST%\__demo_links.txt      Demo page: http://localhost:%PORT%/demo
echo   Admin: http://localhost:%PORT%/   user admin / password admin  (local only)
echo   Press Ctrl+C in this window to stop the server.
echo.
".venv\Scripts\otree.exe" devserver %PORT%
echo.
echo [server stopped] If it stopped right away, read the error above.
pause
