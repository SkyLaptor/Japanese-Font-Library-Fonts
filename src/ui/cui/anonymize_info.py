import argparse
import sys

from modules.anonymize_info import FONT_NAME, action_anonymize_info


def main():
    parser = argparse.ArgumentParser(
        description="フォント情報から元フォントを特定できる情報を改変して匿名化する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument(
        "-o", "--output_path", type=str, help="匿名化済みフォントの書き出し先"
    )
    parser.add_argument(
        "-n",
        "--font_name",
        type=str,
        default=FONT_NAME,
        help=f"任意のフォント名。空白や記号類は使用できません。 デフォルト: {FONT_NAME}",
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_anonymize_info(**vars(args))


if __name__ == "__main__":
    main()
