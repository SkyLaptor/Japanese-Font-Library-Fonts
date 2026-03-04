[![Python Tests (Windows)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml)

# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のサブプロジェクトです。  
お好みの日本語フォント（TTF）から、スカイリムのUI表示に最適化されたフォントファイル（SWF）を一括生成します。


## 動作環境
以下のツールをインストールして下さい。

* **[UV](https://docs.astral.sh/uv/)**  
Python実行環境。

```powershell:uvインストール
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```


* **[FFDec](https://github.com/jindrapetrik/jpexs-decompiler)**  
SWF作成時に使用します。`data/ffdec/ffdec.jar` に配置してください。


## 使い方
### 1. 準備
1. 本リポジトリをクローンまたはダウンロードします。

2. 使用したいフォント（`.ttf`）を用意します。

> [!TIP]
> OTF形式の場合は、`uv run otf2ttf sample.otf` で変換可能です。

### 2. 作業ディレクトリの配置
`build` フォルダ内にフォント名ごとのフォルダを作成し、フォントファイルを配置します。

* **配置例**: build/YourFontName/YourFont.ttf

![作業ディレクトリの配置-フォントフォルダ](https://github.com/user-attachments/assets/47ce4637-fe40-4a72-96f7-b73096842166)

![作業ディレクトリの配置-フォント配置](https://github.com/user-attachments/assets/2314e0ba-9794-4a24-94ec-330bb331397b)

### 3. 変換実行
作業ディレクトリに配置したフォントをスカイリム向けのフォントに変換します。  
`build.cmd` をダブルクリックで実行して下さい。

#### フォントのマージ
`build.cmd` を実行してしばらくするとマージ待ちによる一時停止状態になります。  
`build.cmd` の画面はそのままにし、マージ設定ファイルを設定してください。

**マージ設定ファイルの作成**  
`build.cmd` と同じ場所にある `merge_conf.csv` を開き、サンプル値やコメントを参考に設定して下さい。

マージ設定ファイルの準備が完了しましたら、`build.cmd` を再開して下さい。

### 4. スカイリムへの適用
1. 作成されたSWFを `Skyrim/Data/Interface` に配置します。

![スカイリムへの適用-フォントSWF配置](https://github.com/user-attachments/assets/60210728-718b-40bc-a259-930dddcc4721)

2. `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。

   * **fontlib**: `fontlib "Interface\作成したファイル名.swf"` を追記。

![スカイリムへの適用-fontlib記述](https://github.com/user-attachments/assets/bff386ee-96a6-4751-859a-5d5571e53bdd)

   * **map**: 各行のフォント指定を、`fontlib` で読み込ませたフォントの内部フォント名に書き換えます。

![スカイリムへの適用-map変更](https://github.com/user-attachments/assets/d76f43e0-b28a-4a19-8db4-2726c4b9f15c)

> [!NOTE]
> 内部フォント名とは？  
> SWFには内部にフォントが埋め込まれており、それに対し名前がついています。  
> 当プロジェクトでビルドされたフォントは、SWF名から `fonts_` を除いたものがそのまま内部フォント名になります。


## 💡Tips & トラブルシューティング
* **特定の処理だけやり直したい**: 各ステップごとの処理バッチが用意されています。
   * `01_font_optimize.cmd` : フォントの事前最適化処理
   * `02_font_merge.cmd` : フォントのマージ処理 ※事前にマージ設定 (`merge_conf.csv`) の準備が必要です。
   * `03_generate_variant.cmd` : フォントのバリエーション生成処理
   * `04_create_swf.cmd` : フォントSWFの作成処理

* **SWF変換時に失敗する**: `data/ffdec/ffdec.jar` と `data/jre/bin/java(.exe)` の配置を確認してください。

* **処理がたまに失敗する**: メモリ不足やディスク容量不足を確認してください。

* **文字の一部が「豆腐（□）」になる**: 使用したフォントがそのグリフを保持していない可能性があります。以下のコマンドで保持グリフを確認できます。

```powershell:
uv run get_glyphs build/YourFontName/YourFont_every.ttf -o build/YourFontName/YourFont_every_glyphs.txt
```