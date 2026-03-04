import argparse
import sys

from modules.subset_generator import generate_subset_jp_jisx0208
from utils.dprint import dprint
from utils.file_io import save_text


def main():
    parser = argparse.ArgumentParser(
        description="JIS第二基準(JISX0208)サブセットテキストを生成する"
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="サブセットテキストの書き出し先",
    )
    parser.add_argument(
        "--validnamechars_escape",
        action="store_true",
        help="fontconfig.txtのvalidNameChars向けエスケープ有効化",
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
    action_generate_subset_jp_jisx0208(**vars(args))


def action_generate_subset_jp_jisx0208(
    output_path: str, validnamechars_escape: bool, debug: bool = False, **_
):
    subset_text = generate_subset_jp_jisx0208(
        validnamechars_escape=validnamechars_escape
    )
    dprint(subset_text, debug)

    if output_path is not None:
        saved_output_path = save_text(subset_text, output_path=output_path)
        print(f"生成したサブセットを出力しました。: {saved_output_path}")


if __name__ == "__main__":
    main()
