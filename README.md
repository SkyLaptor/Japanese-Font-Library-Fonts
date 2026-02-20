[![Python Tests (Windows)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml)

# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のサブプロジェクトです。  
お好みの日本語フォント（TTF）から、スカイリムのUI表示に最適化されたフォントファイル（SWF）を一括生成します。


## 動作環境
以下のツールをインストールし、コマンドラインから呼び出せるように設定してください。

* [UV](https://docs.astral.sh/uv/)  
Python実行環境。

* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)  
TTFをSWFに埋め込む処理を行う際に必要です。

* [FontForge](https://fontforge.org/en-US/)  
TTFをマージする処理を行う際に必要です。


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

```powershell:
cmd /c build_for_skyrim.cmd
```


### 4. フォントのマージ（任意）
変換処理を実行ししばらくすると、マージ待ち状態になります。  
変換処理はそのままにし、マージ設定ファイルを作成してください。

**マージ設定ファイルの作成**  
`merge_conf.csv` を開き、以下の様に設定して下さい。

* **1列目(ベースフォント)**: `build\` を**除いた**ファイルパス
* **2列目(補間フォント)**: `build\` を**除いた**ファイルパス
* **3列目(出力先)**: `build\` を**除いた**出力先。末尾に `_merged` とつけるのを忘れないようにしてください。

マージが完了しましたら、変換処理を再開して下さい。

### 5. スカイリムへの適用
1. 作成されたSWFを `Skyrim/Data/Interface` に配置します。

![スカイリムへの適用-フォントSWF配置](https://github.com/user-attachments/assets/60210728-718b-40bc-a259-930dddcc4721)

2. `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。

   * **fontlib**: `fontlib "Interface\作成したファイル名.swf"` を追記。

![スカイリムへの適用-fontlib記述](https://github.com/user-attachments/assets/bff386ee-96a6-4751-859a-5d5571e53bdd)

   * **map**: 各行のフォント指定を、[手順5](#5-スカイリムへの適用)で設定された内部フォント名に書き換えます。

![スカイリムへの適用-map変更](https://github.com/user-attachments/assets/d76f43e0-b28a-4a19-8db4-2726c4b9f15c)


## 💡Tips & トラブルシューティング
* **SWF変換時に失敗する**: FFDecのインストール場所が、本ツールが想定する場所に無いのかもしれません。`.env` ファイルを開き、 `FFDEC_PATH` を実際の場所に修正してください。※注意: 区切り文字は ￥マーク(`\`)ではなく、バックスラッシュ(`/`)としてください。

* **処理がたまに失敗する**: メモリ不足やディスク容量不足を確認してください。

* **文字が「豆腐（□）」になる**: 使用したフォントがそのグリフを保持していない可能性があります。以下のコマンドで保持グリフを確認できます。

```powershell:
uv run get_glyphs build/YourFontName/YourFont_every.ttf -o build/YourFontName/YourFont_every_glyphs.txt
```