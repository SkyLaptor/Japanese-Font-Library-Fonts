# TESVFontForge
お好みのフォントから、スカイリム向けのフォントファイルを生成します。


## 動作環境
以下のツールをインストールして下さい。

* **[UV](https://docs.astral.sh/uv/)**  
Python実行環境です。PowerShellを起動し、以下のコマンドを実行するとインストールできます。

```powershell:uvインストール
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```


## 使い方
### 1. 準備
1. 本ツールをダウンロードします。

2. 使用したいフォント（`.ttf`）を用意します。

> [!TIP]
> OTF形式のフォントは、事前にTTFへ変換してからGUIへ入力してください。
