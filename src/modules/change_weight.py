# Dependencies: FFDec=False, FontForge=False
import math

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import Path

from core.font_loader import reopen_font
from utils.dprint import dprint
from utils.file_io import save_font


def action_change_weight(
    input_path: str,
    output_path: str,
    offset_weight: int,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        weight_changed_font_obj = change_weight(input_font_obj, offset_weight, debug)
        print(f"文字の太さを変更しました: 変更量: {offset_weight}")
        if output_path is not None:
            saved_output_path = save_font(
                weight_changed_font_obj,
                input_path,
                output_path,
                "_weight_changed",
            )
            print(f"太さを変更したフォントを保存しました: {saved_output_path}")


def change_weight(
    font_obj: TTFont, offset_weight: int = 0, debug: bool = False
) -> TTFont:
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    if offset_weight == 0:
        return reopen_font(font_obj)

    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()
    actual_offset = -offset_weight

    def get_normal(dx, dy):
        length = math.sqrt(dx * dx + dy * dy)
        return (dy / length, -dx / length) if length != 0 else (0, 0)

    for name in glyph_names:
        temp_pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(temp_pen)
        temp_glyph = temp_pen.glyph()

        if temp_glyph.numberOfContours <= 0:
            continue

        coords = list(temp_glyph.coordinates)
        new_coords = list(coords)
        start_idx = 0
        for end_idx in temp_glyph.endPtsOfContours:
            contour_indices = list(range(start_idx, end_idx + 1))
            n = len(contour_indices)
            if n >= 2:
                for i in range(n):
                    curr_idx = contour_indices[i]
                    prev_idx = contour_indices[(i - 1) % n]
                    next_idx = contour_indices[(i + 1) % n]
                    x0, y0 = coords[prev_idx]
                    x1, y1 = coords[curr_idx]
                    x2, y2 = coords[next_idx]
                    v1x, v1y = x1 - x0, y1 - y0
                    v2x, v2y = x2 - x1, y2 - y1
                    n1x, n1y = get_normal(v1x, v1y)
                    n2x, n2y = get_normal(v2x, v2y)
                    nx, ny = n1x + n2x, n1y + n2y
                    n_len = math.sqrt(nx * nx + ny * ny)
                    if n_len != 0:
                        new_coords[curr_idx] = (
                            round(x1 + (nx / n_len) * actual_offset, 2),
                            round(y1 + (ny / n_len) * actual_offset, 2),
                        )
            start_idx = end_idx + 1

        temp_glyph.coordinates = type(temp_glyph.coordinates)(new_coords)

        rec_pen = RecordingPen()
        temp_glyph.draw(rec_pen, font_obj['glyf'])

        path = Path()
        pen = path.getPen()
        rec_pen.replay(pen)

        try:
            path.simplify()
        except Exception as e:
            dprint(e, debug)
            dprint(f"グリフ '{name}' の簡略化に失敗したためスキップします。", debug)

        tt_pen = TTGlyphPen(glyph_set)
        path.draw(tt_pen)
        font_obj['glyf'].glyphs[name] = tt_pen.glyph()

    return reopen_font(font_obj)
