@echo off
setlocal
cd /d %~dp0

set VERSION=1.0.1
set APP_NAME=TESVFontForge
set BUILD_DIR=dist

:: --- 設定エリア ---
:: 出力ファイル名
set OUT_NAME=%BUILD_DIR%\%APP_NAME%_v%VERSION%.7z

:: 圧縮したいフォルダやファイルをスペース区切りで指定
:: (例: assetsフォルダ, dataフォルダ, LICENSEファイル, README.md)
set TARGETS="assets" "data" "docs" "src" ".python-version" "LICENSE" "README.md" "main.py" "pyproject.toml" "run.cmd" "uv.lock"

:: 除外したいファイル（もしあれば）
:: 例: *.pdb (デバッグファイル) や thumbs.db など
set EXCLUDE=-x!data\ffdec\ -x!data\java\
:: -----------------

echo [ツールを配布用にアーカイブします]
echo 出力先: %OUT_NAME%

:: 7za.exe を実行
:: a   : アーカイブ作成
:: -t7z: 7z形式
:: -mx9: 最高圧縮レベル (1-9)
:: -y  : 上書き確認をすべて「はい」にする
7za.exe a "%OUT_NAME%" %TARGETS% -t7z -mx9 -y %EXCLUDE%

if %ERRORLEVEL% equ 0 (
    echo.
    echo ========================================
    echo  成功: %OUT_NAME% を作成しました。
    echo ========================================
) else (
    echo.
    echo [!] エラーが発生しました。
)

exit