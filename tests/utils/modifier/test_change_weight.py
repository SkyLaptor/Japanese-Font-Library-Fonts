import pytest
from fontTools.pens.ttGlyphPen import TTGlyphPen

from src.utils.modifier.change_weight import change_weight


def test_change_weight_grow(create_mock_font):
    # 新しく作るのではなく、最初からある .notdef を正方形にする
    font = create_mock_font()

    glyph_set = font.getGlyphSet()
    pen = TTGlyphPen(glyph_set)
    pen.moveTo((100, 100))
    pen.lineTo((100, 200))
    pen.lineTo((200, 200))
    pen.lineTo((200, 100))
    pen.closePath()

    # 既存の .notdef を置き換える（これなら整合性が崩れない）
    font['glyf'].glyphs['.notdef'] = pen.glyph()

    # 境界計算
    orig_glyph = font['glyf']['.notdef']
    orig_glyph.recalcBounds(font['glyf'])
    orig_xMin, orig_yMin = orig_glyph.xMin, orig_glyph.yMin

    # 実行
    weighted_font = change_weight(font, offset_weight=20)

    # 検証（.notdef を見る）
    weighted_glyph = weighted_font['glyf']['.notdef']
    assert weighted_glyph.xMin < orig_xMin


def test_change_weight_cff_error(create_mock_font):
    """CFF形式の場合にちゃんと ValueError を投げるか"""
    font = create_mock_font()
    font['CFF '] = "dummy"  # CFFテーブルを偽装

    with pytest.raises(ValueError, match="この関数はCFF/CFF2には対応していません。"):
        change_weight(font, offset_weight=10)
