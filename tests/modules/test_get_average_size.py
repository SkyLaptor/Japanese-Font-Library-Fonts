import pytest
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph

from modules.get_average_size import get_average_size


def test_get_average_size_basic(create_mock_font):
    # 平均値計算に使用されていない文字(漢字)を含んだTTFフォントを用意
    mock_font = create_mock_font({0x6F22: "漢"})
    glyph = Glyph()
    glyph.xMin, glyph.xMax, glyph.yMin, glyph.yMax = 0, 500, 0, 500
    glyph.numberOfContours = 1
    mock_font['glyf'].glyphs["漢"] = glyph

    result = get_average_size(mock_font)

    # 漢字が計算値にカウントされているか。
    assert result.count == 1
    assert result.avg_w == glyph.xMax
    assert result.avg_h == glyph.yMax


def test_get_average_size_no_kanji(create_mock_font):
    # 平均値計算に使用されていない文字(半角英字)を含んだTTFフォントを用意
    mock_font = create_mock_font({0x0041: "A"})
    glyph = Glyph()
    glyph.xMin, glyph.xMax, glyph.yMin, glyph.yMax = 0, 500, 0, 500
    glyph.numberOfContours = 1
    mock_font['glyf'].glyphs["A"] = glyph

    result = get_average_size(mock_font)

    # 半角英字が計算値にカウントされていないか。
    assert result.count == 0
    assert result.avg_w == 0
    assert result.count_latin == 1
    assert result.avg_w_latin == 500
    assert result.avg_h_latin == 500


def test_get_average_size_excludes_outline_less_glyphs(create_mock_font):
    mock_font = create_mock_font({0x4E00: "kanji_filled", 0x4E01: "kanji_empty"})

    filled = Glyph()
    filled.xMin, filled.xMax, filled.yMin, filled.yMax = 0, 500, 0, 500
    filled.numberOfContours = 1

    empty = Glyph()
    empty.numberOfContours = 0

    mock_font['glyf'].glyphs["kanji_filled"] = filled
    mock_font['glyf'].glyphs["kanji_empty"] = empty

    result = get_average_size(mock_font)

    assert result.count == 1
    assert result.avg_w == 500
    assert result.avg_h == 500


def test_get_average_size_excludes_outline_less_latin_glyphs(create_mock_font):
    mock_font = create_mock_font({0x41: "latin_filled", 0x42: "latin_empty"})

    filled = Glyph()
    filled.xMin, filled.xMax, filled.yMin, filled.yMax = 0, 400, 0, 400
    filled.numberOfContours = 1

    empty = Glyph()
    empty.numberOfContours = 0

    mock_font['glyf'].glyphs["latin_filled"] = filled
    mock_font['glyf'].glyphs["latin_empty"] = empty

    result = get_average_size(mock_font)

    assert result.count == 0
    assert result.count_latin == 1
    assert result.avg_w_latin == 400
    assert result.avg_h_latin == 400


@pytest.mark.parametrize("invalid_outlinetype", ["CFF ", "CFF2"])
def test_get_average_size_outlinetype_error(create_mock_font, invalid_outlinetype):
    mock_font = create_mock_font()
    mock_font[invalid_outlinetype] = newTable(invalid_outlinetype)

    # CFF/CFF2テーブルが存在する場合にエラーを投げるか
    with pytest.raises(ValueError, match="CFF/CFF2には対応していません"):
        get_average_size(mock_font)
