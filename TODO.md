# することリスト
Issueに上げるほどのものでもないTODO。

* [ ] 各スクリプトはTTF専用にする。
  * `README.md` にTTFは使わないでと書いてるしね。

* [ ] `utils.inspector.py` を単体事項可能にする。
  * [ ] `get_info()` をもうちょっと何とかする。
* [X] `utils.modifier.py` を単体事項可能にする。

* [ ] 全般的にいらない関数消去。
  * [ ] 特に `utils.__init__.py` がゴミだらけかも。

* [ ] ベースバニラフォントを最新の関数で処理し、`/data/skyrim/` にアップする。
  * 空白除去 `optimizer.remove_empty_glyphs`
  * 格納文字列取得 `inspector.get_glyphs`

* [ ] ベースバニラフォントの名前から `empty_removed` を消す。

* [ ] `convert_for_skyrim.py` を修正する。