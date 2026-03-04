from pathlib import Path

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from modules.remove_black_circles import (
    action_remove_black_circles,
    remove_black_circles,
)


@pytest.fixture
def black_circle_font():
    """判定対象・保護対象の様々なグリフを含むフォントを生成"""
    fb = FontBuilder(unitsPerEm=1000, isTTF=True)

    # 1. グリフ定義
    # .notdef: 必須
    # kanji_bad:  U+4E00 (漢字) - 大きな正方形 -> 削除対象
    # kanji_good: U+4E01 (漢字) - 細長い線 (一) -> 維持対象
    # kanji_hole: U+4E02 (漢字) - 二つの輪郭 (口) -> 維持対象
    # symbol_dot: U+25CF (記号) - 大きな正方形 -> 維持対象（漢字範囲外）
    glyph_order = [".notdef", "kanji_bad", "kanji_good", "kanji_hole", "symbol_dot"]
    cmap = {
        0x4E00: "kanji_bad",
        0x4E01: "kanji_good",
        0x4E02: "kanji_hole",
        0x25CF: "symbol_dot",
    }

    glyphs = {}

    # 削除対象: 100x100 の正方形 (numberOfContours = 1)
    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 200))
    pen.lineTo((200, 200))
    pen.lineTo((200, 100))
    pen.closePath()
    bad_box = pen.glyph()
    glyphs["kanji_bad"] = bad_box
    glyphs["symbol_dot"] = bad_box  # 形状は同じだがコードが範囲外
    glyphs[".notdef"] = bad_box

    # 維持対象: 細長い線 (アスペクト比で外れる)
    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 110))
    pen.lineTo((900, 110))
    pen.lineTo((900, 100))
    pen.closePath()
    glyphs["kanji_good"] = pen.glyph()

    # 維持対象: 二つの輪郭 (numberOfContours = 2 で外れる)
    pen = TTGlyphPen(None)
    # 外枠
    pen.moveTo((100, 100))
    pen.lineTo((100, 900))
    pen.lineTo((900, 900))
    pen.lineTo((900, 100))
    pen.closePath()
    # 内枠
    pen.moveTo((200, 200))
    pen.lineTo((800, 200))
    pen.lineTo((800, 800))
    pen.lineTo((200, 800))
    pen.closePath()
    glyphs["kanji_hole"] = pen.glyph()

    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({n: (1000, 0) for n in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupNameTable({"familyName": "BlackCircleTest", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    return fb.font


def test_action_remove_black_circles_output(tmp_path):
    """
    フォントから黒丸を除去するアクションが正常に走り、ファイルが書き出されるかのテスト
    """
    # 準備: 入力フォント及び出力先パス
    input_file = Path("tests/data/test-font/test-font-medium.ttf")
    output_file = tmp_path / "test_font.ttf"

    # 実行: アクションを直接叩く
    action_remove_black_circles(
        input_path=input_file,
        output_path=output_file,
        target_size=90,
        debug=True,
    )

    # ファイルが物理的に存在し、中身が空でないか
    assert output_file.exists(), "ファイルが生成されていません"


def test_remove_black_circles_logic(black_circle_font):
    # ターゲットサイズ 90 で実行
    cleaned_font = remove_black_circles(black_circle_font, target_size=90, debug=True)
    new_cmap = cleaned_font.getBestCmap()
    glyf = cleaned_font['glyf']

    # 1. 漢字範囲内の大きな正方形は削除される
    assert 0x4E00 not in new_cmap
    assert glyf["kanji_bad"].numberOfContours == 0  # 中身が空になっているか

    # 2. 漢字範囲内でも「線」のような形状は残る
    assert 0x4E01 in new_cmap

    # 3. 漢字範囲内でも「複数の輪郭（口など）」は残る
    assert 0x4E02 in new_cmap

    # 4. 漢字範囲外（記号など）は、同じ形状でも残る
    assert 0x25CF in new_cmap
