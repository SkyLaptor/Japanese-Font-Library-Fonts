# コントリビューションガイド
開発するに当たっての留意事項、ナレッジなど。

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
* メトリクス ※twips単位(1px=20twips) EM換算にすると880,114なのでそのフォントを入れてフォントEMを反映させればいいはず
    * Everywere/Book/Handwrite:
        * Ascent: 17600
        * Descent: 2880
        * Leadline: 0
