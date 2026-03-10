# アセット準備ガイド

本プロジェクトで必要なベースフォントやテンプレートSWFの作成手順です。

## ゲームデフォルトの日本語フォントの取り出し
1. 最新版のSkyrimSE 英語版をインストールします。（v1.6.1170以降には日本語フォントが含まれています）。
2. `Skyrim\Data\Skyrim - Interface.bsa` をBSA Browserで開きます。
3. `interface\fonts_ja.swf` を取り出し、FFDecで開きます。
4. 左ツリーの「フォント」から、任意のフォントを右クリックして「エクスポート」します。

## ベースフォントの作成
カスタムフォントのサイズ調整の基準となるフォントです。

1. 取り出した `.swf` から以下の3種類をエクスポートします。
   * **Every**: `1_Skyrim_JP_EveryFont_0805`
   * **Book**: `22_Skyrim_JP_BookFont_0805`
   * **Handwrite**: `5_Skyrim_JP_HandWriteFont_0805`
2. GUIの「個別処理」タブで、空白グリフ除去を有効にして保存します。
   * 保存先: `contents\skyrim\every.ttf` / `book.ttf` / `handwrite.ttf`

## コアフォントSWF (`fonts_core.swf`) の作成
ゲーム内で使用する特殊フォント（ボタン、ドラゴン文字等）をまとめたSWFです。

1. バニラの `fonts_ja.swf` から以下のフォントをエクスポートします。
   * `Controller Buttons`, `Controller Buttons inverted`, `Dragon_script`, `Daedric`, `Dwemer`, `Falmer`, `SkyrimSymbols`, `Mage Script`, `SkyrimBooks_Unreadable`
2. FFDecの [New empty] から新規SWFを作成し、上記フォントを追加します。
   * **ヘッダー設定**: 無圧縮, バージョン10, フレームレート24.0, サイズ0
   * 各フォントのメトリクス値（Ascent等）はバニラの値を正確に再現してください。

## フォントテンプレートSWFの作成
フォントを格納するための中身が空のフォントSWFです。

1. [New empty] から新規SWFを作成します。
2. `DefineFont3` (chid:1) を追加し、フォント名を以下に設定します。
   * `dummy`

## テンプレートフォントコンフィグの作成
`fontconfig.txt` のマスターを作成します。

1. 各バージョンの英語版・日本語版の `fontconfig.txt` を比較し、重複なく `map` を結合します。
2. マップ先のフォント名は原則 `template` 等に置き換え、プロジェクト固有のパスに調整します。
3. `$MCMFont` などのカスタムマップも追加します。
