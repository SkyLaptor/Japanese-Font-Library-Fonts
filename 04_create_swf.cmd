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
echo [Step 4] SWF Creation...
uv run builder --action run_batch_swf_export --work_dir "%work_dir%"
echo.
echo Done.
echo Completed!!
pause