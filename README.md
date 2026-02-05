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
### フォントを最適化する
最適化したいフォントに対し、サブセットなどをパラメーターとして渡す。

```
$ fontforge -quiet -script optimize_font.py <フォントファイル> <サブセット> <横幅%> <サイズ%> <ウェイト調整>

例: local/test_font.ttf をsubset.txtの内容でサブセット化しつつ、ウェイトを15増やす（太字にする）
$ fontforge -quiet -script optimize_font.py local/source_font.ttf subset.txt 100 100 15
```

### OTFフォントをTTFフォントに変換する
最適化スクリプトにも組み込んでいるが、単体でOTF→TTFへの変換も可能。

```
$ fontforge -quiet -script convert_otf2ttf.py <OTFフォントファイル>

例: local/test_font.otf を local/test_font.ttf に変換する
$ fontforge -quiet -script convert_otf2ttf.py local/source_font.otf
```

### TTC(TTFコレクション)を分解する
TODO

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




