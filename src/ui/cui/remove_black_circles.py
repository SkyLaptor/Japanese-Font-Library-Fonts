import argparse
import sys

from modules.remove_black_circles import (
    REMOVE_TARGET_SIZE,
    action_remove_black_circles,
)


def main():
    parser = argparse.ArgumentParser(
        description="フォントから不正な黒丸（●）と思われるグリフを検出し削除する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="フォントの出力先")
    parser.add_argument(
        "-t",
        "--target_size",
        type=int,
        default=REMOVE_TARGET_SIZE,
        help="削除対象とする黒丸の最大サイズ",
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_remove_black_circles(**vars(args))


if __name__ == "__main__":
    main()
