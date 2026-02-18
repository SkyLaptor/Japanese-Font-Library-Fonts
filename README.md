# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント関連サブプロジェクトです。  
お好みのフォントを用意するだけで、スカイリムのUI表示に最適化されたフォントファイルを一括生成できます。


## 動作環境
* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)
フォントファイルをSWFへ埋め込むために必要です。`ffdec-cli` がパスに通っている必要があります。 



* [UV](https://docs.astral.sh/uv/)
スクリプトの実行環境です。OSに合わせて[インストール](https://docs.astral.sh/uv/getting-started/installation/)を完了させてください。
 
* [FontForge](https://fontforge.org/en-US/)
フォントの目視検査、破損したフォントの修復、および手動マージの際に使用します。

## 使い方
### 1. 準備
本リポジトリをクローンまたはダウンロードし、ルートディレクトリで環境構築を行います。

```powershell:
$ uv sync
```

### 2. フォントファイルの用意
使用したいTTFフォントを用意します。  
**OTF形式の場合**: `$ uv run otf2ttf フォントファイル.otf` 等を利用してTTFに変換してください。


> [!TIP]
> フォント製作者よりTTF版が提供されている場合は、変換による不具合防止のため可能な限りそちらを使用してください。

### 3. マージ前処理
グリフを補完するためにフォント同士をマージする前の事前調整（UPM変更や空白グリフ削除）を一括で行います。

1. 作業ディレクトリ (`build`) 内にフォント名ごとのフォルダを作成します。
2. その中に処理対象のフォントファイル(`.ttf`)と、オフセット調整ファイル(`offset_height_everywhere.txt`)を配置します。
オフセット値が不明な場合は、後述の[備考](#オフセット調整ファイルが無い場合)を参照してください。
3. 以下のコマンドを実行します。

```powershell:
$ uv run build_skyrim_fonts --action run_batch_premerge_export --work_dir build
```

実行後、フォルダ内にあるすべてのフォントに対して `*-premerge.ttf` が生成されます。

### 4. フォントのマージ (手動)
FontForgeを使用して、メインフォントにサブフォントを統合します。

   1. **基準となるフォント**（`*-premerge.ttf`）を FontForge で開きます。
   2. メニュー **[エレメント]** > **[フォントの統合]** を選択し、マージしたいフォントを開きます。
   3. メニュー **[ファイル]** > **[フォントを出力]** で、マージ済みフォントを保存します。
      * **重要**: ファイル名末尾を必ず `*-merged.ttf` にしてください（次の工程のトリガーになります）。

> [!NOTE]
> 単一フォントで使用し、マージが不要な場合は `*-premerge.ttf` をコピーして `*-merged.ttf` にリネームしてください。

### 5. フォントバリエーション作成
スカイリムの各用途（全般、本、手書き）に合わせたサブセットと、長体（Condense）モデルを一括生成します。

```powershell:
$ uv run build_skyrim_fonts --action run_batch_variant_export --work_dir build
```

実行後、`*-full.ttf` や `*-skyrim.ttf` などのバリエーションファイルが生成されます。

### 6. フォントSWFの作成
生成されたTTFを、ゲームが読み込み可能なSWF形式へ変換し、内部フォント名をパッチします。

```powershell:
$ uv run build_skyrim_fonts --action run_batch_swf_export --work_dir build
```

`build` ディレクトリ内に、スカイリム用フォントSWF（`fonts_*.swf`）が作成されます。

### 7. スカイリムへの適用
1. 作成されたSWFファイルを `Skyrim/Data/Interface` フォルダへ配置します。
2. 同フォルダの `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。
   * **読み込み設定**: 上部に `fontlib "Interface\作成したファイル名.swf"` を追記。
   * **割り当て設定**: 各 `map` 行の右側を、[手順6](#6-フォントswfの作成)で設定されたフォント名（内部名）に書き換えます。

## 備考
### オフセット調整ファイルが無い場合
フォントの上下位置をバニラの基準に合わせるための数値を算出します。

1. まず `*-premerge.ttf` を作成します（`$ uv run builder --action run_batch_premerge_export --work_dir build` を実行）。
2. 生成されたファイルに対し、以下のコマンドでオフセット値を取得します。

```powershell:
$ uv run inspector --action get_offset_to_align_bottom -i フォントファイル-premerge.ttf
# 出力例: オフセット値: XXX
```
3. この数値を記載したテキストファイルを `offset_height_everywhere.txt` という名前でフォントフォルダに保存し、再度マージ前処理を実行してください。
