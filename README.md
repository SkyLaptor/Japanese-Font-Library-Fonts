# Japanese Font Library - Fonts
[Japanese Font Library](https://github.com/SkyLaptor/Japanese-Font-Library) のフォント部分の分離

## 開発時に使用するツール/MOD
### UniteTTC
TTCをTTFに分解するために利用。  
http://yozvox.web.fc2.com/556E697465545443.html

### FontForge
フォントファイルそのものを編集するために利用。OTF→TTFに変換する用途でも使う。  
https://fontforge.org/

### JPEXS Free Flash Decompiler - ffdec
SWFファイルを操作するために利用。
https://github.com/jindrapetrik/jpexs-decompiler


## 作成手順


太字/斜体オプションは使用しない。ぱっと見何が設定されているかわからなくなるため。

英語版配置と合わせる。

```
Ascent: 19408 (24260*0.8)
Desent: 4852 (24260*0.2)
Leading: 3882 (24260*0.16)
```


## セット
### フルセット
FFdecにてすべての文字を包含する。

### 通常セット
FFdecにて以下で絞る。

* Uppercase
* Lowercase
* Numerals
* Punctuation
* Basic Latin
* Japanese Kana
* Japanese Kanji - Level 1
* Japanese (All)


## TIPS
### OTFをTTFに変換する方法



