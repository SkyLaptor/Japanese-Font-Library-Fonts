import argparse
import sys
from pathlib import Path

from const import ENCODE
from utils.common import (
    EXT_TXT,
)
from utils.common.dprint import dprint
from utils.common.save_text import save_text


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

    action_merge_text(**vars(args))


def action_merge_text(input_dir, output_path, debug: bool = False, **_):
    unique_sorted_chars = merge_text(input_dir)
    saved_output_path = save_text(
        unique_sorted_chars, input_dir, output_path, suffix="_merged"
    )
    print(f"マージ済みテキストを出力しました。: {saved_output_path}")


def merge_text(input_dir: str, debug: bool = False) -> str:
    """
    指定ディレクトリ内のテキストを結合する

    :param input_dir: 入力ディレクトリ
    :type input_dir: str
    :param debug: デバッグモード
    :type debug: bool
    :return: 結合済みテキスト
    :rtype: str
    """
    input_dir_path = Path(input_dir)
    all_text = ""

    # 1. ディレクトリ内の全 .txt ファイルをループ
    for txt_file in input_dir_path.glob("*" + EXT_TXT):
        dprint(f"読み込み中... {txt_file.name}", debug)
        all_text += txt_file.read_text(encoding=ENCODE)

    # 2. 改行・空白・タブを削除
    # スカイリムのサブセットには不要な制御文字をここで一掃します
    table = str.maketrans("", "", "\n\r\t ")
    clean_text = all_text.translate(table)

    # 3. 重複排除 & ソート
    unique_sorted_chars = "".join(sorted(set(clean_text)))

    return unique_sorted_chars


if __name__ == "__main__":
    main()
