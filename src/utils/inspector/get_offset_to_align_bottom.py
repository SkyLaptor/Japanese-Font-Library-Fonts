import argparse
import sys

from fontTools.ttLib import TTFont

from utils.common.dprint import dprint
from utils.common.save_text import save_text


def main():
    parser = argparse.ArgumentParser(
        description="フォント内のグリフの底面位置が基準値からどれだけ異なるか計算する"
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
        help="オフセット値の書き出し先",
    )
    parser.add_argument(
        "-b",
        "--base_line",
        type=int,
        default=0,
        help="基準となるY座標 デフォルト:0",
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

    action_get_offset_to_align_bottom(**vars(args))


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
    font_obj: TTFont, base_line: int, debug: bool = False
) -> int:
    """
    フォント内のグリフの底面位置が基準値からどれだけ異なるか計算する

    平均値の対象となるグリフはその位置の均一性から一般的な漢字の範囲に限定しています。
    漢字の範囲に空白が混ざっていると精度が落ちるため、
    この計算を行う前にフォントから余分な空白グリフを清掃しておいてください。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param base_under: 基準となるY座標
    :type base_under: int
    :return: オフセット値
    :rtype: int
    """
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("CFF/CFF2には対応していません。")

    cmap = font_obj.getBestCmap()
    glyf_table = font_obj["glyf"]

    total_y_min = 0
    count = 0

    # 漢字の範囲でループ
    for code, name in cmap.items():
        if not (0x4E00 <= code <= 0x9FFF):
            continue

        if name not in glyf_table:
            continue

        glyph = glyf_table[name]

        # yMinが存在し、かつ空のグリフでないことを確認
        if hasattr(glyph, "yMin"):
            # 極端に小さいゴミデータ（空白など）を除外したい場合はここでフィルタ
            # if (glyph.yMax - glyph.yMin) > (font_obj['head'].unitsPerEm * 0.1):
            total_y_min += glyph.yMin
            count += 1

    if count == 0:
        return 0

    # このフォントの「平均的な底辺」
    avg_y_min = total_y_min / count
    dprint(f"検査対象フォントの 底面平均値: {avg_y_min:.1f}", debug)

    # オフセット = 目標値 - 現在値
    # 例: 目標が -140 で 現在が -200 なら、+60 して浮かせる必要がある
    offset = base_line - avg_y_min

    return round(offset)


if __name__ == "__main__":
    main()
