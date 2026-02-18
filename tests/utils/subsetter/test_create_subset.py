from pathlib import Path

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from utils.subsetter.create_subset import action_create_subset, create_subset


@pytest.fixture
def real_minimal_font():
    """サブセッターが壊れない程度の最小限の構造を持つ本物のフォントを生成"""
    fb = FontBuilder(unitsPerEm=1000, isTTF=True)

    # 1. グリフ名とUnicodeの定義
    glyph_order = [".notdef", "A", "uni3042"]  # uni3042 = 'あ'
    cmap = {0x41: "A", 0x3042: "uni3042"}

    # 2. 空のグリフデータを作成
    glyphs = {}
    for name in glyph_order:
        pen = TTGlyphPen(None)  # glyphSetをNoneに
        # 正しくは pen.glyph() ですが、空なら直接オブジェクト生成でもOK
        # 今回はより確実な方法で空グリフを指定します
        glyphs[name] = pen.glyph()

    # 3. 各種テーブルのセットアップ
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (500, 0) for name in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupNameTable({"familyName": "TestFont", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()

    return fb.font


def test_action_create_subset_output(tmp_path):
    """
    フォントサブセット化アクションが正常に走り、ファイルが書き出されるかテスト
    """
    # 準備: 入力フォント及び出力先パス
    input_path = Path("tests/data/test-font/test-font-medium.ttf")
    output_path = tmp_path / "test_font.ttf"
    subset_path = Path("data/subsets/skyrim/subset_jp_test.txt")

    # 実行: アクションを直接叩く
    action_create_subset(
        input_path=input_path,
        output_path=output_path,
        subset_path=subset_path,
        debug=True,
    )

    # ファイルが物理的に存在し、中身が空でないか
    assert output_path.exists(), "ファイルが生成されていません"


def test_create_subset_functionality(real_minimal_font):
    # 'A' だけを残すサブセット
    subset_text = "A"
    # サブセッターに渡す（内部で reload_font されるので新しいオブジェクトが返る）
    subset_font = create_subset(real_minimal_font, subset_text)

    new_cmap = subset_font.getBestCmap()
    assert 0x41 in new_cmap  # 'A' は残っている
    assert 0x3042 not in new_cmap  # 'あ' は消えている
    assert ".notdef" in subset_font.getGlyphOrder()


def test_create_subset_empty_text(real_minimal_font):
    # 空文字を渡しても .notdef さえあればフォントとして壊れない
    subset_font = create_subset(real_minimal_font, "")
    assert ".notdef" in subset_font.getGlyphOrder()
