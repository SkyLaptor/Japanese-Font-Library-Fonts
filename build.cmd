@echo off
setlocal
cd /d "%~dp0"

set "work_dir=build"

echo ======================================================
echo  Skyrim Font Build Script
echo ======================================================
echo.
echo Work Directory: %work_dir%
pause

echo.
echo [Step 1] Pre-merge Processing (Optimization)...
uv run builder --action run_batch_premerge_export --work_dir "%work_dir%"
echo.
echo Done.

echo.
echo ------------------------------------------------------
echo Please prepare [merge_conf.csv].
echo After preparation, press any key to continue.
echo ------------------------------------------------------
pause

echo.
echo [Step 2] Font Merging...
uv run builder --action run_batch_merge_font --work_dir "%work_dir%"
echo.
echo Done.

echo.
echo [Step 3] Variant Generation...
uv run builder --action run_batch_variant_export --work_dir "%work_dir%"

echo.
echo [Step 4] SWF Creation...
uv run builder --action run_batch_swf_export --work_dir "%work_dir%"
echo.
echo Done.

echo.
echo Completed!!
pause