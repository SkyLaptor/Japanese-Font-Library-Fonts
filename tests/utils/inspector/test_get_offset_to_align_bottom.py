from tests.utilstest import MockGlyph
from utils.inspector.get_offset_to_align_bottom import get_offset_to_align_bottom


def test_get_offset_to_align_bottom_basic(create_mock_font):
    """2つの漢字の平均yMinからオフセットが正しく計算されるか"""
    # 0x4E00 (一) : yMin = -100
    # 0x4E01 (丁) : yMin = -200
    # 平均 yMin = -150.0
    mapping = {0x4E00: "一", 0x4E01: "丁"}
    font = create_mock_font(mapping)

    # 引数順: xmin, xmax, ymin, ymax
    font['glyf'].glyphs["一"] = MockGlyph(0, 500, -100, 800)
    font['glyf'].glyphs["丁"] = MockGlyph(0, 500, -200, 800)

    # 0 - (-150.0) = 150.0
    offset = get_offset_to_align_bottom(font, base_line=0)
    assert offset == 150.0


def test_get_offset_to_align_bottom_with_base_line(create_mock_font):
    """base_line を指定した時に差分が正しく計算されるか"""
    mapping = {0x4E00: "一"}
    font = create_mock_font(mapping)
    font['glyf'].glyphs["一"] = MockGlyph(0, 500, -100, 800)

    # -50 - (-100.0) = 50.0
    offset = get_offset_to_align_bottom(font, base_line=-50)
    assert offset == 50.0


def test_get_offset_to_align_bottom_exclude_non_kanji(create_mock_font):
    """漢字以外の文字が除外されているか"""
    # A(-500) は範囲外なので無視されるべき
    mapping = {0x0041: "A", 0x4E00: "一"}
    font = create_mock_font(mapping)
    font['glyf'].glyphs["A"] = MockGlyph(0, 500, -500, 800)
    font['glyf'].glyphs["一"] = MockGlyph(0, 500, -100, 800)

    # 平均 yMin = -100.0 -> offset = 100.0
    offset = get_offset_to_align_bottom(font, base_line=0)
    assert offset == 100.0
