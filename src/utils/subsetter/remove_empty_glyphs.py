import argparse
import sys

from fontTools.ttLib import TTFont

from const import BLANK_GLYPHS
from utils.common.generate_subset_jp_full import generate_subset_jp_full
from utils.common.reload_font import reload_font
from utils.common.save_font import save_font
from utils.subsetter.create_subset import create_subset


def main():
    parser = argparse.ArgumentParser(
        description="フォントに含まれるグリフの一覧を取得する"
    )

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントファイルのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="フォントの出力先",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ表示の有効化",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    action_remove_empty_glyphs(**vars(args))


def action_remove_empty_glyphs(
    input_path: str, output_path: str, debug: bool = False, **_
):
    font_obj = TTFont(input_path)
    font_obj = remove_empty_glyphs(font_obj, debug)
    if output_path is not None:
        saved_output_path = save_font(
            font_obj,
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
    # CFF/CFF2の場合は非対応
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    glyf = font_obj['glyf']
    cmap = font_obj.getBestCmap()
    deleted_glyphs = []

    for code, name in cmap.items():
        if code in BLANK_GLYPHS:
            continue

        glyph = glyf[name]

        # numberOfContours:
        # > 0: 単純グリフ（中身あり）
        #   0: 単純グリフ（空っぽ） -> これを削除！
        #  -1: 複合グリフ（他を参照） -> 削除を避ける
        if glyph.numberOfContours == 0:
            deleted_glyphs.append(code)

    # cmapから削除（これでフォント的に「持っていない文字」になる）
    for code in deleted_glyphs:
        del cmap[code]
        # dprint(f"グリフをcmapから削除: U+{code:04X}", debug)

    # このままでは実体が残りっぱなしになりますが、
    # JIS第四基準+αまで網羅したサブセットを行うことで、実質的にGIDを整理した綺麗なフォントになります。
    gid_cleaned_font_obj = create_subset(font_obj, generate_subset_jp_full(), debug)

    return reload_font(gid_cleaned_font_obj)
