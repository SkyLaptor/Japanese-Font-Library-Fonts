# スカイリムサブセットについて

## 作成手順
1. バニラの日本語フォントSWFからFFDecを用いて、Everywhere/Book/Handwrittenの3種のフォントを取り出し、`assets\fonts\skyrim\`に配置する。

2. 取り出したフォントファイルに対し、空白グリフ削除処理を実施。

```cmd:
$ uv run optimizer --action remove_empty_glyphs -i .\assets\fonts\skyrim\1_Skyrim_JP_EveryFont_0805.ttf -o .\build\1_Skyrim_JP_EveryFont_0805.ttf
$ uv run optimizer --action remove_empty_glyphs -i .\assets\fonts\skyrim\22_Skyrim_JP_BookFont_0805.ttf -o .\build\22_Skyrim_JP_BookFont_0805.ttf
$ uv run optimizer --action remove_empty_glyphs -i .\assets\fonts\skyrim\5_Skyrim_JP_HandWriteFont_0805.ttf -o .\build\5_Skyrim_JP_HandWriteFont_0805.ttf
```

3. 空白グリフ削除処理を実施したフォントから中に含まれている文字を取り出す。

```cmd:
$ uv run inspector --action get_glyphs -i .\build\1_Skyrim_JP_EveryFont_0805.ttf -o .\build\1_Skyrim_JP_EveryFont_0805_glyphs.txt 
$ uv run inspector --action get_glyphs -i .\build\22_Skyrim_JP_BookFont_0805.ttf -o .\build\22_Skyrim_JP_BookFont_0805_glyphs.txt 
$ uv run inspector --action get_glyphs -i .\build\5_Skyrim_JP_HandWriteFont_0805.ttf -o .\build\5_Skyrim_JP_HandWriteFont_0805_glyphs.txt 
```

> [!NOTE]
> 最新のバニラフォントはなぜか全角英数記号が欠落しています。
> 補間するための全角英数記号ファイルを `data\skyrim\essential_glyphs_zenkaku.txt` を補間用として `build\essential_glyphs_zenkaku.txt` にコピーしてから次に進みます。


4. 3種のフォントから取り出した文字列一覧を結合し、スカイリム用最小サブセットとする。

```cmd:
$ uv run common --action merge_text --input_text_dir .\build\ -o .\data\subsets\subset_jp_skyrim_new.txt
[DEBUG]: 読み込み中... 1_Skyrim_JP_EveryFont_0805_glyphs.txt
[DEBUG]: 読み込み中... 22_Skyrim_JP_BookFont_0805_glyphs.txt
[DEBUG]: 読み込み中... 5_Skyrim_JP_HandWriteFont_0805_glyphs.txt
[DEBUG]: 読み込み中... essential_glyphs_zenkaku.txt
マージ済みテキストを出力しました。data\subsets\subset_jp_skyrim_new.txt
```

5. サブセットを検証する。

源ノ明朝(Source-Han-Serif)などの巨大なフォントを用意し、それに対してサブセットテキストの比較検証を実施します。

```cmd:
$ uv run inspector --action validate_subset --input_font_file .\assets\fonts\source-han-serif\SourceHanSerifJP-Medium.ttf --subset_text_file .\data\subsets\subset_jp_skyrim_new.txt
[SUCCESS]: おめでとうございます！すべての文字がフォントに含まれています。
サブセットにあってフォントに無い文字列を出力しました: build\SourceHanSerifJP-Medium_missing_glyphs.txt
```

> [!NOTE]
> このサブセットは3種類のフォントの文字が含まれています。3種類のフォントはそれぞれそこそこの差分があるため、このサブセットをバニラフォントで検証すると200文字程度の欠落が表示されます。これは正しい挙動です。