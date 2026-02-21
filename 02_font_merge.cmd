@echo off
setlocal
cd /d "%~dp0"

set "work_dir=build"
set "merge_conf=merge_conf.csv"

echo ======================================================
echo  Skyrim Font Build Script
echo ======================================================
echo.
echo Work Directory: %work_dir%
pause

echo.
echo ------------------------------------------------------
echo Please prepare [%merge_conf%].
echo After preparation, press any key to continue.
echo ------------------------------------------------------
pause

echo.
echo [Step 2] Font Merging...
uv run builder --action run_batch_merge_font --work_dir "%work_dir%" --merge_conf "%merge_conf%"
echo.
echo Done.
echo Next step: 03_gen_variant_proccess.cmd
pause