# コントリビューションガイド
開発するに当たっての留意事項、ナレッジなど。

## Git開発フロー
GitLab-Flowを採用

## フォント開発時に使用するツール
### BSA Browser
ベセスダアーカイブ(.bsa)を展開するツール。バニラのフォントや設定ファイルを取り出すために使う。
https://www.nexusmods.com/skyrimspecialedition/mods/1756

### xTranslator
プラグインやスクリプトを翻訳するツール。
https://www.nexusmods.com/starfield/mods/313

### JPEXS Free Flash Decompiler - FFDec
SWFを作成加工するために使用。
https://github.com/jindrapetrik/jpexs-decompiler

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

## テスト

