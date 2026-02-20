@echo off
setlocal
cd /d %~dp0

set work_dir=build
set merge_cmd=merge.cmd

echo %work_dir%ディレクトリにあるフォントファイルをスカイリム用フォントに変換します。
pause

echo.
echo プリマージ処理（最適化）を実行しています...
uv run builder --action run_batch_premerge_export --work_dir %work_dir%

echo.
echo フォントのマージバッチ処理（%merge_cmd%）を実行しますか？
set /p choice="実行する場合は 'y' を入力して下さい (y/n): "
if /i "%choice%"=="y" call %merge_cmd%
if /i "%choice%"=="n" echo マージ処理の手動対応を待機しています...
pause

echo.
echo バリエーション生成を実行しています...
uv run builder --action run_batch_variant_export --work_dir %work_dir%

echo.
echo SWFファイルの作成を実行しています...
uv run builder --action run_batch_swf_export --work_dir build

pause
