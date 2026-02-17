import pytest
from fontTools.ttLib import newTable

from tests.utilstest import MockGlyph
from utils.inspector.get_average_size import get_average_size


def test_get_average_size_basic(create_mock_font):
    # 平均値計算に使用されていない文字(漢字)を含んだTTFフォントを用意
    mock_font = create_mock_font({0x4E00: "kanji1"})
    mock_font['glyf'].glyphs["kanji1"] = MockGlyph(0, 500, 0, 500)

    result = get_average_size(mock_font)

    # 漢字が計算値にカウントされているか。
    assert result.count == 1
    assert result.avg_w == 500
    assert result.avg_h == 500


def test_get_average_size_no_kanji(create_mock_font):
    # 平均値計算に使用されていない文字(半角英字)を含んだTTFフォントを用意
    mock_font = create_mock_font({0x0041: "A"})
    mock_font['glyf'].glyphs["A"] = MockGlyph(0, 500, 0, 500)

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
