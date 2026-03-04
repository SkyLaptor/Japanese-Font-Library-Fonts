# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from const import EXCLUDE_CHARS
from modules.get_glyphs import get_glyphs
from utils.file_io import load_text, save_text


def action_validate_subset(
    input_path: str,
    output_path: str,
    subset_path: str,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        subset_text = load_text(subset_path, EXCLUDE_CHARS)
        missing_glyphs = validate_subset(input_font_obj, subset_text, debug)
        missing_glyphs_count = len(missing_glyphs)
        print(f"サブセットにあってフォントに無い文字数: {missing_glyphs_count}")
        if output_path is not None:
            saved_output_path = save_text(
                missing_glyphs,
                input_path,
                output_path,
                suffix="_missing_glyphs",
            )
            print(
                f"サブセットにあってフォントに無い文字を出力しました: {saved_output_path}"
            )


def validate_subset(font_obj: TTFont, subset_text: str, debug: bool = False) -> str:
    missing_chars = set(subset_text) - set(get_glyphs(font_obj))
    missing_chars_sorted = sorted(list(missing_chars))
    missing_str_sorted = "".join(missing_chars_sorted)

    return missing_str_sorted
