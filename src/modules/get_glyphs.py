# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from utils.file_io import save_text


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

    cmap = font_obj.getBestCmap()

    valid_chars = []
    for code in sorted(cmap.keys()):
        char = chr(code)
        valid_chars.append(char)

    glyph_text = "".join(valid_chars)

    return glyph_text
