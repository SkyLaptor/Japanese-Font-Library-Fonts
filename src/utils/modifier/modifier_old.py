import argparse
import sys

from utils.modifier.anonymize_info import action_anonymize_info
from utils.modifier.change_weight import action_change_weight


def main():
    parser = argparse.ArgumentParser(
        description="フォントへ各種更新を施すためのツールボックス"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
    )
    parser.add_argument(
        "-i",
        "--input_font_file",
        type=str,
        help="フォントファイル",
    )
    parser.add_argument(
        "-b",
        "--base_font_file",
        type=str,
        help="ベースとなるフォントファイル",
    )
    parser.add_argument(
        "-o",
        "--output_font_file",
        type=str,
        help="ファイルの書き出し先",
    )
    parser.add_argument(
        "--scale_width",
        type=float,
        default=1.0,
        help="横方向の拡大縮小率 デフォルト: 1.0",
    )
    parser.add_argument(
        "--scale_height",
        type=float,
        default=1.0,
        help="縦方向の拡大縮小率 デフォルト: 1.0",
    )
    parser.add_argument(
        "--offset_width",
        type=int,
        default=0,
        help="横方向の移動量 デフォルト: 0",
    )
    parser.add_argument(
        "--offset_height",
        type=int,
        default=0,
        help="縦方向の移動量 デフォルト: 0",
    )
    parser.add_argument(
        "--offset_weight",
        type=int,
        default=0,
        help="文字の太さ調整量 デフォルト: 0",
    )
    parser.add_argument(
        "--family_name",
        type=str,
        default="Anonymize",
        help="フォントファミリー名",
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

    dispatch_action(**vars(args))


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


ACTION_MAP = {
    "anonymize_info": action_anonymize_info,
    "change_weight": action_change_weight,
}

if __name__ == "__main__":
    main()
