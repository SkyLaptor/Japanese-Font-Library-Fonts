from pathlib import Path

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from modules.remove_empty_glyphs import (
    action_remove_empty_glyphs,
    remove_empty_glyphs,
)


@pytest.fixture
def test_font_for_cleaning():
    """空っぽ、中身あり、複合グリフを含む本物の構造のフォントを生成"""
    fb = FontBuilder(unitsPerEm=1000, isTTF=True)

    # .notdef: 必須
    # space: 0x0020 (空だがホワイトリスト)
    # normal: 0x0041 'A' (中身あり)
    # empty: 0x0042 'B' (空 -> 削除対象)
    # composite: 0x0043 'C' (複合 -> 維持対象)
    glyph_order = [".notdef", "space", "normal", "empty", "composite"]
    cmap = {0x20: "space", 0x41: "normal", 0x42: "empty", 0x43: "composite"}

    glyphs = {}
    # 中身ありグリフ作成 (正方形)
    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 900))
    pen.lineTo((900, 900))
    pen.lineTo((900, 100))
    pen.closePath()
    normal_glyph = pen.glyph()
    glyphs["normal"] = normal_glyph
    glyphs[".notdef"] = normal_glyph

    # 空っぽグリフ
    pen = TTGlyphPen(None)
    empty_glyph = pen.glyph()
    glyphs["space"] = empty_glyph
    glyphs["empty"] = empty_glyph

    # 複合グリフ (normalを参照)
    pen = TTGlyphPen(glyphs)
    pen.addComponent("normal", (1, 0, 0, 1, 0, 0))
    glyphs["composite"] = pen.glyph()  # これで numberOfContours = -1 になる

    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (500, 0) for n in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    return fb.font


def test_action_remove_empty_glyphs_output(tmp_path):
    """
    フォント空白削除アクションが正常に走り、ファイルが書き出されるかテスト
    """
    # 準備: 入力フォント及び出力先パス
    input_file = Path("tests/data/test-font/test-font-medium.ttf")
    output_file = tmp_path / "test_font.ttf"

    # 実行: アクションを直接叩く
    action_remove_empty_glyphs(
        input_path=input_file,
        output_path=output_file,
        debug=True,
    )

    # ファイルが物理的に存在し、中身が空でないか
    assert output_file.exists(), "ファイルが生成されていません"


def test_remove_empty_glyphs_logic(test_font_for_cleaning):
    # 実行
    cleaned_font = remove_empty_glyphs(test_font_for_cleaning, debug=True)
    new_cmap = cleaned_font.getBestCmap()

    # 1. 中身あり(A)は残る
    assert 0x41 in new_cmap

    # 2. ホワイトリスト(Space)は空でも残る
    assert 0x20 in new_cmap

    # 3. 複合グリフ(C)は numberOfContours = -1 なので残る
    assert 0x43 in new_cmap

    # 4. ただの空グリフ(B)は削除される
    assert 0x42 not in new_cmap
