# Dependencies: FFDec=False, FontForge=False

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

from const import EXCLUDE_CHARS
from core.font_processor import reopen_font
from utils.file_io import load_text, save_font


def action_create_subset(
    input_path: str,
    output_path: str,
    subset_path: str,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        subsetted_input_font_obj = create_subset(
            input_font_obj, load_text(subset_path, EXCLUDE_CHARS), debug
        )
        if output_path is not None:
            saved_output_path = save_font(
                subsetted_input_font_obj, input_path, output_path, "_subsetted"
            )
            print(f"フォントを保存しました: {saved_output_path}")


def create_subset(font_obj: TTFont, subset_text: str, debug: bool = False) -> TTFont:
    """
    サブセットフォントを作成する

    サブセッターによりタグ情報の一部書き換えが発生するため、
    もしタグ情報の編集を行うのであればサブセット後に実施するようにして下さい。

    :param font_obj: フォント
    :type font_obj: TTFont
    :param subset_text: サブセット文字列
    :type subset_text: str
    :return: サブセットフォント
    :rtype: TTFont
    """
    options = Options()
    options.notdef_glyph = True
    options.notdef_outline = True
    options.retain_gids = False
    options.legacy_kern = True
    options.name_IDs = ['*']
    options.name_languages = ['*']
    options.hinting = True
    options.layout_features = ['*']
    options.recalc_timestamp = False

    subsetter = Subsetter(options=options)
    subsetter.populate(text=subset_text)
    subsetter.subset(font=font_obj)

    return reopen_font(font_obj)
