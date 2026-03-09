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
uv run -m src.cui.subset_generator -t jp-full -o data/subsets/subset_jp_full.txt
```

* **JIS第二水準準拠**

以下のコマンドを実行します。

```powerShell:
uv run -m src.cui.subset_generator -t jisx0208 -o data/subsets/subset_jp_jisx0208.txt
```

* **スカイリム準拠**

   * [**利用者向けREADME.md**](/docs/user/README.md) の **【オプション】基準フォントの準備（ゲームデフォルトの日本語フォント）** を参考にゲームフォントを取り出します。


```powerShell:
# 2. 空白を取り除いたフォントに対し中に格納されている文字情報を取り出す。
uv run -m src.cui.get_glyphs -i contents/skyrim/1_Skyrim_JP_EveryFont_0805.ttf -o build/subsets_jp_skyrim/every.txt
uv run -m src.cui.get_glyphs -i contents/skyrim/22_Skyrim_JP_BookFont_0805.ttf -o build/subsets_jp_skyrim/book.txt
uv run -m src.cui.get_glyphs -i contents/skyrim/5_Skyrim_JP_HandWriteFont_0805.ttf -o build/subsets_jp_skyrim/handwrite.txt

# 3. 【スカイリム日本語版v1.6.1170の場合】
# data/subsets/zenkaku_japanese.txt を build/subsets_jp_skyrim にコピー。

# 4. 文字情報を結合する。
uv run -m src.cui.merge_text -i build/subsets_jp_skyrim -o data/subsets/subset_jp_skyrim.txt
```

* **スカイリム＋JIS第二基準＋追加**

   * `data/subsets/subset_jp_skyrim.txt`を `build/subset_jp_skyrim_custom` にコピーします。作成方法は上記参照。
   * `data/subsets/subset_jp_jisx0208.txt`を `build/subset_jp_skyrim_custom` にコピーします。作成方法は上記参照。
   * **【オプション】** 追加したい文字列を `build/subset_jp_skyrim_custom/additional.txt` として文字を記載します。
   * 以下のコマンドを実行します。

```powerShell:
uv run -m src.cui.merge_text -i build/subset_jp_skyrim_custom -o data/subsets/subset_jp_skyrim_custom.txt
```