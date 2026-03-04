# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from core.font_processor import reopen_font
from utils.file_io import save_font

REMOVE_TARGET_SIZE = 90


def action_remove_black_circles(
    input_path: str, output_path: str, target_size: int, debug: bool = False, **_
):
    with TTFont(input_path) as input_font_obj:
        removed_font_obj = remove_black_circles(input_font_obj, target_size, debug)
        if output_path is not None:
            saved_output_path = save_font(
                removed_font_obj,
                input_path,
                output_path,
                suffix="_black_circles_removed",
            )
            print(f"フォントを保存しました: {saved_output_path}")


def remove_black_circles(
    font_obj: TTFont, target_size: int = REMOVE_TARGET_SIZE, debug: bool = False
) -> TTFont:
    glyf_table = font_obj["glyf"]
    cmap = font_obj.getBestCmap()

    kanji_range = range(0x4E00, 0x9FFF + 1)

    keep_glyphs = {".notdef"}

    for code, name in cmap.items():
        if code not in kanji_range:
            keep_glyphs.add(name)

    glyphs_to_remove = []

    for glyph_name in font_obj.getGlyphOrder():
        if glyph_name in keep_glyphs:
            continue

        if glyph_name not in glyf_table:
            continue

        glyph = glyf_table[glyph_name]

        if glyph.numberOfContours == 1:
            xMin, yMin, xMax, yMax = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
            width = xMax - xMin
            height = yMax - yMin

            aspect_ratio = width / height if height != 0 else 0
            if 0.8 < aspect_ratio < 1.2 and width > target_size:
                glyphs_to_remove.append(glyph_name)

    from fontTools.ttLib.tables._g_l_y_f import Glyph

    for g_name in glyphs_to_remove:
        for code in [k for k, v in cmap.items() if v == g_name]:
            del cmap[code]
        glyf_table[g_name] = Glyph()

    return reopen_font(font_obj)
