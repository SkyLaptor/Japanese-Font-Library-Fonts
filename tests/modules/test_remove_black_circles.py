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
    fb = FontBuilder(unitsPerEm=1000, isTTF=True)

    glyph_order = [".notdef", "kanji_bad", "kanji_good", "kanji_hole", "symbol_dot"]
    cmap = {
        0x4E00: "kanji_bad",
        0x4E01: "kanji_good",
        0x4E02: "kanji_hole",
        0x25CF: "symbol_dot",
    }

    glyphs = {}

    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 200))
    pen.lineTo((200, 200))
    pen.lineTo((200, 100))
    pen.closePath()
    bad_box = pen.glyph()
    glyphs["kanji_bad"] = bad_box
    glyphs["symbol_dot"] = bad_box
    glyphs[".notdef"] = bad_box

    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 110))
    pen.lineTo((900, 110))
    pen.lineTo((900, 100))
    pen.closePath()
    glyphs["kanji_good"] = pen.glyph()

    pen = TTGlyphPen(None)
    pen.moveTo((100, 100))
    pen.lineTo((100, 900))
    pen.lineTo((900, 900))
    pen.lineTo((900, 100))
    pen.closePath()
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
    input_file = Path("tests/data/test-font/test-font-medium.ttf")
    output_file = tmp_path / "test_font.ttf"

    action_remove_black_circles(
        input_path=input_file,
        output_path=output_file,
        target_size=90,
        debug=True,
    )

    assert output_file.exists(), "ファイルが生成されていません"


def test_remove_black_circles_logic(black_circle_font):
    cleaned_font = remove_black_circles(black_circle_font, target_size=90, debug=True)
    new_cmap = cleaned_font.getBestCmap()
    glyf = cleaned_font["glyf"]

    assert 0x4E00 not in new_cmap
    assert glyf["kanji_bad"].numberOfContours == 0

    assert 0x4E01 in new_cmap

    assert 0x4E02 in new_cmap

    assert 0x25CF in new_cmap
