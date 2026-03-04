import argparse
import sys

from modules.get_info import action_get_info


def main():
    parser = argparse.ArgumentParser(description="フォント情報を取得する")
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument(
        "-o", "--output_path", type=str, help="フォント情報の書き出し先"
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_get_info(**vars(args))


if __name__ == "__main__":
    main()
