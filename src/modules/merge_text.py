# Dependencies: FFDec=False, FontForge=False
from pathlib import Path

from const import ENCODE
from modules.validate_subset import EXCLUDE_CHARS
from utils.dprint import dprint
from utils.file_io import save_text


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

    for txt_file in input_dir_path.glob("*.txt"):
        dprint(f"読み込み中... {txt_file.name}", debug)
        all_content.append(txt_file.read_text(encoding=ENCODE))

    combined_text = "".join(all_content)

    table = str.maketrans("", "", EXCLUDE_CHARS)
    clean_text = combined_text.translate(table)

    unique_sorted_chars = "".join(sorted(set(clean_text)))

    return unique_sorted_chars
