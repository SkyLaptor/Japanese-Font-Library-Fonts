import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="フォントを再構成するためのツールボックス"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
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


# TODO: フォントマージ関数を直使用するアクション
# TODO: フォントマージ関数

ACTION_MAP = {}

if __name__ == "__main__":
    main()
