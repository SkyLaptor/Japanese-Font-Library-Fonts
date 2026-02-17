import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from fontTools.ttLib import TTFont

from utils.common.save_text import (
    save_text,
)


@dataclass
class Result:
    count: Optional[int] = None
    avg_w: Optional[float] = None
    avg_h: Optional[float] = None

    def __str__(self):
        output = "[サイズ平均測定結果]\n"
        output += f"平均算出に用いたグリフ数: {self.count}\n"
        output += f"平均値: 横幅:{self.avg_w:.1f}, 縦幅:{self.avg_h:.1f}\n"
        return output


def main():
    parser = argparse.ArgumentParser(description="フォント内グリフの平均サイズを取得")

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントファイルのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="平均サイズ情報の書き出し先",
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

    action_get_average_size(**vars(args))


def action_get_average_size(
    input_path: str, output_path: str, debug: bool = False, **_
):
    font_obj = TTFont(input_path)
    result = get_average_size(font_obj, debug)
    print(result)
    if output_path is not None:
        output_path = save_text(
            str(result),
            input_path,
            output_path,
            "_average_size",
        )
        print(f"平均値計算結果を保存しました: {output_path}")


def get_average_size(font_obj: TTFont, debug: bool = False) -> Result:
    """
    フォント内のグリフの大きさの平均値を計算する。

    平均値の対象となるグリフはその大きさの均一性から一般的な漢字の範囲に限定しています。
    漢字の範囲に空白が混ざっていると精度が落ちるため、
    この計算を行う前にフォントから余分な空白グリフを清掃しておいてください。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: 計算結果
    :rtype: AverageSizeResult
    """
    # CFF/CFF2の場合は非対応
    if 'CFF ' in font_obj or 'CFF2' in font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    cmap = font_obj.getBestCmap()
    glyf_table = font_obj["glyf"]

    total_width = 0
    total_height = 0
    count = 0

    # Unicode（コードポイント）でループを回す
    # 4E00 - 9FFF が一般的な漢字の範囲
    for code, name in cmap.items():
        if not (0x4E00 <= code <= 0x9FFF):
            continue

        if name not in glyf_table:
            continue

        glyph = glyf_table[name]
        w, h = 0, 0
        if hasattr(glyph, "xMax"):
            w = glyph.xMax - glyph.xMin
            h = glyph.yMax - glyph.yMin

        # 漢字範囲に絞っているので、条件は少し緩めても「変な文字」が混ざらなくなります
        # if h > upm * 0.2:
        #     total_width += w
        #     total_height += h
        #     count += 1
        total_width += w
        total_height += h
        count += 1

    if count == 0:
        avg_w, avg_h = 0, 0
    else:
        avg_w = total_width / count
        avg_h = total_height / count

    return Result(
        count=count,
        avg_w=avg_w,
        avg_h=avg_h,
    )


if __name__ == "__main__":
    main()
