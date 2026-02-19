[![Python Tests (Windows)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/SkyLaptor/Japanese-Font-Library-Fonts/actions/workflows/python-tests.yml)

# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のサブプロジェクトです。  
お好みの日本語フォント（TTF）から、スカイリムのUI表示に最適化されたフォントファイル（SWF）を一括生成します。


## 動作環境
以下のツールをインストールし、コマンドラインから呼び出せるように設定してください。

* [UV](https://docs.astral.sh/uv/)  
Python実行環境。

* [JPEXS Free Flash Decompiler - FFDec](https://github.com/jindrapetrik/jpexs-decompiler)  
SWF埋め込み用。`ffdec-cli` にパスを通してください。

* [FontForge](https://fontforge.org/en-US/)  
フォント修復・マージ用。`fontforge` にパスを通してください。

> [!NOTE]
> **「パスを通す」とは？**
> ターミナルで `ffdec-cli` と打つだけでプログラムが起動するように、Windowsの環境変数 `Path` に実行ファイルの場所を登録することです。

![Windows環境変数-Path](https://github.com/user-attachments/assets/2ed25f9e-f138-46c0-be95-1caff284045d)

![Windows環境変数-Path-FontForge-FFDec](https://github.com/user-attachments/assets/71e5e2f9-2731-4b55-a248-c64858352045)

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

![作業ディレクトリの配置-フォントとオフセット配置](https://github.com/user-attachments/assets/f86a738c-4d8c-4963-98ad-d3edd8aed12d)

> [!IMPORTANT]
> オフセット調整ファイル（`offset_height_every.txt`）について  
> フォントの上下位置をバニラに合わせるための設定ファイルです。持っていない場合は、以下のコマンドで生成してください。

```powershell:
# 一度仮のプリマージを行い、オフセット値を算出する例
uv run builder --action run_batch_premerge_export --work_dir build
uv run get_offset_to_align_bottom build/YourFontName/YourFont_premerge.ttf -o build/YourFontName/offset_height_every.txt
# 生成後、一度 *_premerge.ttf は削除してください
```

### 3. プリマージ処理（最適化）
UPMの変更や空白グリフの削除など、スカイリム向けの事前調整を行います。

```powershell:
uv run builder --action run_batch_premerge_export --work_dir build
```

実行後、 `*_premerge.ttf` が生成されます。

![プリマージ処理（最適化）-完了](https://github.com/user-attachments/assets/4101eb65-7ad6-45fd-8a6e-b8d6286d18fb)

### 4. フォントのマージ（任意）
不足している文字を別のフォントで補完したい場合、FontForgeを使用してマージします。  
※ マージが不要な場合は、`*_premerge.ttf` を `*_merged.ttf` にリネームして進めてください。

```powershell:
fontforge .\src\utils\modifier\merge_font_ff.py ベースフォント_premerge.ttf 補間フォント_premerge.ttf -o build\任意のフォント名_merged.ttf
```

![フォントのマージ（任意）-完了](https://github.com/user-attachments/assets/83151bc7-8d5f-4905-809f-e3aa520d655e)


### 5. バリエーション生成
用途別（本、手書き、長体モデルなど）のサブセットを一括生成します。

```powershell:
uv run builder --action run_batch_variant_export --work_dir build
```

![バリエーション生成](https://github.com/user-attachments/assets/c05f928a-4aea-4942-9ce2-492dfc1a6927)

### 6. SWFファイルの作成
ゲームが読み込める形式へ変換します。**※非常に重い処理です**

```powershell:
uv run builder --action run_batch_swf_export --work_dir build
```

![SWFファイルの作成-完了](https://github.com/user-attachments/assets/e4acade3-1432-473a-9888-36567f7b8b62)

* **注意**: 作業ドライブに1GB以上の空き容量を確保してください。
* 生成された `fonts_*.swf` の「内部フォント名」は、ファイル名から `fonts_` を除いたものになります。

### 7. スカイリムへの適用
1. 作成されたSWFを `Skyrim/Data/Interface` に配置します。

![スカイリムへの適用-フォントSWF配置](https://github.com/user-attachments/assets/60210728-718b-40bc-a259-930dddcc4721)

2. `fontconfig.txt`（または `fontconfig_ja.txt`）を編集します。

   * **fontlib**: `fontlib "Interface\作成したファイル名.swf"` を追記。

![スカイリムへの適用-fontlib記述](https://github.com/user-attachments/assets/bff386ee-96a6-4751-859a-5d5571e53bdd)

   * **map**: 各行のフォント指定を、[手順6](#6-swfファイルの作成)で設定された内部フォント名に書き換えます。

![スカイリムへの適用-map変更](https://github.com/user-attachments/assets/d76f43e0-b28a-4a19-8db4-2726c4b9f15c)


## 💡Tips & トラブルシューティング
* **処理が失敗する**: メモリ不足やディスク容量不足を確認してください。

* **文字が「豆腐（□）」になる**: 使用したフォントがそのグリフを保持していない可能性があります。以下のコマンドで保持グリフを確認できます。

```powershell:
uv run get_glyphs build/YourFontName/YourFont_every.ttf -o build/YourFontName/YourFont_every_glyphs.txt
```