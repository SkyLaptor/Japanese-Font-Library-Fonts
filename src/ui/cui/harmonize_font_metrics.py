import argparse
import sys

from modules.harmonize_font_metrics import action_harmonize_font_metrics


def main():
    parser = argparse.ArgumentParser(
        description="渡されたベースフォント及びカスタムパラメーターに従いフォントメトリクスを更新する"
    )
    parser.add_argument("input_path", type=str, help="フォントファイルのパス")
    parser.add_argument(
        "-o", "--output_path", type=str, help="処理後のフォントの書き出し先"
    )
    parser.add_argument(
        "-b", "--base_path", type=str, help="ベースとなるフォントファイルのパス"
    )
    parser.add_argument("--scale_width", type=float, default=1.0, help="横幅の拡大率")
    parser.add_argument("--scale_height", type=float, default=1.0, help="縦幅の拡大率")
    parser.add_argument("--offset_width", type=int, default=0, help="横方向の移動量")
    parser.add_argument("--offset_height", type=int, default=0, help="縦方向の移動量")
    parser.add_argument("--debug", action="store_true", help="デバッグ表示の有効化")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    action_harmonize_font_metrics(**vars(args))


if __name__ == "__main__":
    main()
