from pathlib import Path

from fontTools.fontBuilder import FontBuilder


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
