# TESVFontForge
お好みのフォントファイル（TTF/OTF）を、スカイリムのゲーム内で使用可能な形式（SWF）へ変換・加工するツールです。

## 動作環境
以下のツールを事前にインストールしてください。

* **[UV](https://docs.astral.sh/uv/)**  
Python実行環境を自動管理するツールです。PowerShellを起動し、以下のコマンドを実行するだけでインストールが完了します。

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## 使い方
基本的な流れを説明します。詳細は [ユーザー向けマニュアル](/docs/user/README.md) を参照してください。

### 1. ツールのダウンロード
[Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/174143) または [GitHub](https://github.com/SkyLaptor/TESVFontForge/releases) から最新版をダウンロードしてください。

### 2. フォントの準備
使用したいフォントを用意します。

> [!TIP]
> OTF形式も使用可能ですが、変換を高速化したい場合は、事前に以下のコマンドでTTFに変換しておくことを推奨します。
> `uv run otf2ttf [フォントファイル]`

### 3. 【任意】フォントの加工
太さや幅を調整したい場合は、トップの `run.cmd` を実行してGUIを起動します。
`個別：フォント加工` タブから、プレビューを確認しながら調整してください。

![TESVFontForge-フォント加工](https://github.com/user-attachments/assets/281af337-622f-4e6f-89df-f13e74602689)

### 4. SWFへの埋め込み
ゲームで認識させるために、フォントをSWF形式に変換します。
GUIの `個別：SWF埋め込み` タブにて、出力先とフォント内部名を指定して実行してください。

![TESVFontForge-SWF埋め込み](https://github.com/user-attachments/assets/3f6662ba-a8ef-4102-af41-fa74067901e5)

### 5. ゲームへの導入
生成されたSWFをゲームに反映させるには、姉妹ツールの [TESVFontPresetBuilder](https://github.com/SkyLaptor/TESVFontPresetBuilder) を使用するのが最も簡単で確実です。

## クレジット・利用について
* 本ツールで作成したフォントをMODとして公開する際、連絡は不要ですが、ツール名を紹介いただけると開発の励みになります。
