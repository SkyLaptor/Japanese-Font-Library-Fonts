import argparse
import sys

from modules.get_glyphs import action_get_glyphs


def main():
    parser = argparse.ArgumentParser(
        description="フォントに含まれるグリフの一覧を取得する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="グリフ一覧の書き出し先")
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_get_glyphs(**vars(args))


if __name__ == "__main__":
    main()
