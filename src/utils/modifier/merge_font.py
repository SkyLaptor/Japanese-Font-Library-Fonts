import argparse
import sys

from fontTools.merge import Merger
from fontTools.ttLib import TTFont


def main():
    parser = argparse.ArgumentParser(
        description="指定ディレクトリ内のテキストを結合する"
    )

    parser.add_argument(
        "input_dir",
        type=str,
        help="結合対象のテキストが存在するディレクトリ",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="結合済みテキストの書き出し先",
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

    action_merge_font(**vars(args))


def action_merge_font():
    return


def merge_font(font_objs: list[TTFont], debug: bool = False):
    # Mergerインスタンスの作成
    merger = Merger()

    # マージ実行
    # 先に指定したフォントが「ベース」になり、
    # 後のフォントに同名グリフがあれば上書き、なければ追加されます
    font = merger.merge([base_path, sub_path])


if __name__ == "__main__":
    main()
