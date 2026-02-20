@echo off
setlocal
cd /d %~dp0

set work_dir=build
set merge_script=src\utils\modifier\merge_font_ff.py
set premerge_flag=_premerge
set merged_flag=_merged

echo マージ作業を開始します。
echo 作業ディレクトリ: %work_dir%
pause

:: echo 英椎行書
::fontforge %merge_script% ^
::%work_dir%\font1\font1%premerge_flag%.ttf ^
::%work_dir%\font2\font2%premerge_flag%.ttf ^
::-o %work_dir%\font1\font1%merged_flag%.ttf
:: マージ不要の場合
::copy %work_dir%\font1\font1%premerge_flag%.ttf ^
::%work_dir%\font1\font1%merged_flag%.ttf
