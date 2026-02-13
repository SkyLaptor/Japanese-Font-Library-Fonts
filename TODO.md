# することリスト
Issueに上げるほどのものでもないTODO。

* [X] debugオプションとか付けられない？

* [X] 各スクリプトはTTF専用にする。
  * `README.md` にTTFは使わないでと書いてるしね。
  * [X] inspector.py
  * [X] modifier.py
  * [X] optimizer.py
  * [X] reconstructor.py

* [X] `utils.inspector.py` を単体事項可能にする。
  * [ ] `get_info()` をもうちょっと何とかする？
* [X] `utils.modifier.py` を単体事項可能にする。

* [X] 全般的にいらない関数消去。
  * [X] 特に `utils.__init__.py` がゴミだらけかも。

* [X] ベースバニラフォントを最新の関数で処理し、`/data/skyrim/` にアップする。
  * 空白除去 `optimizer.remove_empty_glyphs`
  * 格納文字列取得 `inspector.get_glyphs`
  * スカイリムサブセット作成: `common.merge_text`

* [X] ベースバニラフォントの名前から `empty_removed` を消す。

* [X] font_tools 不要

* [ ] フォントコレクションを分解するツール→common.pyに実装する？

* [X] `convert_for_skyrim.py` を修正する。