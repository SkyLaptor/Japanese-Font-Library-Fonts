import argparse
import sys

from modules.inspect_swf_tags import action_inspect_swf_tags


def main():
    parser = argparse.ArgumentParser(description="SWFタグ情報を取得する")
    parser.add_argument("input_path", type=str, help="SWFファイルのパス")
    parser.add_argument("-o", "--output_path", type=str, help="解析結果の書き出し先")
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_inspect_swf_tags(**vars(args))


if __name__ == "__main__":
    main()
