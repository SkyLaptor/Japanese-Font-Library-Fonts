# ユーザーガイド

このディレクトリには、ツールの使い方やレシピの書き方などのユーザー向けドキュメントを配置します。

## 詳細準備
### 【オプション】基準フォントの準備（ゲームデフォルトの日本語フォント）

基準フォントとしてゲームデフォルトのフォントを使用する場合の手順です。

1. 最新版のSkyrimSE 英語版をインストールします。（v1.6.1170以降には日本語フォントが含まれています）。

2. `Skyrim\Data\Skyrim - Interface.bsa` をBSA Browserで開きます。

3. `interface\fonts_ja.swf` を取り出し、FFDecで開きます。

4. 左ツリーの **[フォント]** から、任意のフォントを右クリックして **[エクスポート]** します。
   * **Every**: `1_Skyrim_JP_EveryFont_0805`
   * **Book**: `22_Skyrim_JP_BookFont_0805`
   * **Handwrite**: `5_Skyrim_JP_HandWriteFont_0805`

5. このツールを起動し、**[個別:フォント加工]** タブで、空白グリフ除去を有効(デフォルト)にして、他は何も変更せずに出力します。
   * 出力先: `contents\skyrim\1_Skyrim_JP_EveryFont_0805.ttf` / `22_Skyrim_JP_BookFont_0805.ttf` / `5_Skyrim_JP_HandWriteFont_0805.ttf`

