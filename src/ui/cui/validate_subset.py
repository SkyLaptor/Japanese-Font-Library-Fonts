import argparse
import sys

from modules.validate_subset import action_validate_subset


def main():
    parser = argparse.ArgumentParser(
        description="サブセット文字列とフォントに格納されている文字を比較検証する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="比較結果の書き出し先")
    parser.add_argument(
        "-s", "--subset_path", type=str, help="サブセットファイルのパス"
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_validate_subset(**vars(args))


if __name__ == "__main__":
    main()
