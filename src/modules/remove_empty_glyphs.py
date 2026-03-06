# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from const import BLANK_GLYPHS
from core.font_loader import reopen_font
from modules.create_subset import create_subset
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
    if "CFF " in font_obj or "CFF2" in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    glyf = font_obj["glyf"]
    cmap = font_obj.getBestCmap()
    deleted_glyphs = []

    for code, name in cmap.items():
        if code in BLANK_GLYPHS:
            continue

        if name not in glyf:
            deleted_glyphs.append(code)
            continue

        glyph = glyf[name]

        # 輪郭もコンポーネントも持たないグリフを空と判定
        number_of_contours = getattr(glyph, "numberOfContours", 0)
        has_outline = number_of_contours > 0 or (
            number_of_contours < 0 and bool(getattr(glyph, "components", None))
        )
        if not has_outline:
            deleted_glyphs.append(code)

    if debug:
        print(f"[remove_empty_glyphs] 削除対象の空グリフ数: {len(deleted_glyphs)}")

    for code in deleted_glyphs:
        if code in cmap:
            del cmap[code]

    # 現在の全文字を維持しつつ、GIDを詰め直すためにサブセット作成を呼び出す
    all_chars = "".join(chr(cp) for cp in cmap.keys())
    gid_cleaned_font_obj = create_subset(font_obj, all_chars, debug)

    return reopen_font(gid_cleaned_font_obj)
