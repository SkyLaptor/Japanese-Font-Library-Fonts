import argparse
import sys

from const import CONDENSE_RATIO_CONFIGS, SKYRIM_BASE_FONT_CONFIGS
from modules.skyrim_optimizer import convert


def main():
    parser = argparse.ArgumentParser(
        description="渡されたフォントをスカイリムのUI向けに最適化します。"
    )
    parser.add_argument(
        "input", type=str, help="最適化したいフォントの入力元ファイルパス"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="", help="出力先ファイルパス"
    )
    parser.add_argument(
        "--base", choices=list(SKYRIM_BASE_FONT_CONFIGS.keys()), default="everywhere"
    )
    parser.add_argument("--subset", type=str, default="", help="サブセットファイルパス")
    parser.add_argument(
        "--condense", choices=list(CONDENSE_RATIO_CONFIGS.keys()), default="normal"
    )
    parser.add_argument("--monospace", action="store_true", help="等幅モード")
    parser.add_argument("--offset_height", type=int, default=0, help="上下位置調整")
    parser.add_argument("--anonymize", action="store_true", help="匿名化")
    parser.add_argument("--debug", action="store_true", help="デバッグモード")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    convert(
        target_font_path=args.input,
        output_font_path=args.output,
        subset_file_path=args.subset,
        base_type=args.base,
        condense_type=args.condense,
        mode_monospace=args.monospace,
        offset_height=args.offset_height,
        anonymize=args.anonymize,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
