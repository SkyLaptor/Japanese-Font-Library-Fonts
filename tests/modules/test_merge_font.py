from pathlib import Path

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from modules.merge_font import _prepare_interpolation_font_for_merge, action_merge_font


def _build_test_font(
    font_path: Path,
    upm: int,
    glyph_order: list[str],
    cmap: dict[int, str],
    glyphs: dict[str, object],
) -> None:
    fb = FontBuilder(unitsPerEm=upm, isTTF=True)
    fb.setupGlyphOrder(glyph_order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (1000, 0) for name in glyph_order})
    fb.setupHorizontalHeader()
    fb.setupNameTable({"familyName": "Test", "styleName": "Regular"})
    fb.setupOS2()
    fb.setupPost()
    fb.save(str(font_path))


def test_action_merge_font_outputs_file(tmp_path):
    base_path = Path("tests/data/test-font/test-font-medium.ttf")
    interpolation_path = Path("tests/data/test-font/test-font-bold.ttf")
    output_path = tmp_path / "merged.ttf"

    action_merge_font(
        base_path=str(base_path),
        interpolation_path=str(interpolation_path),
        output_path=str(output_path),
    )

    assert output_path.exists()

    with TTFont(str(base_path)) as base_font, TTFont(str(output_path)) as merged_font:
        assert len(merged_font.getGlyphOrder()) >= len(base_font.getGlyphOrder())


def test_action_merge_font_handles_upem_mismatch(tmp_path):
    base_path = Path("tests/data/test-font/test-font-medium.ttf")
    interpolation_path = Path("tests/data/test-font2/test-font2.ttf")
    output_path = tmp_path / "merged_upem_mismatch.ttf"

    action_merge_font(
        base_path=str(base_path),
        interpolation_path=str(interpolation_path),
        output_path=str(output_path),
    )

    assert output_path.exists()


def test_prepare_interpolation_font_removes_empty_and_syncs_upm(tmp_path):
    base_path = tmp_path / "base.ttf"
    sub_path = tmp_path / "sub.ttf"

    base_pen = TTGlyphPen(None)
    base_pen.moveTo((100, 100))
    base_pen.lineTo((100, 900))
    base_pen.lineTo((900, 900))
    base_pen.lineTo((900, 100))
    base_pen.closePath()
    base_a = base_pen.glyph()

    _build_test_font(
        font_path=base_path,
        upm=1000,
        glyph_order=[".notdef", "A"],
        cmap={0x41: "A"},
        glyphs={".notdef": base_a, "A": base_a},
    )

    sub_pen = TTGlyphPen(None)
    sub_pen.moveTo((200, 200))
    sub_pen.lineTo((200, 1800))
    sub_pen.lineTo((1800, 1800))
    sub_pen.lineTo((1800, 200))
    sub_pen.closePath()
    sub_a = sub_pen.glyph()

    empty_pen = TTGlyphPen(None)
    sub_empty = empty_pen.glyph()

    _build_test_font(
        font_path=sub_path,
        upm=2000,
        glyph_order=[".notdef", "A", "B", "empty"],
        cmap={0x41: "A", 0x42: "B", 0x43: "empty"},
        glyphs={".notdef": sub_a, "A": sub_a, "B": sub_a, "empty": sub_empty},
    )

    with TTFont(str(base_path)) as base_font_obj, TTFont(str(sub_path)) as sub_font_obj:
        prepared_font = _prepare_interpolation_font_for_merge(
            base_font_obj=base_font_obj,
            interpolation_font_obj=sub_font_obj,
            remove_empty=True,
        )

    assert prepared_font["head"].unitsPerEm == 1000

    prepared_cmap = prepared_font.getBestCmap()
    assert 0x41 not in prepared_cmap
    assert 0x42 in prepared_cmap
    assert 0x43 not in prepared_cmap

    b_name = prepared_cmap[0x42]
    prepared_glyph = prepared_font["glyf"][b_name]
    prepared_glyph.recalcBounds(prepared_font["glyf"])

    assert prepared_glyph.xMax > 0
    assert prepared_glyph.yMax > 0


def test_prepare_interpolation_font_uses_latin_baseline_when_no_cjk(tmp_path):
    base_path = tmp_path / "base_latin.ttf"
    sub_path = tmp_path / "sub_latin.ttf"

    base_pen = TTGlyphPen(None)
    base_pen.moveTo((0, 0))
    base_pen.lineTo((0, 800))
    base_pen.lineTo((800, 800))
    base_pen.lineTo((800, 0))
    base_pen.closePath()
    base_a = base_pen.glyph()

    sub_pen = TTGlyphPen(None)
    sub_pen.moveTo((0, 0))
    sub_pen.lineTo((0, 1600))
    sub_pen.lineTo((1600, 1600))
    sub_pen.lineTo((1600, 0))
    sub_pen.closePath()
    sub_a = sub_pen.glyph()

    _build_test_font(
        font_path=base_path,
        upm=1000,
        glyph_order=[".notdef", "A"],
        cmap={0x41: "A"},
        glyphs={".notdef": base_a, "A": base_a},
    )

    _build_test_font(
        font_path=sub_path,
        upm=1000,
        glyph_order=[".notdef", "B"],
        cmap={0x42: "B"},
        glyphs={".notdef": sub_a, "B": sub_a},
    )

    with TTFont(str(base_path)) as base_font_obj, TTFont(str(sub_path)) as sub_font_obj:
        prepared_font = _prepare_interpolation_font_for_merge(
            base_font_obj=base_font_obj,
            interpolation_font_obj=sub_font_obj,
        )

    prepared_cmap = prepared_font.getBestCmap()
    b_name = prepared_cmap[0x42]
    prepared_glyph = prepared_font["glyf"][b_name]
    prepared_glyph.recalcBounds(prepared_font["glyf"])

    assert prepared_glyph.xMax == 800
    assert prepared_glyph.yMax == 800


def test_prepare_interpolation_font_drops_overlap_codepoints(tmp_path):
    base_path = tmp_path / "base_overlap.ttf"
    sub_path = tmp_path / "sub_overlap.ttf"

    base_pen = TTGlyphPen(None)
    base_pen.moveTo((0, 0))
    base_pen.lineTo((0, 700))
    base_pen.lineTo((700, 700))
    base_pen.lineTo((700, 0))
    base_pen.closePath()
    base_a = base_pen.glyph()

    sub_pen = TTGlyphPen(None)
    sub_pen.moveTo((0, 0))
    sub_pen.lineTo((0, 1200))
    sub_pen.lineTo((1200, 1200))
    sub_pen.lineTo((1200, 0))
    sub_pen.closePath()
    sub_a = sub_pen.glyph()

    _build_test_font(
        font_path=base_path,
        upm=1000,
        glyph_order=[".notdef", "A"],
        cmap={0x41: "A"},
        glyphs={".notdef": base_a, "A": base_a},
    )

    _build_test_font(
        font_path=sub_path,
        upm=1000,
        glyph_order=[".notdef", "A"],
        cmap={0x41: "A"},
        glyphs={".notdef": sub_a, "A": sub_a},
    )

    with TTFont(str(base_path)) as base_font_obj, TTFont(str(sub_path)) as sub_font_obj:
        prepared_font = _prepare_interpolation_font_for_merge(
            base_font_obj=base_font_obj,
            interpolation_font_obj=sub_font_obj,
        )

    prepared_cmap = prepared_font.getBestCmap()
    assert 0x41 not in prepared_cmap


# TODO: 検証先関数未完成
