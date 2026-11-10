@echo off
rem  A-1 decision study : run the analysis pipeline (Windows). ASCII only (cmd.exe code page).
rem  Needs R >= 4.2 and packages: tidyverse psych GPArotation lavaan boot jsonlite digest patchwork
rem    run_analysis.bat             real data:      raw\final\altruism_study_*.csv -> data\ -> output\
rem    run_analysis.bat synthetic   synthetic data: analysis\99_synthetic.R -> raw\synthetic -> data_synthetic\ -> output_synthetic\
rem    run_analysis.bat original    analysis\03_compare_original.R (OSF public data, needs network)
rem  Real and synthetic outputs go to different folders so they never mix.
setlocal
cd /d "%~dp0"
rem  Figure axis labels: Japanese by default on Windows (font Yu Gothic). For English: set A1_FIG_LANG=en
if "%A1_FIG_LANG%"=="" set "A1_FIG_LANG=ja"
if "%A1_FIG_FONT%"=="" set "A1_FIG_FONT=Yu Gothic"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=real"
if "%MODE%"=="original" ( Rscript analysis\03_compare_original.R & goto :end )
if "%MODE%"=="synthetic" (
  set "A1_RAW_DIR=raw/synthetic"
  set "A1_DATA_DIR=data_synthetic"
  set "A1_OUT_DIR=output_synthetic"
  Rscript analysis\99_synthetic.R %2 %3
  if errorlevel 1 goto :fail
)
Rscript analysis\01_clean.R
if errorlevel 1 goto :fail
Rscript analysis\02_main.R
if errorlevel 1 goto :fail
Rscript analysis\04_figures.R
if errorlevel 1 goto :fail
echo done. see results.md / analysis_notes.md / fig_*.pdf in the output folder
goto :end
:fail
echo [FAIL] see the message above
:end
pause
