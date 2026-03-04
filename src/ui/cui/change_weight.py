import argparse
import sys

from modules.change_weight import action_change_weight


def main():
    parser = argparse.ArgumentParser(description="文字の太さを変更する")
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="グリフ一覧の書き出し先")
    parser.add_argument("-w", "--offset_weight", type=int, default=0, help="太さ変更量")
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_change_weight(**vars(args))


if __name__ == "__main__":
    main()
