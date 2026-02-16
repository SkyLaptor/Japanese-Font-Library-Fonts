# 各種データの作り方
万が一紛失した時用の備忘録

TODO: 後で手順を検証すること。

## ベースフォントの作成
任意のフォントをゲーム内フォントに合わせるための基準となるフォントです。  
パス直指定で各スクリプトから使用されているため迂闊に名前を変更したりしないように注意して下さい。

1. 日本語版スカイリムをインストールします。

2. インストール後、(BSABrowser](https://www.nexusmods.com/skyrimspecialedition/mods/1756)を使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

3. `fonts_ja.swf`（または `fonts_jp.swf`）を任意の場所にエクスポートします。

4. エクスポートした `.swf` を[FFDec](https://github.com/jindrapetrik/jpexs-decompiler)で開き、**[フォント]** セクションから以下の3種類のフォントを取り出します。

   * **Everywhere** : `1_Skyrim_JP_EveryFont_0805`
   * **Book** : `22_Skyrim_JP_BookFont_0805`
   * **Handwrite** : `5_Skyrim_JP_HandWriteFont_0805`

> [!NOTE]
> ゲームバージョンにより若干フォント名前が異なります。

5. 取り出したフォントに対し空白除去処理を行います。
以下のコマンドで空白が除去されます。
`$ uv run optimizer --action remove_empty_glyphs -i 取り出したフォント.ttf -o build\フォント名(everywhere.ttfなど)`

6. 空白除去処理を行ったフォントを以下のパスに配置します。

   * **Everywhere** : `data\basefonts\everywhere.ttf`
   * **Book** : `data\basefonts\book.ttf`
   * **Handwrite** : `data\basefonts\handwrite.ttf`

以上でベースフォントの作成が完了となります。このフォントはサイズ変更処理などで基準となるので、空白グリフクリーンアップ以外の変更は行ってはなりません。

## サブセットテキスト作成(スカイリム準拠)
ゲームデフォルトのフォントで使用可能な文字列のみのサブセットテキストを作成します。  
事前に[ベースフォント](#ベースフォントの作成)を作成しておく必要があります。

1. 各フォントに含まれている文字を取り出します。
以下のコマンドを実行します。

```powershell:
$ uv run inspector --action get_glyphs -i data\basefonts\everywhere.ttf -o build\everywhere_glyphs.txt
$ uv run inspector --action get_glyphs -i data\basefonts\book.ttf -o build\book_glyphs.txt
$ uv run inspector --action get_glyphs -i data\basefonts\handwrite.ttf -o build\handwrite_glyphs.txt
```

> [!NOTE]
> 困ったことにバニラのゲームフォントには意図しない空白が多数存在します。それをクリーニングしていない状態で含まれている文字を検索してしまうと正しい結果を得られません。
> なお、各フォントに含まれる文字には若干の差があります。

2. 全角英数記号ファイルを準備します。
以下の文字列を記載したファイルを **UTF-8(BOMなし)** で `build\essential_glyphs_zenkaku.txt` に保存します。

```text:
！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～｟｠｡｢｣､
```

> [!NOTE]
> 最新スカイリム(v1.6.1170)の日本語フォントはなぜか全角英数字が空白グリフで登録されているというとんでもないバグがあります。さすがにこれは看過できないため、補間用として準備します。

3. 文字列を結合します。
以下のコマンドを実行します。

```powershell:
$ uv run common --action merge_text --input_text_dir build -o data\subsets\subset_jp_skyrim.txt
```

> [!NOTE]
> buildディレクトリには**フォントから抽出した文字列ファイル**と**全角英数補間ファイル**以外のテキストファイルは置かないで下さい。それらも結合されてしまいます。


## サブセットテキスト作成(日本語フル)
JIS第四水準＋いくつかの最新文字を加えた、おおよそ日本で使用しうる文字を網羅したサブセットテキストを作成します。

1. 以下のコマンドを実行します。

```powershell:
$ uv run common --action generate_subset_jp_full --input_text_dir build -o data\subsets\subset_jp_full.txt
```

> [!NOTE]
> `common.generate_subset_jp_full()` では可能な限り日本語圏で表示しうる文字列を生成していますが、> もし不足が出た場合にはソースの `extra_unicodes` にUnicode指定で追加することを検討します。


## コアフォントSWFの作成
どの言語であろうが使用する特殊なフォントのみを格納したフォントSWFを作成します。こうすることで、無駄なフォント容量を削減できます。

1. 日本語版スカイリムをインストールします。

2. インストール後、(BSABrowser](https://www.nexusmods.com/skyrimspecialedition/mods/1756)を使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

3. `fonts_ja.swf`（または `fonts_jp.swf`）を任意の場所にエクスポートします。

4. エクスポートした `.swf` を[FFDec](https://github.com/jindrapetrik/jpexs-decompiler)で開き、**[フォント]** セクションから以下の3種類以外のフォントをエクスポートします。

   * **Everywhere** : `1_Skyrim_JP_EveryFont_0805`
   * **Book** : `22_Skyrim_JP_BookFont_0805`
   * **Handwrite** : `5_Skyrim_JP_HandWriteFont_0805`

5. [FFDec](https://github.com/jindrapetrik/jpexs-decompiler)を起動し、**[New empty]** から以下のパラメーター通りに新しいSWFを作成します。

TODO: これで作ったやつ試験する。これで問題なければ、気持ちよいが

* ヘッダー
  * 圧縮: 無圧縮
  * SWFのバージョン: 10
  * Harman encrypted: □
  * GFX: □
  * フレームレート: 24.0
  * フレーム数: 1
  * ディスプレイの大きさ: 全て0
* フォント
  * DefineFont3 ※4でエクスポートしたフォント全て
* フレーム
  * frame 1
* その他
  * FileAttributes
    * 全項目: □




## フォントテンプレートSWFの作成
フォントを格納するためのガワのみのフォントSWFを作成します。

TODO: これで作ったやつ試験する。これで問題なければ今のテンプレよりさらに小さくできるが、、

1. [FFDec](https://github.com/jindrapetrik/jpexs-decompiler)を起動し、**[New empty]** から以下のパラメーター通りに新しいSWFを作成します。

* ヘッダー
  * 圧縮: 無圧縮
  * SWFのバージョン: 10
  * Harman encrypted: □
  * GFX: □
  * フレームレート: 24.0
  * フレーム数: 1
  * ディスプレイの大きさ: 全て0
* フォント
  * DefineFont3 chid:1 フォント名: `REPLACE_ME_FONT_NAME_LENGTH_MAX_XXXXXXXXXXXXXXX` ※
* フレーム
  * frame 1
* その他
  * FileAttributes
    * 全項目: □

※フォント名は必ず `src\build_skyrim_fonts.py` 内の `DUMMY_NAME` 定数と同じにすること。



## テンプレートフォントコンフィグの作り方
マスターコンフィグを作るため、各ゲームの英語版、日本語版フォントコンフィグを比較し、全てのマップを網羅する。

1. 各バージョンの英語版、日本語版スカイリムをインストールします。

2. インストール後、(BSABrowser](https://www.nexusmods.com/skyrimspecialedition/mods/1756)を使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

3. フォント設定ファイル( `fontconfig.txt` または `fontconfig_ja.txt`) を任意の場所にエクスポートします。

4. 各バージョンのフォント設定ファイルを比較し、`map "キー名"`を重複なしで結合していきます。マップされるフォント名は、以下を除いて全て `template` などにしておきます。

`$DragonFont, $FalmerFont, $DwemerFont, $DaedricFont, $MageScriptFont, $SkyrimSymbolsFont, $SkyrimBooks_UnreadableFont, ControllerButtons, ControllerButtonsInverted`

5. 以下のマップを書き足します。

`$MCMFont, $MCMMediumFont, $MCMBoldFont`

6. フォント設定ファイルの先頭にある `fontlib ～` は `fontlib "Interface\fonts_core.swf"` のみにします。

7. フォント設定ファイルの末尾にある `validNameChars ～` は `data\fontconfigs\validNameChars.txt` に中身を書き換えます。`validNameChars` は [生成手順](#validnamecharsの生成) を参照してください。


## validNameCharsの生成

1. 以下のコマンドを実行します。

```
$ uv run common --action generate_subset_jp_jisx0208 --output_text_file data\fontconfigs\validNameChars.txt
```


> [!NOTE]
> validNameCharsはRaceMenuでキャラ名に使用できる名前の文字の一覧です。フォントとは直接の関係はありません。
> validNameCharsにダブルクォーテーションを入れる場合は、`\`でエスケープする必要があります。なお、この手順では自動でエスケープされています。
