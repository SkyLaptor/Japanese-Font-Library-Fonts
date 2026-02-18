# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント関連サブプロジェクトです。  
お好みのフォントを用意するだけで、スカイリムのUI表示に最適化されたフォントファイルを一括生成できます。


## 動作環境
* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)
フォントファイルをSWFへ埋め込むために必要です。`ffdec-cli` がパスに通っている必要があります。 

* [UV](https://docs.astral.sh/uv/)
スクリプトの実行環境です。OSに合わせて[インストール](https://docs.astral.sh/uv/getting-started/installation/)を完了させてください。
 
* [FontForge](https://fontforge.org/en-US/)
フォントの目視検査、破損したフォントの修復、およびマージの際に使用します。`fontforge` がパスに通っている必要があります。 

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
2. その中に処理対象のフォントファイル(`.ttf`)と、オフセット調整ファイル(`offset_height_every.txt`)を配置します。
オフセット値が不明な場合は、後述の[備考](#オフセット調整ファイルが無い場合)を参照してください。
3. 以下のコマンドを実行します。

```powershell:
$ uv run builder --action run_batch_premerge_export --work_dir build
```

実行後、フォルダ内にあるすべてのフォントに対して `*_premerge.ttf` が生成されます。

### 4. フォントのマージ
以下のコマンドを実行します。

```powershell:
$ fontforge .\src\utils\modifier\merge_font_ff.py ベースフォント_premere.ttf 補間フォント_premerge.ttf -o build\任意のフォント名_merged.ttf
```

> [!NOTE]
> 単一フォントで使用し、マージが不要な場合は `*_premerge.ttf` をコピーまたはそのまま `*_merged.ttf` にリネームしてください。

### 5. フォントバリエーション作成
スカイリムの各用途（全般、本、手書き）に合わせたサブセットと、長体（Condense）モデルを一括生成します。

```powershell:
$ uv run builder --action run_batch_variant_export --work_dir build
```

実行後、`フォント名_every.ttf` や `フォント名_book_lightweight.ttf` などのバリエーションファイルが生成されます。

### 6. フォントSWFの作成
生成されたTTFをゲームが読み込み可能なSWF形式へ変換します。

```powershell:
$ uv run builder --action run_batch_swf_export --work_dir build
```

実行後、スカイリム用フォントSWF（`fonts_*.swf`）が作成されます。

> [!NOTE]
> 非常に重い処理です。場合により処理に失敗することがあります。

### 7. スカイリムへの適用
1. 作成されたSWFファイルを `Skyrim/Data/Interface` フォルダへ配置します。
2. 同フォルダの `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。
   * **読み込み設定**: 上部に `fontlib "Interface\作成したファイル名.swf"` を追記。
   * **割り当て設定**: 各 `map` 行の右側を、[手順6](#6-フォントswfの作成)で設定されたフォント名（内部名）に書き換えます。

## 備考
### オフセット調整ファイルが無い場合
フォントの上下位置をバニラの基準に合わせるための数値を算出します。

1. まず `*_premerge.ttf` を作成します（`$ uv run builder --action run_batch_premerge_export --work_dir build` を実行）。
2. 生成された `*_premerge.ttf` ファイルに対し、以下のコマンドでオフセット値を取得します。

```powershell:
$ uv run get_offset_to_align_bottom build\フォント名\フォントファイル-premerge.ttf -o build\フォント名\offset_height_everywhere.txt
```

3. この時点で生成された `*_premerge.ttf` ファイルはオフセット値が適用されていないため不要なファイルとなります。削除してからもう一度[マージ前処理](#3-マージ前処理)を実施して下さい。