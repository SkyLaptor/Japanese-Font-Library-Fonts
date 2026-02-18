import argparse
import sys

from fontTools.ttLib import TTFont

from utils.common.save_text import save_text


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
        help="グリフ一覧の書き出し先",
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

    action_get_glyphs(**vars(args))


def action_get_glyphs(
    input_path: str,
    output_path: str,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        glyphs = get_glyphs(input_font_obj, debug)
        print(f"文字数: {len(glyphs)}")
        if output_path is not None:
            saved_output_path = save_text(glyphs, input_path, output_path, "_glyphs")
            print(f"フォントに含まれる文字を保存しました: {saved_output_path}")


def get_glyphs(font_obj: TTFont, debug: bool = False) -> str:
    """
    フォントに含まれるグリフの一覧を取得する

    不正な空白グリフであっても有効として取得されます。
    必要に応じて不正な空白グリフは事前に消してから使用して下さい。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: グリフ一覧
    :rtype: str
    """

    # cmap（文字コードとグリフ名の対応表）を取得
    cmap = font_obj.getBestCmap()

    # Unicode値(int)から文字(str)に変換
    # cmapのキーはUnicode値(整数)
    valid_chars = []
    for code in sorted(cmap.keys()):
        char = chr(code)
        valid_chars.append(char)

    # 文字列に変換
    glyph_text = "".join(valid_chars)

    return glyph_text


if __name__ == "__main__":
    main()
