# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント関連サブプロジェクトです。  
お好みのフォントを用意するだけで、スカイリムのUI表示に最適化されたフォントファイルを生成できます。  


## 動作環境
* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)

フォントファイルをSWFへ埋め込むために必要です。  

* [UV](https://docs.astral.sh/uv/)

スクリプトの実行環境です。OSに合わせて[インストール](https://docs.astral.sh/uv/getting-started/installation/)を完了させてください。  
 

## 使い方
1. 本リポジトリをクローンまたはダウンロードします。

2. ターミナルでリポジトリのルートディレクトリへ移動し、以下のコマンドを実行して環境を構築します。

```:PowerShell
$ uv sync
```

3. 使用したいTTFフォントを用意します。
   * **OTF形式の場合**: 以下のコマンドでTTFに変換してください。

```:PowerShell
$ uv run otf2xml フォントファイル.otf
```

> [!TIP]
> フォント製作者よりTTF版が提供されている場合は、不具合防止のため可能な限りそちらを使用してください。

4. フォントの最適化

以下のコマンドを実行して、スカイリム用フォントを生成します。

```
$ uv run convert_for_skyrim フォントファイル.ttf --base everywhere --subset ./data/subsets/subset_jp_skyrim.txt
```

* **実行内容**: スカイリム標準の Everywhere 日本語フォントに合わせてサイズを調整し、バニラで表示可能な文字のみに絞り込んだ（サブセット化）TTFファイルを `build` ディレクトリ内に出力します。
* **カスタマイズ**: 基準サイズの変更、長体（コンデンス）の適用、サブセットの変更などが可能です。詳細は `$ uv run convert_for_skyrim --help` を参照してください。

5. SWFへの埋め込み
   1. **FFDec**を起動し、 `assets/swf/skyrim/fonts_template.swf` を開きます。
   2. 左ツリーの **[フォント]** > **[DefineFont3]** を選択し、右下の **[埋め込む]** をクリック。
   3. 手順2で生成したTTFファイルを選択し、 **[全ての文字]** にチェックを入れて [OK]（上書き警告は「全て上書き」）。
   4. **[名前を付けて保存]** で、 `build` ディレクトリ内へ `fonts_任意の名前.swf` として保存します。

> [!NOTE]
> FFDecをコマンドラインから実行可能な場合は、以下のコマンドで一括処理できます。

5. SWFタグ情報の編集

* 保存したSWFを再度FFDecで開き、以下の3箇所を編集します（右下の [編集] ボタンから値を変更後、 [保存] を押してください）。
  * **DefineFont3**: [タグ内のフォント名] の `template` を任意の英数字に変更。
  * **DefineFontName**: `fontName:String="template"` を上記と同じ名前に変更。
  * **ExportAssets**: assets 内の `tag[0]:U16=1, name[0]:String="template"`を上記と同じ名前に変更。

6. スカイリムへの適用
   1. 作成したSWFを `Skyrim/Data/Interface` フォルダへ配置します。
   2. 同フォルダの `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。
      * **フォント読み込み設定**: 上部に `fontlib "Interface\作成したファイル名.swf"` を追記。
      * **フォント割り当て設定**: 中段の各 `map` 行の右側を、手順4で設定した「フォント名」に書き換えます。
        * **一般的なUI（字幕・メニュー等）**: `$StartMenuFont`, `$DialogueFont`, `$EverywhereFont` など。
        * **本・手紙**: `$SkyrimBooks`, `$HandwrittenFont` など。

7. 完了

ゲームを起動し、フォントが美しく適用されていることを確認してください！
