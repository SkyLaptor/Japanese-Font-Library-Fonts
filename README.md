# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント部分分離プロジェクト。
フォントファイルをスカイリム向けに最適化するためのスクリプト類及び最適化済フォントファイルを保管する。

## 動作確認環境
* OS: Windows11 Pro build26200.7628
* [FontForge](https://fontforge.org/en-US/) v2025-10-09
* [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) v24.1.2

## 動作環境のセットアップ
### FontForgeインストール
フォントファイルを編集するため、[FontForge](https://fontforge.org/en-US/) をインストールする。
本READMEにおいては、`fontforge`へのパスが通っているものとする。

### JPEXS Free Flash Decompilerのインストール
フォントファイルをSWFに変換するため、[JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) をインストールする。
本READMEにおいては、`ffdec-cli`及び`ffdec`へのパスが通っているものとする。

## 使い方
### スカイリム向けにフォントを最適化する
任意のフォントを、バニラのフォント類(Everywere,Book,Handwritten)に準拠した形で最適化することができる。

```
$ fontforge -quiet -script optimize_skyrim_font.py <フォントファイルパス> [サブセットファイルパス] [モード(every/book/handwrite
)] [横幅指定(%)] [ウェイト調整値(em)] [サフィックス]

例: example.ttfをEverywereフォントに準拠した形で最適化する。
$ fontforge -quiet -script optimize_skyrim_font.py example.ttf subset_jp_skyrim.txt every

例: example.ttfをEverywereフォントに準拠した形で、横幅を70%にして最適化する。
$ fontforge -quiet -script optimize_skyrim_font.py example.ttf subset_jp_skyrim.txt every 70
```

### フォントを任意に最適化する
任意のフォントをサブセット化したり、サイズや太さを変形したりしつつ最適化することができる。

```
$ fontforge -quiet -script optimize_font.py <フォントファイルパス> [サブセットファイルパス] [サイズ指定(%)] [横幅指定(%)] [ウェイト調整値(em)] [メトリック値(x,y em)] [プレフィクス] [サフィックス]

例: example.ttfをsubset_jp_skyrim.txtに従いサブセット化しつつ横幅を70%にする。
$ fontforge -quiet -script optimize_font.py example.ttf subset_jp_skyrim.txt 100 70
```

### OTCやTTCといったフォントコレクションからフォントを抽出する
フォントコレクションの中のフォントを処理する場合、事前にフォントを取り出しておく必要がある。

```
$ fontforge -quiet -script extract_font_collection.py <フォントコレクションファイル>

例: example.ttc内のttfファイルを抽出する。
$ fontforge -quiet -script extract_font_collection.py example.ttc
```

### フォントをSWFに変換する
TODO


## サブセットファイルについて
フォントファイルの中に含めたい文字を記述したテキストファイル（UTF-8エンコードされていること）を用意する。
フォント最適化時に読み込むことで、フォントを軽量化することができる。

### プリセット
#### subset_jp_full.txt
シンボルを含めJIS第4水準まで網羅した、おおよそ日本語圏であれば表示できない文字は無いであろうサブセット。非常に大きい。

#### subset_jp_skyrim.txt
[TESVKanjiChecker v1.4.2](https://www.nexusmods.com/skyrim/mods/66768)を参考に、バニラのSkyrimで表示可能な文字のみに絞ったサブセット。非常に軽量。




