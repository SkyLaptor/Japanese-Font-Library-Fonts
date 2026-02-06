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
$ fontforge -quiet -script .\convert_for_skyrim.py --help
usage: convert_for_skyrim.py [-h] -i INPUT [-o OUTPUT] [--subset SUBSET] [--mode_ui MODE_UI]
                             [--ratio_width RATIO_WIDTH] [--resize_mode RESIZE_MODE]

Convert the specified font for Skyrim's UI

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Font file paths subject to converion.
  -o OUTPUT, --output OUTPUT
                        Output font file path. The file extension must be ttf.
  --subset SUBSET       Subset character file path.
  --mode_ui MODE_UI     UI mode(every,book,hand).
  --ratio_width RATIO_WIDTH
                        Width specification(%).
  --resize_mode RESIZE_MODE
                        Resize mode(v,vh,he).
```

### フォントを任意に最適化する
任意のフォントをサブセット化したり、サイズや太さを変形したりしつつ最適化することができる。

```
$ fontforge -quiet -script .\optimize_font.py --help
usage: optimize_font.py [-h] -i INPUT [-o OUTPUT] [--subset SUBSET] [--ascent ASCENT] [--descent DESCENT]
                        [--ratio_total RATIO_TOTAL] [--ratio_width RATIO_WIDTH] [--weight_offset WEIGHT_OFFSET]
                        [--shift_height SHIFT_HEIGHT]

Apply various processing and optimization to the font and output it as a TTF font.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Font file paths subject to optimization.
  -o OUTPUT, --output OUTPUT
                        Output font file path. The file extension must be ttf.
  --subset SUBSET       Subset character file path.
  --ascent ASCENT       Ascent value. Ensure that the total with descent is 1024. If no value is entered, the font
                        value will be used.
  --descent DESCENT     Descent value. Ensure that the total with ascent is 1024. If no value is entered, the font
                        value will be used.
  --ratio_total RATIO_TOTAL
                        Size specification(%).
  --ratio_width RATIO_WIDTH
                        Width specification(%).
  --weight_offset WEIGHT_OFFSET
                        Weight adjustment value(units). Thick for positive values, thin for negative values.
  --shift_height SHIFT_HEIGHT
                        Height adjustment value(units). Thick for positive values, thin for negative values.
```

### OTCやTTCといったフォントコレクションからフォントを抽出する
フォントコレクションの中のフォントを処理する場合、事前にフォントを取り出しておく必要がある。

```
$ fontforge -quiet -script .\extract_font_collection.py --help
usage: extract_font_collection.py [-h] -i INPUT [-o OUTPUT]

Extract fonts from the font collection.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the font collection file to be extracted.
  -o OUTPUT, --output OUTPUT
                        Extraction destination directory.
```

### OTFをTTFに変換する
スクリプト類はTTFが入力されることを想定した処理を行っているため、OTFを使用する場合はまずTTFに変換すること。

```
$ fontforge -quiet -script .\convert_otf2ttf.py --help
usage: convert_otf2ttf.py [-h] -i INPUT [-o OUTPUT]

Convert OpenTypeFont(OTF) to TrueTypeFont(TTF).

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Font file paths subject to convert.
  -o OUTPUT, --output OUTPUT
                        Output font file path. The file extension must be ttf.
```

### フォント同士を組み合わせる
 例えば [しねきゃぷしょん](https://www.vector.co.jp/soft/data/writing/se314690.html) などの、格納されているグリフが少ないフォントをそのまま使用すると一部の文字が豆腐化してしまうことがある。
 そこで [源柔ゴシック](http://jikasei.me/font/genjyuu/) といった字体が似ていて、なおかつ格納グリフ数が多いフォントで補間してあげることで、違和感を最小限に豆腐化を防ぐことができる。
なお、組み合わせるフォントは事前にオプションなしで最適化を施しておくこと推奨。

 ```
$ fontforge -quiet -script .\merge_font.py --help
usage: merge_font.py [-h] -b BASE -s SUB [-o OUTPUT]

Merge fonts and output them as a new font.

options:
  -h, --help            show this help message and exit
  -b BASE, --base BASE  Base font file. The side that is interpolated.
  -s SUB, --sub SUB     Interpolation font file.
  -o OUTPUT, --output OUTPUT
                        Output font file path. The file extension must be ttf.
```


### フォントSWFファイルに変換する
TTFのままではスカイリムでは使用できないため、フォントSWFに変換する必要がある。
ただ、FFDecでは単純に埋め込むだけしかできないため、結局FFDecで開いてフォント名、ExportAssetsの修正が必要。

```:cmd
$ ffdec-cli.exe -replace fonts_template.swf <出力フォントSWF名> 1 <埋め込むフォントファイル(TTF)>

例: example_s97_w100_b0_every.ttfを埋め込んだfonts_test.swfというSWFを作成する。
$ ffdec-cli.exe -replace fonts_template.swf fonts_example_test.swf 1 example_s97_w100_b0_every.ttf
```

#### フォントSWFの命名規則
```
fonts_<フォント名>[特殊ウェイト:_light|_bold|_heavy]<調整モード:_every|_book|_handwrite>[長形:_condensed|_skinny][サブセット:_jp-full|_jp-skyrim].swf

例: noto-sansというフォント名で、ウェイトがBoldで、Everywere向け調整で、70%長形になっていて、サブセットがJPSkyrimの場合
フォント名= noto-sans_bold_every_condensed_jp-skyrim
SWF名: fonts_noto-sans_bold_every_condensed_jp-skyrim.swf
```

## サブセットファイルについて
フォントファイルの中に含めたい文字を記述したテキストファイル（UTF-8エンコードされていること）を用意する。
フォント最適化時に読み込むことで、フォントを軽量化することができる。

### プリセット
#### subset_jp_full.txt
シンボルを含めJIS第4水準まで網羅した、おおよそ日本語圏であれば表示できない文字は無いであろうサブセット。非常に大きい。

#### subset_jp_skyrim.txt
SkyrimSE v1.6.1170 に格納されている日本語フォントを解析し、バニラのSkyrimで表示可能な文字のみに絞ったサブセット。非常に軽量。




