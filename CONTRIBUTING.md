# 開発ガイドライン
## はじめに（必ずお読みください）
本プロジェクトへの貢献を検討いただきありがとうございます。 メンテナーの負担軽減とプロジェクトの品質維持のため、以下のルールを遵守してください。これらが守られていないプルリクエストは、内容を確認せずにクローズする場合があります。

* Issue優先: 大きな変更や機能追加を行う前に、必ずIssueで提案し合意を得てください。
* 最小PRs: 変更は可能な限り最小単位に分割してください。巨大な変更はレビュー対象外となります。
* 品質管理: ローカルでのビルドおよびテスト通過は必須条件です。

## 開発フロー
本リポジトリでは GitLab-Flow を採用しています。

1. mainブランチ: 全ての開発のベースです。
2. 作業ブランチ: `main` から作業用のブランチ(`feature/issue-番号`等)を切って作業してください。
3. マージ: `main` へのマージは、レビュー承認およびCI通過後に行われます。
4. プレリリース: 仮公開は、`main` から `pre-production` ブランチへのマージによって実行されます。
5. リリース: 公開は、`pre-production` から `production` ブランチへのマージによって実行されます。

## フォルダ構成

* assets: 生のフォントTTFやSWFといった開発に必要なリソース類を配置します。
* build: 一時ビルド時などに使用します。コミット対象外。
* data: サブセットデータなどを配置します。
* dist: 最終的な配布物を保管します。コミット対象外。
* docs: ドキュメント類を配置します。
* src: プログラムソースコードを配置します。
* tests: pytestなどのテスト用コードを配置します。

## 適用対象
* 対象ゲーム: Skyrim, SkyrimSE(SkyrimAE), SkyrimVR の英語版/日本語版 全てのバージョン。
* 対象Modマネージャー: [Vortex](https://www.nexusmods.com/about/vortex), [ModOrganizer2](https://www.nexusmods.com/about/vortex) ※公式そのままの状態でカスタムを加えていないものであること。
* Mod: [SKSE](https://skse.silverlock.org/), [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) ※フォント周りに影響を及ぼす場合はIssueで提案すること。

## 大まかな開発手順
1. リポジトリから `main` ブランチをクローン/チェックアウトします。
2. 開発ツール類、テスト環境をセットアップします。
3. コンテンツを修正し、テストを実行します。`$ uv run -m pytest`
4. `main` ブランチに対してプルリクエストを作成します。

## 開発及びテスト時に使用するツール
### Visual Studio Code (VSCode)
軽量、強力なIDEです。  
https://code.visualstudio.com/

### UV
OSを汚さずにPython実行環境を準備するために使用します。  
https://docs.astral.sh/uv/getting-started/installation/

### FontForge
作成したフォントの確認やマージにて使用します。パスを `fontforge.exe` に通してください。  
https://fontforge.org/en-US/

### JPEXS Free Flash Decompiler - FFDec
SWFを作成加工するために使用します。パスを `ffdec-cli.exe` に通してください。  
https://github.com/jindrapetrik/jpexs-decompiler

### BSA Browser
ベセスダアーカイブ(.bsa)を展開するツール。バニラのフォントや設定ファイルを取り出すために使います。  
https://www.nexusmods.com/skyrimspecialedition/mods/1756


## ゲームデフォルトの日本語フォントの取り出し方
1. 最新版のSkyrimSE 英語版をインストールします。※最新SkyrimSE英語版v1.6.1170には日本語フォントが含まれています。
2. `ゲームインストールディレクトリ\Data\Skyrim - Interface.bsa` をBSA Browserで開きます。
3. `interface\fonts_ja.swf` を取り出し、FFDecで開きます。
4. 左ツリーから`フォント`を選び、任意のフォントを右クリックし'選択中のものをエクスポート'から任意の場所にエクスポートする。


## ベースフォントの作成
任意のフォントをゲーム内フォントに合わせるための基準となるフォントです。  
パス直指定で各スクリプトから使用されているため迂闊に名前を変更したりしないように注意して下さい。

1. 日本語版スカイリムをインストールします。

2. インストール後、BSABrowserを使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

3. `fonts_ja.swf`（または `fonts_jp.swf`）を任意の場所にエクスポートします。

4. エクスポートした `.swf` を[FFDec](https://github.com/jindrapetrik/jpexs-decompiler)で開き、**[フォント]** セクションから以下の3種類のフォントを取り出します。

   * **Every** : `1_Skyrim_JP_EveryFont_0805`
   * **Book** : `22_Skyrim_JP_BookFont_0805`
   * **Handwrite** : `5_Skyrim_JP_HandWriteFont_0805`

> [!NOTE]
> ゲームバージョンにより若干フォント名前が異なります。

5. 取り出したフォントに対し空白除去処理を行います。
以下のコマンドで空白が除去されます。

```powershell:
$ uv run remove_empty_glyphs build\1_Skyrim_JP_EveryFont_0805.ttf -o data\base_fonts\skyrim\every.ttf
$ uv run remove_empty_glyphs build\22_Skyrim_JP_BookFont_0805.ttf -o data\base_fonts\skyrim\book.ttf
$ uv run remove_empty_glyphs build\5_Skyrim_JP_HandWriteFont_0805.ttf -o data\base_fonts\skyrim\handwrite.ttf
```

以上でベースフォントの作成が完了となります。このフォントはサイズ変更処理などで基準となるので、空白グリフクリーンアップ以外の変更は行ってはなりません。


## コアフォントSWFの作成
どの言語であろうともゲーム内で使用する特殊なフォントのみを格納したフォントSWFを作成します。これにより無駄なフォント容量を削減できます。

1. 日本語版スカイリムをインストールします。

2. インストール後、BSABrowserを使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

3. `fonts_ja.swf`（または `fonts_jp.swf`）を任意の場所にエクスポートします。

4. エクスポートしたSWFファイルを[FFDec](https://github.com/jindrapetrik/jpexs-decompiler)で開き、**[フォント]** セクションから以下のフォントをエクスポートします。

   * **コントローラーボタン** : `Controller  Buttons`
   * **コントローラーボタン(反転)** : `Controller  Buttons inverted`
   * **ドラゴン文字** : `Dragon_script`
   * **デイドラ文字** : `Daedric`
   * **ドゥーマー文字** : `Dwemer`
   * **ファルマー文字** : `Falmer`
   * **ゲーム内シンボルマーク** : `SkyrimSymbols`
   * **魔術文字** : `Mage Script`
   * **読めない本の文字** : `SkyrimBooks_Unreadable`

5. [FFDec](https://github.com/jindrapetrik/jpexs-decompiler)を起動し、**[New empty]** から以下のパラメーター通りに新しいSWFを作成します。

* ヘッダー
  * 圧縮: 無圧縮
  * SWFのバージョン: 10
  * Harman encrypted: □
  * GFX: □
  * フレームレート: 24.0
  * フレーム数: 1
  * ディスプレイの大きさ: 全て0
* フォント
  * DefineFont3: `Controller  Buttons` Ascent: 17160, Descent: 4180, Leading: 860 ※メトリクス値は元のデータを参照すること。
  * DefineFont3: `Controller  Buttons inverted` Ascent: 17160, Descent: 4180, Leading: 860
  * DefineFont3: `Dragon_script` Ascent: 19900, Descent: 3900, Leading: 3320
  * DefineFont3: `Daedric` Ascent: 17160, Descent: 4180, Leading: 860
  * DefineFont3: `Dwemer` Ascent: 17160, Descent: 4180, Leading: 860
  * DefineFont3: `Falmer` Ascent: 17160, Descent: 4180, Leading: 860
  * DefineFont3: `SkyrimSymbols` Ascent: 15800, Descent: 4180, Leading: -500
  * DefineFont3: `Mage Script` Ascent: 17160, Descent: 4180, Leading: 860
  * DefineFont3: `SkyrimBooks_Unreadable` Ascent: 20460, Descent: 12600, Leading: 12580
* フレーム
  * frame 1
* その他
  * FileAttributes
    * 全項目: □ または 0


## フォントテンプレートSWFの作成
フォントを格納するための中身が空のフォントSWFを作成します。

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
  * DefineFont3 chid:1 フォント名: `REPLACE_ME_FONT_NAME_LENGTH_MAX_XXXXXXXXXXXXXXX`
* フレーム
  * frame 1
* その他
  * FileAttributes
    * 全項目: □

> [!IMPORTANT]
> フォント名は必ず `src/const.py` 内の `DUMMY_FONT_NAME_IN_SWF` 定数と同じにして下さい。SWF変換の際にフォント名が書き換わらなくなります。

## テンプレートフォントコンフィグの作り方
マスターコンフィグを作るため、各ゲームの英語版、日本語版フォントコンフィグを比較し、全てのマップを網羅します。

1. 各バージョンの英語版、日本語版スカイリムをインストールします。

2. インストール後、BSABrowserを使って `Skyrim\Data\Skyrim - Interface.bsa`を開きます。

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
$ uv run generate_subset_jp_jisx0208 data\fontconfigs\skyrim\validNameChars.txt --validnamechars_escape
```

> [!NOTE]
> validNameCharsはRaceMenuでキャラ名に使用できる名前の文字の一覧です。フォントとは直接の関係はありません。
> validNameCharsにダブルクォーテーションを入れる場合は、`\`でエスケープする必要があります。なお、この手順では自動でエスケープされています。


## サブセットテキスト作成(軽量版)
ゲームデフォルトのフォントで使用可能な文字列のみの軽量なサブセットテキストを作成します。  
事前に[ベースフォント](#ベースフォントの作成)を作成しておく必要があります。

1. 各フォントに含まれている文字を取り出します。
以下のコマンドを実行します。

```powershell:
$ uv run get_glyphs data\base_fonts\skyrim\every.ttf -o build\every_glyphs.txt
$ uv run get_glyphs data\base_fonts\skyrim\book.ttf -o build\book_glyphs.txt
$ uv run get_glyphs data\base_fonts\skyrim\handwrite.ttf -o build\handwrite_glyphs.txt
```

> [!NOTE]
> 困ったことにバニラのゲームフォントには意図しない空白が多数存在します。それをクリーニングしていない状態で含まれている文字を検索してしまうと正しい結果を得られません。なお、各フォントに含まれる文字には若干の差があります。

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
$ uv run merge_text build -o data\subsets\skyrim\subset_jp_lightweight.txt
```

> [!NOTE]
> 結合を実行する際、`build` ディレクトリには**フォントから抽出した文字列ファイル**と**全角英数補間ファイル**以外のテキストファイルは置かないで下さい。それらも結合されてしまいます。


## サブセットテキスト作成(日本語フル)
JIS第四水準＋いくつかの最新文字を加えた、おおよそ日本で使用しうる文字を網羅したサブセットテキストを作成します。

1. 以下のコマンドを実行します。

```powershell:
$ uv run generate_subset_jp_full data\subsets\skyrim\subset_jp_full.txt
```

> [!NOTE]
> 可能な限り日本語圏で表示しうる文字列を生成していますが、もし不足が出た場合には `src\const.py` の `EXTRA_UNICODES` にUnicode指定で追加することを検討して下さい。


 ## バニラバグフィックスパッチの作り方
### 本UIの内蔵フォントバグ除去
Skyrim時代から存在するバグです。
SE版はv1.6.629(AEアップデート)以降解消していますが、下位バージョン(特に1.5.97.0)を使用している場合はパッチする必要があります。
英語版の本UI`interface/book.swf`にはなぜかフォントファイルそのものが格納されていて、それが優先して使用されてしまうことにより発生します。FFDecを使用して余分なフォントを除去して下さい。
動作確認を行う場合は、「エリトリスのノート」や「アーヴェルの日記」を開いてみると良でしょう。
参考情報: https://obachanskyrim.blogspot.com/2012/07/bookswf.html

### レベルアップメニューUI
Skyrim時代から存在するバグです。
SE版はv1.6.629(AEアップデート)以降解消していますが、下位バージョン(特に1.5.97.0)を使用している場合向けはパッチする必要があります。  
日本語版のレベルアップメニューUI`interface/levelupmenu.swf`のフォントマップが正しく指定されておらず、きちんと表示されません。英語版ではバグがないため、英語版の`interface/levelupmenu.swf`を取り出して使用することで解消します。  
ただし、デフォルトUIはバグは解消されていても表示が非常に大きく見切れていますので、そこも修正する必要があります。
FFdecを使用して、該当部品のyminを増やして文字の位置を変えた上で、HTMLレンダリングに変えてフォントサイズを指定することでサイズが変わります。

## SkyUI向けMCM専用フォントマップ適用パッチの作り方
コンフィグメニュー(MCM)はデフォルトで`$EverywhereFont`系の汎用フォントを使用しますが、日本語のような全角フォントだと文字が多すぎてUIからはみ出てしまいます。かと言って`$EverywhereFont`系に長体(Condensed/Skinny)フォントを指定すると他のUIが見づらくなります。そこで、MCMには専用のフォントマップを使用するパッチを用意することで対応します。  
MCMを実現しているUIは SkyUI LE/SE共に`Interface/skyui/configpanel.swf`です。FFDecを使用してフォントマップを指定している箇所を検索して書き換えます。


## 開発の参考に
* fontTools Documentation: https://fonttools.readthedocs.io/en/latest/
* FontForge Scripting: https://fontforge.org/docs/scripting/scripting.html
