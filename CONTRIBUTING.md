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

## 大まかな開発手順

1. リポジトリから `main` ブランチをクローン/チェックアウトする。
2. 開発ツール類、テスト環境をセットアップする。
3. コンテンツを修正し、テストを実行する。
4. `main` ブランチに対してプルリクエストを作成する。

## テスト環境
* 対象のゲーム: Skyrim, SkyrimSE(SkyrimAE), SkyrimVR
* 対象のModマネージャー: [Vortex](https://www.nexusmods.com/about/vortex), [ModOrganizer2](https://www.nexusmods.com/about/vortex) ※公式そのままの状態でカスタムを加えていないものであること。
* Mod: [SKSE](https://skse.silverlock.org/), [SkyUI](https://www.nexusmods.com/skyrimspecialedition/mods/12604) ※フォント周りに影響を及ぼす場合はIssueで提案すること。


## 開発及びテスト時に使用するツール
### Visual Studio Code (VSCode)
軽量、強力なIDEです。
https://code.visualstudio.com/

### BSA Browser
ベセスダアーカイブ(.bsa)を展開するツール。バニラのフォントや設定ファイルを取り出すために使います。
https://www.nexusmods.com/skyrimspecialedition/mods/1756

### xTranslator
プラグインやスクリプトを翻訳します。
https://www.nexusmods.com/starfield/mods/313

### UV
OSを汚さずにPython実行環境を準備するために使用します。
https://docs.astral.sh/uv/getting-started/installation/

初回や更新があった場合は以下のコマンドを実行して下さい。
```
$ uv sync
```

### FontForge
作成したフォントを確認するとき等に使用します。
https://fontforge.org/en-US/

### JPEXS Free Flash Decompiler - FFDec
SWFを作成加工するために使用します。`ffdec-cli.exe` にパスを通してください。
https://github.com/jindrapetrik/jpexs-decompiler


## 開発手順
### 新規フォントの場合
1. 非商用にて無償利用可能なフォントを入手する。その場合は入手元、使用許諾情報も併せて取得すること。

2. フォントにてサブセット検証を行う。

```
$ cd scripts
$ fontforge --quiet --script ./check_fontcoverage.py -t <TTF> -s < subset_jp_full.txt | subset_jp_skyrim.txt >
```

スカイリムサブセット(`subset_jp_skyrim.txt`)による検証にて、不足グリフがあった場合は原則的にプルリクエストは却下となります。似たフォントで補間するものとしてください。

3. サブセット検証が完了したフォントに対し、スカイリム専用変換を行う。

```
$ cd scripts
$ fontforge --quiet --script ./convert_for_skyrim.py -i <TTF> -s <subset> -m <ui_mode> -w <width_mode>
```

4. テンプレートSWFにフォントを埋め込む。

```
$ cd scripts
$ ffdec-cli -replace fonts_template.swf <SWF> 1 <TTF>
```

5. フォントを埋め込んだSWFをFFDecで開き、フォント名、ExportAssetsを次のルールに従って書き換える。

```
フォントファイル名:
fonts_<フォントファミリー>[太さ: _light | _bold]<UIタイプ: _every | _book | _handwrite>[長形: _condensed | _skinny][サブセット: _lightweight].swf

フォント名:
<フォント名>[太さ: _light | _bold]<UIタイプ: _every | _book | _handwrite>[長形: _condensed | _skinny][サブセット: _lightweight]
```

7. テスト用のfontconfig.txtを用いて、ゲーム内にて表示を確認する。




## テスト項目

* [ ] pytestを通過するか。`$ uv run -m pytest`
* [ ] サブセット検証にてスカイリムサブセットをパスしていること。
* [ ] ゲーム起動直後にCTDが起きないこと。
* [ ] メインメニューで豆腐化が起きないこと。




## バニラの日本語フォントの取り出し方
対象バージョン: SkyrimSE 英語版 v1.6.1170

1. 最新版のSkyrimSE 英語版をインストールする。※最新SkyrimSE英語版v1.6.1170には日本語フォントが含まれている。
2. `ゲームインストールディレクトリ\Data\Skyrim - Interface.bsa` を [BSA Browser](https://www.nexusmods.com/skyrimspecialedition/mods/1756) で開く。
3. `interface\fonts_ja.swf` を取り出し、[JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) で開く。
4. 左ツリーから`フォント`を選び、任意のフォントを右クリックし'選択中のものをエクスポート'から任意の場所にエクスポートする。


## コアフォントSWFの作り方
対象バージョン: SkyrimSE 英語版 v1.6.1170
スカイリムのフォントにはコントローラーボタンやドラゴン文字などの言語を問わないシンボル系のフォントが含まれている。
バージョン（特にCreationClub実装あたり）により追加されていったものはあるが、基本的にスカイリムでもスカイリムSEでも同じものが使用されているが、ファイル名がゲームバージョンによりまちまちである。
つまり、最新の英語版スカイリムから取り出し、余計なフォントを削除して軽量化したfonts_core.swfとかにし、fontconfig.txtでインポートすればコアフォントとして利用可能となる。

1. 最新版のSkyrimSE 英語版をインストールする。
2. `ゲームインストールディレクトリ\Data\Skyrim - Interface.bsa` を [BSA Browser](https://www.nexusmods.com/skyrimspecialedition/mods/1756) で開く。
3. `interface\fonts_en.swf`を`fonts_core.swf`として取り出す。
4. `fonts_core.swf`を [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) で開く。
5. 左ツリーから`テキスト`を選び、全て消す。
6. 左ツリーから`フォント`を選び、フォント名が以下のもの**以外**のフォントを削除する。※バージョンが上がった際は差異を確認すること。多分これから増えることはないと思われるが。
    * `Controller  Buttons`
    * `Controller  Buttons inverted`
    * `Dragon_script`
    * `Daedric`
    * `Dwemer`
    * `Falmer`
    * `SkyrimSymbols`
    * `Mage Script`
    * `SkyrimBooks_Unreadable`
7. 各フォントの配下にある`DefineFontAlignZones`と`DefineFontName`を開き、それぞれの`forceWriteAsLong`を`false`にする。
7. 動作高速化のため残ったフォントにExportAssetsを付ける。
    1. 左ツリーから`その他`→`Add tag inside`→`ExportAssets`→各フォント`DefineFontName`の直下に差し込む。
    2. 差し込んだExportAssetsの編集にて、assetsを右クリック`先頭にassetを挿入します`でassetを追加する。
    3. 追加したassetのU16を、フォントのChildIDにし、Stringを**フォント名**と同じにする。
    4. 全フォントに同様の操作を行う。
8. 左ツリーから`ヘッダー`を選択し、編集から以下のように設定する。
    * 圧縮: ZLIB
    * SWFのバージョン: 10
    * Harman encrypted: False
    * GFX: False
    * フレームレート: 24
    * ディスプレイの大きさ: 0,0～0,0
9. 左ツリーから`その他`を選択し、`FileAttributes`を以下のように設定する。
    * reservedA: false
    * useDirectBlit: false
    * useGPU: false
    * hasMetadata: false
    * actionScript3: false
    * useNetwork: false
    * noCrossDomainCache: false
    * swfRelativeUrls: false
    * reservedB: 0
    * forceWriteAsLong: false
8. 左ツリーから`その他`を選択し、`Metadata`と`SetBackgroundColor`を削除する。
9. 保存して完了。


## 比較対象バニラフォントの作り方
1. FFDecを使い、最新Skyrimの日本語フォント(interface\fonts_jp.swf)からTTFで日本語フォントを抜く。以下のような名前が付いている
   * Everywhere_JP
   * Book_JP
   * JP_Handwritten

2. 取り出したフォントに対し、以下の処理を掛ける
   1. 空白グリフ消去 `$ uv run font_tools --action remove_empty_glyphs 対象のフォント`
   2. 空白グリフを消去したフォントから文字列を抜き出してサブセットテキスト作成。`$ uv run font_tools --action get_glyphs 対象のフォント（空白除去済）`
   3. 空白グリフを消去したフォントをメトリクス調整 `$ uv run font_tools --action set_metrics 対象のフォント（空白除去済） --ascent 880 --descent -144`

## フォントテンプレートSWFの作り方
対象バージョン: SkyrimSE 英語版 v1.6.1170

1. [コアフォント](##コアフォントSWFの作り方)を`fonts_template.swf`としてコピーする。
3. `fonts_template.swf` を [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) で開く。
5. 左ツリーから`フォント`を選び、フォントIDが1以外を全て削除する。
8. 左ツリーから`その他`を選択し、フォントIDが1以外の`ExportAssets`を削除する。
9. 保存して完了。

メモ バニラ日本語SWFのメトリクス値:
* メトリクス ※twips単位(1px=20twips) EM換算にすると880,144なので、フォント側メトリクスをそれに合わせておけばいいはず。
    * Everywere/Book/Handwrite:
        * Ascent: 17600
        * Descent: 2880
        * Leadline: 0


## ゲーム日本語化方法
MODの互換性を考慮し、英語版を日本語化するという方式を採用する。Steam版のみ。

## 不要なデータの掃除
Skyrimをプレイするとあちこちにファイルが出来上がる。完全リセットする場合は以下を消去、必要に応じてバックアップすること。

* ロードオーダーなど
    * `C:\Users\{USERNAME}\Appdata\Local\Skyrim`
    * `C:\Users\{USERNAME}\Appdata\Local\Skyrim Special Edition`
* ゲーム設定、セーブデータ、SKSEログ類
    * `C:\Users\{USERNAME}\Documents\My Games\Skyrim`
    * `C:\Users\{USERNAME}\Documents\My Games\Skyrim Special Edition`
* WryeBash Modディレクトリ ※WryeBashを使用していた場合
    * `{SteamLibrary}\steamapps\common\Skyrim Mods`
    * `{SteamLibrary}\steamapps\common\Skyrim Special Edition Mods`
* Vortexディレクトリ ※Vortexを使用していた場合
    * `C:\Users\{USERNAME}\Appdata\Roaming\Vortex` もしくは自身で設定したパス
* ModOrganizer2ディレクトリ ※ModOrganizerを使用していた場合
    * `C:\Modding\MO2` もしくは自身で設定したパス

## SkyrimSE v1.6.629～v1.6.1170(現在)
v1.6.629以降、SkyrimSE無料AEアップデートということで構造がSkyrimAEとほぼ同等となった？模様。
英語版と日本語版の差がほぼ無くなり、英語版ファイル群に対し日本語版音声ファイルが追加され、Skyrim.iniが日本語版用にチューニングされただけとなった。

```:差分
Skyrim.ini(SSEゲームディレクトリ\Skyrim_Default.ini)の差分
●言語設定
sLanguage=ENGLISH
↓
sLanguage=JAPANESE

●フォント設定
※追加
[Fonts]
sFontConfigFile=Interface\FontConfig_ja.txt

●音声ファイル読込
sResourceArchiveList2=Skyrim - Voices_en0.bsa, 省略
↓
sResourceArchiveList2=Skyrim - Voices_ja0.bsa, 省略
```

まずは普通に英語版SkyrimSEをインストールし、`SkyrimSELauncher.exe`を起動してそのまま終了する。
これにより、ロードオーダー情報及びゲーム設定ファイルがユーザープロファイルの各所に生成される。

[BSA Browser](https://www.nexusmods.com/skyrimspecialedition/mods/1756)を使用して以下のファイルを開き、対象の日本語StringsとTranslateをエクスポートする。`japanese`で検索すると良い。

* _ResourcePack.bsa
* ccBGSSSE001-Fish.bsa
* ccBGSSSE025-AdvDSGS.bsa
* ccBGSSSE037-Curios.bsa
* ccQDRSSE001-SurvivalMode.bsa
* Skyrim - Interface.bsa


**英語音声のままでよければ、この作業はスキップしてOK**
日本語音声データをダウンロードする。
Webブラウザを開き、`steam://open/console`と入力するとSteamコンソールが開くので、以下のコマンドを入力する。
`download_depot 489830 544861 3494476046078906882`
ダウンロードが完了したら、`C:\Program Files (x86)\Steam\steamapps\content\app_489830\depot_544861\Data`を開き、`skyrim - voices_ja0.bsa`をゲームディレクトリの`Data`直下にコピーする。

ゲーム設定ファイル(`C:\Users\{USERNAME}\Documents\My Games\Skyrim Special Edition\Skyrim.ini`)を開き、以下を編集する。

```
編集
sResourceArchiveList2=Skyrim - Voices_en0.bsa, 省略
↓
sResourceArchiveList2=Skyrim - Voices_ja0.bsa, 省略
```


 ## バニラバグフィックスパッチの作り方
### 本UIの内蔵フォントバグ除去
Skyrim時代から存在するバグ。
SE版はv1.6.629以降解消しているが、下位バージョン(特に1.5.97.0)を使用している場合向けにパッチする必要あり。
英語版の最新の本UI`interface/book.swf`にはなぜかフォントファイルそのものが格納されており、そちらが使用されてしまうことにより発生する。FFDecを使用して余分なフォントを除去する。
動作確認としては、「エリトリスのノート」や「アーヴェルの日記」を開いてみると良い。
参考情報: https://obachanskyrim.blogspot.com/2012/07/bookswf.html

### レベルアップメニューUI
Skyrim時代から存在するバグ。
SE版はv1.6.629以降解消しているが、下位バージョンを使用している場合向けにパッチする必要あり。  
日本語版のレベルアップメニューUI`interface/levelupmenu.swf`のフォントマップが正しく指定されておらず、きちんと表示されない。英語版ではバグがないため、英語版の`interface/levelupmenu.swf`を取り出して使用する。  
ただ、デフォルトUIはバグは解消されていても表示が非常に大きく見切れているため、そこも修正する。yminを増やして文字の位置を変えた上で、HTMLレンダリングに変えてフォントサイズを指定する。


## SkyUI向けMCM専用フォントマップ適用パッチの作り方
コンフィグメニュー(MCM)はデフォルトで`$EverywhereFont`系の汎用フォントを使用するが、日本語のような全角フォントだと文字が多すぎてUIをぶち抜いてしまう。かと言って`$EverywhereFont`系に長形フォントを指定すると他のUIが見づらくなる。その解決策として、MCMには専用のフォントマップを使用するパッチを用意する。
MCMを実現しているUIは LE/SE共に`Interface/skyui/configpanel.swf` 。FFDecを使用してフォントマップを指定している箇所を検索して書き換える。





## 参考
FontForge Scripting: https://fontforge.org/docs/scripting/scripting.html

