# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from const import BASE_LINE_TARGET
from utils.dprint import dprint
from utils.file_io import save_text


def action_get_offset_to_align_bottom(
    input_path: str,
    output_path: str,
    base_line: int = 0,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        offset = get_offset_to_align_bottom(input_font_obj, base_line, debug)
        print(f"ベースライン: {base_line}, オフセット値: {offset}")
        if output_path is not None:
            output_path = save_text(
                str(offset), input_path, output_path, "_bottom_offset"
            )
            print(f"オフセット値を保存しました: {output_path}")


def get_offset_to_align_bottom(
    font_obj: TTFont, base_line: int = BASE_LINE_TARGET, debug: bool = False
) -> int:
    if "CFF " in font_obj or "CFF2" in font_obj:
        raise ValueError("CFF/CFF2には対応していません。")

    cmap = font_obj.getBestCmap()
    glyf_table = font_obj["glyf"]

    total_y_min = 0
    count = 0

    for code, name in cmap.items():
        if not (0x4E00 <= code <= 0x9FFF):
            continue

        if name not in glyf_table:
            continue

        glyph = glyf_table[name]

        if hasattr(glyph, "yMin"):
            total_y_min += glyph.yMin
            count += 1

    if count == 0:
        return 0

    avg_y_min = total_y_min / count
    dprint(f"検査対象フォントの 底面平均値: {avg_y_min:.1f}", debug)

    offset = base_line - avg_y_min

    return round(offset)
