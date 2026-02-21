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

echo 英椎行書
fontforge %merge_script% ^
%work_dir%\acgyosyo\acgyosyo%premerge_flag%.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
-o %work_dir%\acgyosyo\acgyosyo%merged_flag%.ttf

echo あんずもじ
fontforge %merge_script% ^
%work_dir%\apricot\apricot%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
-o %work_dir%\apricot\apricot%merged_flag%.ttf

echo あんずもじ等幅
fontforge %merge_script% ^
%work_dir%\apricot-mono\apricot-mono%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_medium%premerge_flag%.ttf ^
-o %work_dir%\apricot-mono\apricot-mono%merged_flag%.ttf

echo しねきゃぷしょん
fontforge %merge_script% ^
%work_dir%\cinecaption\cinecaption%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
-o %work_dir%\cinecaption\cinecaption%merged_flag%.ttf

echo 源柔ゴシック
copy %work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%merged_flag%.ttf
copy %work_dir%\genjyuu-gothic\genjyuu-gothic_bold%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_bold%merged_flag%.ttf
copy %work_dir%\genjyuu-gothic\genjyuu-gothic_heavy%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_heavy%merged_flag%.ttf

echo 源柔ゴシック等幅
copy %work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_medium%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_medium%merged_flag%.ttf
copy %work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_bold%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_bold%merged_flag%.ttf
copy %work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_heavy%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic-mono\genjyuu-gothic-mono_heavy%merged_flag%.ttf

echo 源真ゴシック
copy %work_dir%\genshin-gothic\genshin-gothic_medium%premerge_flag%.ttf ^
%work_dir%\genshin-gothic\genshin-gothic_medium%merged_flag%.ttf
copy %work_dir%\genshin-gothic\genshin-gothic_bold%premerge_flag%.ttf ^
%work_dir%\genshin-gothic\genshin-gothic_bold%merged_flag%.ttf
copy %work_dir%\genshin-gothic\genshin-gothic_heavy%premerge_flag%.ttf ^
%work_dir%\genshin-gothic\genshin-gothic_heavy%merged_flag%.ttf

echo 源真ゴシック等幅
copy %work_dir%\genshin-gothic-mono\genshin-gothic-mono_medium%premerge_flag%.ttf ^
%work_dir%\genshin-gothic-mono\genshin-gothic-mono_medium%merged_flag%.ttf
copy %work_dir%\genshin-gothic-mono\genshin-gothic-mono_bold%premerge_flag%.ttf ^
%work_dir%\genshin-gothic-mono\genshin-gothic-mono_bold%merged_flag%.ttf
copy %work_dir%\genshin-gothic-mono\genshin-gothic-mono_heavy%premerge_flag%.ttf ^
%work_dir%\genshin-gothic-mono\genshin-gothic-mono_heavy%merged_flag%.ttf

echo 白源等幅
copy %work_dir%\hackgen-mono\hackgen-mono_regular%premerge_flag%.ttf ^
%work_dir%\hackgen-mono\hackgen-mono_regular%merged_flag%.ttf
copy %work_dir%\hackgen-mono\hackgen-mono_bold%premerge_flag%.ttf ^
%work_dir%\hackgen-mono\hackgen-mono_bold%merged_flag%.ttf

echo じゆうちょう
fontforge %merge_script% ^
%work_dir%\jiyucho\jiyucho%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_heavy%premerge_flag%.ttf ^
-o %work_dir%\jiyucho\jiyucho%merged_flag%.ttf

echo ロアフレンドリーEvery
fontforge %merge_script% ^
%work_dir%\lore-friendly-every\lore-friendly-every%premerge_flag%.ttf ^
%work_dir%\dfp-kakutaihi\dfp-kakutaihi%premerge_flag%.ttf ^
-o %work_dir%\lore-friendly-every\lore-friendly-every%premerge_flag%2.ttf
fontforge %merge_script% ^
%work_dir%\lore-friendly-every\lore-friendly-every%premerge_flag%2.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
-o %work_dir%\lore-friendly-every\lore-friendly-every%merged_flag%.ttf

echo ロアフレンドリーHandwrite
fontforge %merge_script% ^
%work_dir%\lore-friendly-handwrite\lore-friendly-handwrite%premerge_flag%.ttf ^
%work_dir%\dfp-gyosho\dfp-gyosho%premerge_flag%.ttf ^
-o %work_dir%\lore-friendly-handwrite\lore-friendly-handwrite%premerge_flag%2.ttf
fontforge %merge_script% ^
%work_dir%\lore-friendly-handwrite\lore-friendly-handwrite%premerge_flag%2.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
-o %work_dir%\lore-friendly-handwrite\lore-friendly-handwrite%premerge_flag%2.ttf

echo MPLUS
fontforge %merge_script% ^
%work_dir%\mplus\mplus_medium%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
-o %work_dir%\mplus\mplus_medium%merged_flag%.ttf
fontforge %merge_script% ^
%work_dir%\mplus\mplus_bold%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_bold%premerge_flag%.ttf ^
-o %work_dir%\mplus\mplus_bold%merged_flag%.ttf
fontforge %merge_script% ^
%work_dir%\mplus\mplus_extrabold%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_heavy%premerge_flag%.ttf ^
-o %work_dir%\mplus\mplus_extrabold%merged_flag%.ttf

echo Noto-Sans
copy %work_dir%\noto-sans\noto-sans_medium%premerge_flag%.ttf ^
%work_dir%\noto-sans\noto-sans_medium%merged_flag%.ttf
copy %work_dir%\noto-sans\noto-sans_bold%premerge_flag%.ttf ^
%work_dir%\noto-sans\noto-sans_bold%merged_flag%.ttf
copy %work_dir%\noto-sans\noto-sans_extrabold%premerge_flag%.ttf ^
%work_dir%\noto-sans\noto-sans_extrabold%merged_flag%.ttf

echo にゃしいフォント改二
fontforge %merge_script% ^
%work_dir%\nyashi-kai2\nyashi-kai2%premerge_flag%.ttf ^
%work_dir%\genjyuu-gothic\genjyuu-gothic_medium%premerge_flag%.ttf ^
-o %work_dir%\nyashi-kai2\nyashi-kai2%merged_flag%.ttf

echo しっぽり明朝
copy %work_dir%\shippori-mincho\shippori-mincho_medium%premerge_flag%.ttf ^
%work_dir%\shippori-mincho\shippori-mincho_medium%merged_flag%.ttf
copy %work_dir%\shippori-mincho\shippori-mincho_bold%premerge_flag%.ttf ^
%work_dir%\shippori-mincho\shippori-mincho_bold%merged_flag%.ttf
copy %work_dir%\shippori-mincho\shippori-mincho_extrabold%premerge_flag%.ttf ^
%work_dir%\shippori-mincho\shippori-mincho_extrabold%merged_flag%.ttf

echo バニラ日本語Bookフォント
fontforge %merge_script% ^
%work_dir%\skyrim-jp-book\skyrim-jp-book%premerge_flag%.ttf ^
%work_dir%\dfp-gihi\dfp-gihi%premerge_flag%.ttf ^
-o %work_dir%\skyrim-jp-book\skyrim-jp-book%premerge_flag%2.ttf
fontforge %merge_script% ^
%work_dir%\skyrim-jp-book\skyrim-jp-book%premerge_flag%2.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
-o %work_dir%\skyrim-jp-book\skyrim-jp-book%merged_flag%.ttf

echo バニラ日本語Everywhereフォント
fontforge %merge_script% ^
%work_dir%\skyrim-jp-every\skyrim-jp-every%premerge_flag%.ttf ^
%work_dir%\noto-sans\noto-sans_medium%premerge_flag%.ttf ^
-o %work_dir%\skyrim-jp-every\skyrim-jp-every%merged_flag%.ttf

echo バニラ日本語Handwriteフォント
fontforge %merge_script% ^
%work_dir%\skyrim-jp-handwrite\skyrim-jp-handwrite%premerge_flag%.ttf ^
%work_dir%\dfp-gyosho\dfp-gyosho%premerge_flag%.ttf ^
-o %work_dir%\skyrim-jp-handwrite\skyrim-jp-handwrite%premerge_flag%2.ttf
fontforge %merge_script% ^
%work_dir%\skyrim-jp-handwrite\skyrim-jp-handwrite%premerge_flag%2.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
-o %work_dir%\skyrim-jp-handwrite\skyrim-jp-handwrite%merged_flag%.ttf

echo 源ノ角ゴシック
copy %work_dir%\source-han-sans\source-han-sans_medium%premerge_flag%.ttf ^
%work_dir%\source-han-sans\source-han-sans_medium%merged_flag%.ttf
copy %work_dir%\source-han-sans\source-han-sans_bold%premerge_flag%.ttf ^
%work_dir%\source-han-sans\source-han-sans_bold%merged_flag%.ttf
copy %work_dir%\source-han-sans\source-han-sans_heavy%premerge_flag%.ttf ^
%work_dir%\source-han-sans\source-han-sans_heavy%merged_flag%.ttf

echo 源ノ明朝
copy %work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%merged_flag%.ttf
copy %work_dir%\source-han-serif\source-han-serif_bold%premerge_flag%.ttf ^
%work_dir%\source-han-serif\source-han-serif_bold%merged_flag%.ttf
copy %work_dir%\source-han-serif\source-han-serif_heavy%premerge_flag%.ttf ^
%work_dir%\source-han-serif\source-han-serif_heavy%merged_flag%.ttf

echo Tフォント楷書
fontforge %merge_script% ^
%work_dir%\tfont-kaisho\tfont-kaisho%premerge_flag%.ttf ^
%work_dir%\source-han-serif\source-han-serif_medium%premerge_flag%.ttf ^
-o %work_dir%\tfont-kaisho\tfont-kaisho%merged_flag%.ttf
