import argparse
import sys

from fontTools.ttLib import TTFont

from const import EXCLUDE_CHARS
from utils.common.load_text import load_text
from utils.common.save_text import save_text
from utils.inspector.get_glyphs import get_glyphs


def main():
    parser = argparse.ArgumentParser(
        description="サブセット文字列とフォントに格納されている文字を比較検証する"
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
        help="比較結果の書き出し先",
    )
    parser.add_argument(
        "-s",
        "--subset_path",
        type=str,
        help="サブセットファイルのパス",
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

    action_validate_subset(**vars(args))


def action_validate_subset(
    input_path: str,
    output_path: str,
    subset_path: str,
    debug: bool = False,
    **_,
):
    font_obj = TTFont(input_path)
    subset_text = load_text(subset_path, EXCLUDE_CHARS)
    missing_glyphs = validate_subset(font_obj, subset_text, debug)
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
    """
    サブセット文字列とフォントに格納されている文字を比較検証する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param subset_text: サブセットテキスト
    :type subset_text: str
    :param debug: デバッグモード
    :type debug: bool
    :return: サブセットにあってフォントに無い文字
    :rtype: str
    """
    # 差分を抽出： サブセット文字 にあって フォント内グリフ にないもの
    missing_chars = set(subset_text) - set(get_glyphs(font_obj))
    # ソートして表示（何が足りないか見やすくする）
    missing_chars_sorted = sorted(list(missing_chars))
    # リストを一つの文字列に結合
    missing_str_sorted = "".join(missing_chars_sorted)

    return missing_str_sorted


if __name__ == "__main__":
    main()
