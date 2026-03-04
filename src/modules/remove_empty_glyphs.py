# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from const import BLANK_GLYPHS
from core.font_processor import reopen_font
from modules.create_subset import create_subset
from modules.subset_generator import generate_subset_jp_full
from utils.file_io import save_font


def action_remove_empty_glyphs(
    input_path: str, output_path: str, debug: bool = False, **_
):
    with TTFont(input_path) as input_font_obj:
        input_font_obj = remove_empty_glyphs(input_font_obj, debug)
        if output_path is not None:
            saved_output_path = save_font(
                input_font_obj,
                input_path,
                output_path,
                suffix="_emptyglyphs_removed",
            )
            print(f"フォントを保存しました: {saved_output_path}")


def remove_empty_glyphs(font_obj: TTFont, debug: bool = False) -> TTFont:
    """
    アウトラインを持たないグリフをcmapから削除する

    実質的なアウトラインを持たないグリフをcmapから削除することで、
    ゲーム内で豆腐(.notdef)が表示されるようにします。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: クリーニング済みフォントオブジェクト
    :rtype: TTFont
    """
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    glyf = font_obj['glyf']
    cmap = font_obj.getBestCmap()
    deleted_glyphs = []

    for code, name in cmap.items():
        if code in BLANK_GLYPHS:
            continue

        glyph = glyf[name]

        if glyph.numberOfContours == 0:
            deleted_glyphs.append(code)

    for code in deleted_glyphs:
        del cmap[code]

    gid_cleaned_font_obj = create_subset(font_obj, generate_subset_jp_full(), debug)

    return reopen_font(gid_cleaned_font_obj)
