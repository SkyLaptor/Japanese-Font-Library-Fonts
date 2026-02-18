import argparse
import math
import sys

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import Path

from utils.common.dprint import dprint
from utils.common.reload_font import reload_font
from utils.common.save_font import save_font


def main():
    parser = argparse.ArgumentParser(description="文字の太さを変更する")

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
        "-w",
        "--offset_weight",
        type=int,
        help="太さ変更量",
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

    action_change_weight(**vars(args))


def action_change_weight(
    input_path: str,
    output_path: str,
    offset_weight: int,
    debug: bool = False,
    **_,
):
    font_obj = TTFont(input_path)
    weight_changed_font_obj = change_weight(font_obj, offset_weight, debug)
    print(f"文字の太さを変更しました: 変更量: {offset_weight}")
    if output_path is not None:
        saved_output_path = save_font(
            weight_changed_font_obj,
            input_path,
            output_path,
            "_weight_changed",
        )
        print(f"太さを変更したフォントを保存しました: {saved_output_path}")


def change_weight(font_obj: TTFont, offset_weight: int, debug: bool = False) -> TTFont:
    """
    文字の太さを変更する

    負荷が高く不安定な処理です。可能な限り公式が提供しているウェイトフォントを使用することをお勧めします。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param offset_weight: 太さ調整値。正の値で太く、負の値で細くなります。
    :type offset_weight: int
    :param debug: デバッグモード
    :type debug: bool
    :return: 変形後のフォントオブジェクト
    :rtype: TTFont
    """

    # CFF/CFF2の場合は非対応
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    # オフセットが0の場合、操作する必要がないためそのまま返却
    # なんとなくリロード
    if offset_weight == 0:
        return reload_font(font_obj)

    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()
    actual_offset = -offset_weight

    def get_normal(dx, dy):
        l = math.sqrt(dx * dx + dy * dy)
        return (dy / l, -dx / l) if l != 0 else (0, 0)

    for name in glyph_names:
        # OTF/TTF問わず、TTF形式のペンで座標を取り出す
        # これで計算可能な coordinates リストが手に入る
        temp_pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(temp_pen)
        temp_glyph = temp_pen.glyph()

        if temp_glyph.numberOfContours <= 0:
            continue

        # 肉付けロジック
        coords = list(temp_glyph.coordinates)
        new_coords = list(coords)
        start_idx = 0
        for end_idx in temp_glyph.endPtsOfContours:
            contour_indices = list(range(start_idx, end_idx + 1))
            n = len(contour_indices)
            if n >= 2:
                for i in range(n):
                    curr_idx = contour_indices[i]
                    prev_idx = contour_indices[(i - 1) % n]
                    next_idx = contour_indices[(i + 1) % n]
                    x0, y0 = coords[prev_idx]
                    x1, y1 = coords[curr_idx]
                    x2, y2 = coords[next_idx]
                    v1x, v1y = x1 - x0, y1 - y0
                    v2x, v2y = x2 - x1, y2 - y1
                    n1x, n1y = get_normal(v1x, v1y)
                    n2x, n2y = get_normal(v2x, v2y)
                    nx, ny = n1x + n2x, n1y + n2y
                    n_len = math.sqrt(nx * nx + ny * ny)
                    if n_len != 0:
                        new_coords[curr_idx] = (
                            round(
                                x1 + (nx / n_len) * actual_offset, 2
                            ),  # 小数点以下2桁程度に
                            round(y1 + (ny / n_len) * actual_offset, 2),
                        )
            start_idx = end_idx + 1

        temp_glyph.coordinates = type(temp_glyph.coordinates)(new_coords)

        # 重なりを合体させて白抜けを防ぐ
        rec_pen = RecordingPen()
        temp_glyph.draw(rec_pen, font_obj['glyf'])

        path = Path()
        pen = path.getPen()
        rec_pen.replay(pen)

        try:
            path.simplify()
        except Exception as e:
            dprint(e, debug)
            dprint(f"グリフ '{name}' の簡略化に失敗したためスキップします。", debug)

        tt_pen = TTGlyphPen(glyph_set)
        path.draw(tt_pen)
        # font_obj['glyf'][name] = tt_pen.glyph()
        # .glyphs 辞書を直接叩くことで、お節介なバリデーションを回避する
    font_obj['glyf'].glyphs[name] = tt_pen.glyph()

    return reload_font(font_obj)


if __name__ == "__main__":
    main()
