import argparse
import sys

from modules.merge_text import action_merge_text


def main():
    parser = argparse.ArgumentParser(
        description="指定ディレクトリ内のテキストを結合する"
    )
    parser.add_argument(
        "input_dir", type=str, help="結合対象のテキストが存在するディレクトリ"
    )
    parser.add_argument(
        "-o", "--output_path", type=str, help="結合済みテキストの書き出し先"
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_merge_text(**vars(args))


if __name__ == "__main__":
    main()
