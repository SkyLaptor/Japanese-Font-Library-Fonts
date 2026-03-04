import argparse
import sys

from const import BASE_LINE_TARGET, BUILD_DIR, MERGE_CONF_PATH
from modules.skyrim_builder import ACTION_MAP, dispatch_action


def main():
    parser = argparse.ArgumentParser(
        description="フォントファイルをスカイリム向けのフォントSWFに変換する"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
    )
    parser.add_argument(
        "-w",
        "--work_dir",
        type=str,
        default=BUILD_DIR,
        help="作業対象ディレクトリ",
    )
    parser.add_argument(
        "--base_line",
        type=int,
        default=BASE_LINE_TARGET,
        help=f"オフセット位置決めのためのベースライン デフォルト:{BASE_LINE_TARGET}",
    )
    parser.add_argument(
        "--merge_conf",
        type=str,
        default=MERGE_CONF_PATH,
        help=f"オフセット位置決めのためのベースライン デフォルト:{BASE_LINE_TARGET}",
    )
    parser.add_argument(
        "--anonymize",
        action="store_true",
        help="フォントを匿名化するかどうか。 アクションによっては無視されます。",
    )
    parser.add_argument(
        "--output_font_info",
        action="store_true",
        help="処理後のフォント情報を出力するかどうか。 アクションによっては無視されます。",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモード",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    dispatch_action(**vars(args))


if __name__ == "__main__":
    main()
