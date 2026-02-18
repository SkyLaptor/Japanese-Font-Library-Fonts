import argparse
import sys

from fontTools.ttLib import TTFont

from utils.common.save_font import save_font


def main():
    parser = argparse.ArgumentParser(description="2つのフォントを結合する")

    parser.add_argument(
        "base_path",
        type=str,
        help="ベースとなるフォントのパス",
    )
    parser.add_argument(
        "interpolation_path",
        type=str,
        help="補間を行うフォントのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="結合済みフォントの書き出し先",
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


def action_merge_font(
    base_path: str, interpolation_path: str, output_path: str, debug: bool = False, **_
):
    with TTFont(base_path) as base_font_obj, TTFont(
        interpolation_path
    ) as interpolation_font_obj:
        merged_font = merge_font(base_font_obj, interpolation_font_obj, debug)
        if output_path is not None:
            saved_output_path = save_font(
                font_obj=merged_font,
                input_path=base_path,
                output_path=output_path,
                suffix="_merged",
                debug=debug,
            )
            print(f"フォントを保存しました: {saved_output_path}")


def merge_font(
    base_font_obj: TTFont, interpolation_font_obj: TTFont, debug: bool = False
) -> TTFont:
    # TODO: 未実装
    return


if __name__ == "__main__":
    main()
