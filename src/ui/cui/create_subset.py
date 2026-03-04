import argparse
import sys

from modules.create_subset import action_create_subset


def main():
    parser = argparse.ArgumentParser(description="サブセットフォントを作成する")
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="グリフ一覧の書き出し先")
    parser.add_argument(
        "-s", "--subset_path", type=str, help="サブセットファイルのパス"
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_create_subset(**vars(args))


if __name__ == "__main__":
    main()
