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

![作業ディレクトリの配置-フォント配置](https://github.com/user-attachments/assets/2314e0ba-9794-4a24-94ec-330bb331397b)

### 3. 変換実行
作業ディレクトリに配置したフォントをスカイリム向けのフォントに変換します。

```powershell:
cmd /c build_fon_skyrim.cmd
```


### 3. フォントのマージ（任意）
変換処理を実行ししばらくすると、マージ待ち状態になります。  
変換処理はそのままにし、マージを行ってください。

※ マージが不要な場合は、`*_premerge.ttf` を `*_merged.ttf` にリネームして進めてください。

```powershell:
fontforge .\src\utils\modifier\merge_font_ff.py ベースフォント_premerge.ttf 補間フォント_premerge.ttf -o build\任意のフォント名_merged.ttf
```

![フォントのマージ（任意）-完了](https://github.com/user-attachments/assets/83151bc7-8d5f-4905-809f-e3aa520d655e)

> [!NOTE]
> 既にマージパターンが決まっているのであれば、merge.cmd内にそれを記載することで、都度手動でマージする必要がなくなります。

マージが完了しましたら、変換処理を再開して下さい。

### 4. スカイリムへの適用
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