import pytest
from fontTools.ttLib import newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph

from utils.inspector.get_average_size import get_average_size


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


@pytest.mark.parametrize("invalid_outlinetype", ["CFF ", "CFF2"])
def test_get_average_size_outlinetype_error(create_mock_font, invalid_outlinetype):
    mock_font = create_mock_font()
    mock_font[invalid_outlinetype] = newTable(invalid_outlinetype)

    # CFF/CFF2テーブルが存在する場合にエラーを投げるか
    with pytest.raises(ValueError, match="CFF/CFF2には対応していません"):
        get_average_size(mock_font)
