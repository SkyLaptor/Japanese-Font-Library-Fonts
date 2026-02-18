import argparse
import sys
from pathlib import Path

from const import ENCODE
from utils.common.dprint import dprint
from utils.common.save_text import save_text
from utils.inspector.validate_subset import EXCLUDE_CHARS


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
    unique_sorted_chars = merge_text(input_dir, debug)
    if output_path is not None:
        saved_output_path = save_text(
            unique_sorted_chars, output_path=output_path, suffix="_merged"
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
    all_content = []

    # 1. 読み込み
    # EXT_TXT は ".txt" の想定。もしドットがないなら f".{EXT_TXT}" としてください
    for txt_file in input_dir_path.glob("*.txt"):
        dprint(f"読み込み中... {txt_file.name}", debug)
        all_content.append(txt_file.read_text(encoding=ENCODE))

    # 2. 結合
    combined_text = "".join(all_content)

    # 3. EXCLUDE_CHARS を除外
    table = str.maketrans("", "", EXCLUDE_CHARS)
    clean_text = combined_text.translate(table)

    # 4. 重複排除 & ソート
    unique_sorted_chars = "".join(sorted(set(clean_text)))

    return unique_sorted_chars


if __name__ == "__main__":
    main()
