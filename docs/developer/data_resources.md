# リソース作成ガイド

サブセットテキストや `validNameChars` 等の生成・管理手順です。

## validNameCharsの生成
RaceMenuでキャラクター名に使用可能な文字リストを生成します。JIS第二水準基準で作成します。

```powerShell:
uv run -m src.cui.subset_generator -t jisx0208 -e -o build/validNameChars.txt
```

> [!NOTE]
> `"` が含まれている場合は、 `-e` オプションを付けてエスケープを行う必要があります。

## サブセットテキスト作成

* **日本語フル**

以下のコマンドを実行します。

```powerShell:
uv run -m src.cui.subset_generator -t jp-full -o build/subset_jp_full.txt
```

* **JIS第二水準準拠**

以下のコマンドを実行します。

```powerShell:
uv run -m src.cui.subset_generator -t jisx0208 -o build/subset_jp_jisx0208.txt
```

* **スカイリム準拠**

   * BSA Browserを使用し、`Skyrim\Data\Skyrim - Interface.bsa` から `fonts_ja.swf` または `fonts_jp.swf` を取り出します。
   * FFDecを使用し、取り出したSWFから日本語フォント（Every、Boot、Handwrite）を抽出します。
   * 以下のコマンドを実行します。


```powerShell:
# 1. 取り出した3フォントから空白グリフ(スペース記号などを除く、意図しない空白)を取り除く。
uv run -m src.cui.remove_empty_glyphs -i 取り出したフォント（Every）.ttf -o build/subsets_jp_skyrim/every.ttf
uv run -m src.cui.remove_empty_glyphs -i 取り出したフォント（Book）.ttf -o build/subsets_jp_skyrim/book.ttf
uv run -m src.cui.remove_empty_glyphs -i 取り出したフォント（Handwrite）.ttf -o build/subsets_jp_skyrim/handwrite.ttf

# 2. 空白を取り除いたフォントに対し中に格納されている文字情報を取り出す。
uv run -m src.cui.get_glyphs -i build/subsets_jp_skyrim/every.ttf -o build/subsets_jp_skyrim/every.txt
uv run -m src.cui.get_glyphs -i build/subsets_jp_skyrim/book.ttf -o build/subsets_jp_skyrim/book.txt
uv run -m src.cui.get_glyphs -i build/subsets_jp_skyrim/handwrite.ttf -o build/subsets_jp_skyrim/handwrite.txt

# 3. 【スカイリム日本語版v1.6.1170の場合】
# data/subsets/zenkaku_japanese.txt を build/subsets_jp_skyrim にコピー。

# 4. 文字情報を結合する。
uv run -m src.cui.merge_text -i .\build\subsets_jp_skyrim -o build/subset_jp_skyrim.txt
```

* **スカイリム＋JIS第二基準＋追加**

   * スカイリム準拠のテキストを `build/subset_jp_skyrim_custom/subset_jp_skyrim.txt` にコピーします。作成方法は上記参照。
   * JIS第二基準準拠のテキストを `build/subset_jp_skyrim_custom/subset_jp_jisx0208.txt` にコピーします。作成方法は上記参照。
   * **【オプション】** 追加したい文字列を `build/subset_jp_skyrim_custom/additional.txt` として文字を記載します。
   * 以下のコマンドを実行します。

```powerShell:
uv run -m src.cui.merge_text -i build/subsets_jp_skyrim_custom -o build/subset_jp_skyrim_custom.txt
```