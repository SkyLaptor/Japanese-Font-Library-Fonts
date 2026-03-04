# Dependencies: FFDec=False, FontForge=False
import unicodedata

from fontTools.ttLib import TTFont

from models.average_size_result import AverageSizeResult
from utils.file_io import save_text


def _has_outline(glyph: object) -> bool:
    number_of_contours = getattr(glyph, "numberOfContours", 0)
    if number_of_contours > 0:
        return True

    if number_of_contours < 0:
        components = getattr(glyph, "components", None)
        if components:
            return True

    return False


def _is_cjk_codepoint(codepoint: int) -> bool:
    return 0x4E00 <= codepoint <= 0x9FFF


def _is_latin_codepoint(codepoint: int) -> bool:
    try:
        unicode_name = unicodedata.name(chr(codepoint))
    except ValueError:
        return False

    if "LATIN" not in unicode_name:
        return False

    return chr(codepoint).isalpha()


def action_get_average_size(
    input_path: str, output_path: str, debug: bool = False, **_
):
    with TTFont(input_path) as input_font_obj:
        result = get_average_size(input_font_obj, debug)
        print(result)
        if output_path is not None:
            output_path = save_text(
                str(result),
                input_path,
                output_path,
                "_average_size",
            )
            print(f"平均値計算結果を保存しました: {output_path}")


def get_average_size(font_obj: TTFont, debug: bool = False) -> AverageSizeResult:
    """
    フォント内のグリフの大きさの平均値を計算する。

    平均値は CJK(漢字) と Latin(英字) を並行で計算します。
    いずれの計算もアウトラインを持たないグリフを除外します。
    漢字や英字の範囲に空白が混ざっていると精度が落ちるため、
    この計算を行う前にフォントから余分な空白グリフを清掃しておいてください。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: 計算結果
    :rtype: AverageSizeResult
    """
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    cmap = font_obj.getBestCmap()
    glyf_table = font_obj["glyf"]

    total_width_cjk = 0
    total_height_cjk = 0
    count_cjk = 0

    total_width_latin = 0
    total_height_latin = 0
    count_latin = 0

    for code, name in cmap.items():
        is_cjk = _is_cjk_codepoint(code)
        is_latin = _is_latin_codepoint(code)

        if not (is_cjk or is_latin):
            continue

        if name not in glyf_table:
            continue

        glyph = glyf_table[name]
        if not _has_outline(glyph):
            continue

        w, h = 0, 0
        if all(hasattr(glyph, attr) for attr in ("xMin", "xMax", "yMin", "yMax")):
            w = glyph.xMax - glyph.xMin
            h = glyph.yMax - glyph.yMin
        else:
            continue

        if is_cjk:
            total_width_cjk += w
            total_height_cjk += h
            count_cjk += 1

        if is_latin:
            total_width_latin += w
            total_height_latin += h
            count_latin += 1

    if count_cjk == 0:
        avg_w_cjk, avg_h_cjk = 0, 0
    else:
        avg_w_cjk = total_width_cjk / count_cjk
        avg_h_cjk = total_height_cjk / count_cjk

    if count_latin == 0:
        avg_w_latin, avg_h_latin = 0, 0
    else:
        avg_w_latin = total_width_latin / count_latin
        avg_h_latin = total_height_latin / count_latin

    return AverageSizeResult(
        count=count_cjk,
        avg_w=avg_w_cjk,
        avg_h=avg_h_cjk,
        count_latin=count_latin,
        avg_w_latin=avg_w_latin,
        avg_h_latin=avg_h_latin,
    )
