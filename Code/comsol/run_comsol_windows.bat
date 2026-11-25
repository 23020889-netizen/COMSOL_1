@echo off
REM ==================================================================
REM  Build + solve both gyroscope models with COMSOL Multiphysics 6.3
REM  Output: MEMS_TFG_SchemeI_Chevron_v2.mph, MEMS_TFG_SchemeII_Conventional_v2.mph
REM          + *_log.txt, *_modes.csv, *_sense_FRF_fig9.csv, *_gyro_operation.csv, *.png
REM  Options (environment variables):
REM     TFG_MESH=1 (coarse, fast check) / 2 (default) / 3 (fine)
REM     TFG_PAPER=1  -> sweep resolution of the paper (0.1 Hz near resonance, slow)
REM ==================================================================
if "%TFG_MESH%"=="" set TFG_MESH=2
set COMSOL_BIN=C:\Program Files\COMSOL\COMSOL63\Multiphysics\bin\win64
if not exist "%COMSOL_BIN%\comsolcompile.exe" (
  echo Khong tim thay COMSOL tai %COMSOL_BIN% - hay sua bien COMSOL_BIN trong file nay.
  pause
  exit /b 1
)
cd /d "%~dp0"
"%COMSOL_BIN%\comsolcompile.exe" TFG_SchemeI_Chevron.java
"%COMSOL_BIN%\comsolcompile.exe" TFG_SchemeII_Conventional.java
"%COMSOL_BIN%\comsolbatch.exe" -inputfile TFG_SchemeI_Chevron.class -nosave
"%COMSOL_BIN%\comsolbatch.exe" -inputfile TFG_SchemeII_Conventional.class -nosave
python ..\generator\compare_comsol_runs.py .
pause
