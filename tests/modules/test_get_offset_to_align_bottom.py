from pathlib import Path

from fontTools.ttLib.tables._g_l_y_f import Glyph

from modules.get_offset_to_align_bottom import (
    action_get_offset_to_align_bottom,
    get_offset_to_align_bottom,
)


def test_action_get_offset_to_align_bottom_output(tmp_path):
    input_path = Path("tests/data/test-font/test-font-medium.ttf")
    output_path = tmp_path / "test.txt"
    action_get_offset_to_align_bottom(
        input_path=input_path, output_path=output_path, base_line=0, debug=True
    )

    assert output_path.exists(), "ファイルが生成されていません"

    content = output_path.read_text(encoding="utf-8")
    assert len(content) > 0, "生成されたファイルが空です"


def test_get_offset_to_align_bottom_basic(create_mock_font):
    mock_font = create_mock_font({0x4E00: "一", 0x4E01: "丁"})
    glyph1 = Glyph()
    glyph1.xMin, glyph1.xMax, glyph1.yMin, glyph1.yMax = 0, 500, -100, 800
    glyph1.numberOfContours = 1
    mock_font["glyf"].glyphs["一"] = glyph1
    glyph2 = Glyph()
    glyph2.xMin, glyph2.xMax, glyph2.yMin, glyph2.yMax = 0, 500, -200, 800
    glyph2.numberOfContours = 1
    mock_font["glyf"].glyphs["丁"] = glyph2

    offset = get_offset_to_align_bottom(mock_font, base_line=0)
    assert offset == 150.0


def test_get_offset_to_align_bottom_with_base_line(create_mock_font):
    mock_font = create_mock_font({0x4E00: "一"})
    glyph1 = Glyph()
    glyph1.xMin, glyph1.xMax, glyph1.yMin, glyph1.yMax = 0, 500, -100, 800
    glyph1.numberOfContours = 1
    mock_font["glyf"].glyphs["一"] = glyph1

    offset = get_offset_to_align_bottom(mock_font, base_line=-50)
    assert offset == 50.0


def test_get_offset_to_align_bottom_exclude_non_kanji(create_mock_font):
    mock_font = create_mock_font({0x0041: "A", 0x4E00: "一"})
    glyph1 = Glyph()
    glyph1.xMin, glyph1.xMax, glyph1.yMin, glyph1.yMax = 0, 500, -500, 800
    glyph1.numberOfContours = 1
    mock_font["glyf"].glyphs["A"] = glyph1
    glyph2 = Glyph()
    glyph2.xMin, glyph2.xMax, glyph2.yMin, glyph2.yMax = 0, 500, -100, 800
    glyph2.numberOfContours = 1
    mock_font["glyf"].glyphs["一"] = glyph2

    offset = get_offset_to_align_bottom(mock_font, base_line=0)
    assert offset == 100.0
