# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント部分分離プロジェクト。
フォントファイルをスカイリム向けに最適化するためのスクリプト類及び最適化済フォントファイルを保管する。

## 動作確認環境
* [Python](https://www.python.org/) v3.14.2
* [FontForge](https://fontforge.org/en-US/) v2025-10-09
* [JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) v24.1.2


## 動作環境のセットアップ
### Pythonインストール
OSに直接インストールするか、[uv](https://docs.astral.sh/uv/getting-started/)などのPython環境仮想化を用いてOS環境を汚さないようにしても良い。
本READMEにおいては、`python`へのパスが通っているものとする。

### FontForgeインストール
フォントファイルを編集するため、[FontForge](https://fontforge.org/en-US/) をインストールする。
本READMEにおいては、`fontforge`へのパスが通っているものとする。

### JPEXS Free Flash Decompilerのインストール
フォントファイルをSWFに変換するため、[JPEXS Free Flash Decompiler](https://github.com/jindrapetrik/jpexs-decompiler) をインストールする。
本READMEにおいては、`ffdec-cli`及び`ffdec`へのパスが通っているものとする。

## フォントを最適化する
最適化したいフォントなどをパラメーターとして渡す。

```
$ fontforge -script optimize_font.py <フォントファイル> <サブセット> <横幅%> <サイズ%> <ウェイト調整>

例: fonts/test_font.ttf をsubset.txtの内容でサブセット化しつつ、ウェイトを15増やす（太字にする）
$ fontforge -script optimize_font.py fonts/source_font.ttf subset.txt 100 100 15
```





