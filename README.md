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

お好みのフォントをゲーム内で表示できるようになるまでの一連の流れを説明します。より詳細な使い方を知りたい場合は [ユーザー向けマニュアル](/docs/user/README.md) を参照してください。

### 1. 本ツールをダウンロードする
ダウンロードは [Nexus](https://www.nexusmods.com/skyrimspecialedition/mods/174143) もしくは [GitHub](https://github.com/SkyLaptor/TESVFontForge/releases)から可能です。

### 2. 使用したいフォントを用意する

お好みのフォントファイルを用意します。

> [!TIP]
> OTF形式(`.otf CFF/CFF2`)のフォントも使用可能ですが、内部で変換処理が行われて余分に時間がかかるため、以下のコマンドで事前にTTF形式に変換しておくことをお勧めします。
> `uv run otf2ttf OTFフォント` ※同じフォルダに同名の.ttfが作成されます。

### 3. 【オプション】フォントを加工する
フォントの幅を変更したり、太さを変更したりしたい場合は、ゲーム向けの形式（SWF）にする前に加工が必要です。不要であればこの手順はスキップしてください。

本ツールのトップにある `run.cmd` をダブルクリックすると、ツールが起動します。  

![run.cmd](https://github.com/user-attachments/assets/b792d1f6-00e8-4af0-92a9-31f9f36254b9)

`個別：フォント加工` タブにてお好みの加工を施して下さい。詳細は各項目にカーソルを合わせると説明が表示されます。

![TESVFontForge-フォント加工](https://github.com/user-attachments/assets/281af337-622f-4e6f-89df-f13e74602689)

### 4. フォントをSWFに埋め込む

フォントファイルのままではゲーム内で使用できません。SWFに変換する必要があります。

本ツールを起動し、

`個別：SWF埋め込み` タブにてSWF出力先の指定及び埋め込むフォントファイルとその内部名を指定してください。

![TESVFontForge-SWF埋め込み](https://github.com/user-attachments/assets/3f6662ba-a8ef-4102-af41-fa74067901e5)

> [!CAUTION]
> 1つのSWF内に複数のフォントを埋め込むことが出来ますが、あまりたくさん入れるとSWFファイルが大きくなりゲームに負荷がかかります。

### 5. 出来上がったSWFをゲームに読み込ませる

姉妹ツールである [TESVFontPresetBuilder](https://github.com/SkyLaptor/TESVFontPresetBuilder) を使用するのが最も確実です。

利用方法及びゲームへの読み込ませ方については、リンク先をご確認下さい。


## お願い
* 本ツールで作成したフォントを使ってMODとして公開する場合、特に連絡は不要ですが、本ツールを使用した旨を紹介いただけると開発者が喜びます。
