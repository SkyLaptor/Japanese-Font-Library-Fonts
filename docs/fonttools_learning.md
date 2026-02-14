# FontToolsの学習
重要だと感じたところをピックアップして学習記録として残します。

## フォントファイルを開く（TTFontオブジェクト化）
なにはともあれ、pythonで操作できるようにならなければなりません。

```python:Example
from fontTools.ttLib import TTFont

def load_font(input_path: Str):
    font_obj = TTFont(input_path) # TTFontオブジェクトとして利用可能にする
```


## Unicodeとグリフの紐付け (cmap テーブル)
「どの文字コード（Unicode）が、どのグリフID（GID）を呼び出すか」を管理するのが cmap です。

* **GID (Glyph ID)** とは？: フォント内部での 0 から始まるインデックス番号です。

* CID (Character ID)は主としてAdobe-Japan1などの「文字コレクション」に基づくIDですが、現代のOpenTypeにおいては、まずはこの cmap によるマッピングを理解するのが先決です。

```python: exmple
# Unicodeからグリフ名を取得する例
cmap = font_obj.getBestCmap() 
# {3042: 'hiragana_a', 3044: 'hiragana_i', ...} という辞書が返る
# 3042 は 'あ' のUnicode（10進数）
```


## グリフの正体 (glyf または CFF  テーブル)
グリフには大きく分けて2つの種類があります。

* Simple Glyph: 直線や曲線で構成された普通のグリフ。
* Composite Glyph: 他のグリフを組み合わせて作られたグリフ。

`例：「ぱ」＝「は」＋「 ゜」`

内部的には「『は』を座標(x, y)に配置し、さらに『 ゜』を配置する」という参照データだけを持っており、こうすることで統一性の確保、容量の節約になります。

## テーブル構造
### 主要テーブル一覧
|キー名|概要|
|:---|:---|
|head|フォントのバージョン、作成日、全体的なサイズ情報。|
|cmap|文字コードとグリフの対応表。<br>さらに内部にはIDテーブルを持ち、例えばID14の異字体セレクタ(IVS)などが含まれている。|
|glyf|グリフの形状データ（TrueTypeベースの場合）|
|loca|各データの場所を示す情報（TrueType系の場合）|
|CFF |グリフの形状データ（PostScript系の場合：3次ベジェ）<br>**キー名の末尾には半角空白が付くので注意**|
|CFF2|グリフの形状データ（OpenType 1.8以降のPostScriptベースの場合：バリアブル対応）|
|hmtx|各グリフの幅（アドバンス幅）と左サイドベアリング|
|VVAR|垂直方向のバリアブル情報（CFF2テーブルを持っている場合） `HVAR` とペア|
|HVAR|水平方向のバリアブル情報（CFF2テーブルを持っている場合） `VVAR` とペア|
|name|フォント名、著作権情報、ライセンスなどの文字列
|GSUB|合字（f + i → fi のような置換ルール）情報や小型大文字（smcp）や分数（frac）など、機能ごとの切り替えルール|

主要テーブルの一覧は以下で取得できます。

```python: example
table_names = font_obj.keys()
print("テーブル一覧")
print(table_names)
```

フォントが「TrueType系（glyf）」か「PostScript系（CFF/CFF2）」かは、キーの有無を `CFF2`から順に検査すると良いでしょう。

```python: Example
# どのテーブルが存在するかでアウトライン形式を判定
if 'CFF2' in font_obj:
    outline_format = "PostScript (CFF2 / Variable)"
elif 'CFF ' in font_obj:
    outline_format = "PostScript (CFF)"
elif 'glyf' in font_obj:
    outline_format = "TrueType"
else:
    outline_format = "Unknown"

print(f"アウトラインフォーマット: {outline_format}")
```


## スカイリムのフォントとして使用する場合（SWFへのフォント埋め込み）
SWFに持っていく場合、フォントの「多機能さ」が逆にトラブルの元になることがあります。

### 不要テーブルの削除

* **GSUB / GPOS** : 縦書き切り替えやペアカーニング（文字詰め）が不要なら消去。
* **vhea / vmtx** : 縦書き用のメトリクス情報。
* **VORG** : 縦書きの垂直方向の原点情報。
* **BASE** : ベースラインの複雑な位置決め。
* **DSIG** : 署名（容量の無駄）。

### テーブルの簡略化

* **cmap** : Unicode（Format 4 or 12）だけに絞り、Format 14（異体字セレクタ）も削除します。ゲームで「葛」の旧字などを使い分ける必要がなければ、基本字形だけで十分です。

## Tips
ハマったところなど。

### フォントオブジェクトのまま触り続けるのはトラブルの元
拡大縮小やグリフのクリア等を行っていると、フォントオブジェクトの中が荒れていき、いつしか謎のエラーを起こすことがあります。  
中身を変更する処理を行ったら、 `BytesIO` を用いて仮想的にメモリ上にフォントとして書き出し、すぐに読み込むように実装するとトラブルを防止できます。

```python:
def reload_font(font_obj: TTFont) -> TTFont:
    buffer = BytesIO() # メモリ上に保存場所を用意する
    font_obj.save(buffer) # メモリ上に書き出す
    buffer.seek(0) # 保存場所のポインタを先頭にする
    font_obj = TTFont(buffer) # TTFontの形に再インスタンス化する。
    # 再読み込みしたフォントオブジェクトを返す
    # 注意: Pythonからは「全く別のオブジェクト」として見られるため、呼び出し元では必ず戻り値を受け取ること。
    return font_obj
```