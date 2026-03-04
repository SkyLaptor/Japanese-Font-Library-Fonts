import argparse
import sys

from const import BASE_LINE_TARGET
from modules.get_offset_to_align_bottom import action_get_offset_to_align_bottom


def main():
    parser = argparse.ArgumentParser(
        description="フォント内のグリフの底面位置が基準値からどれだけ異なるか計算する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument(
        "-o", "--output_path", type=str, help="オフセット値の書き出し先"
    )
    parser.add_argument(
        "-b",
        "--base_line",
        type=int,
        default=BASE_LINE_TARGET,
        help=f"基準となるY座標 デフォルト:{BASE_LINE_TARGET}",
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_get_offset_to_align_bottom(**vars(args))


if __name__ == "__main__":
    main()
