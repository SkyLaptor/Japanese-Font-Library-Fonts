import argparse
import sys

from fontTools.ttLib import TTFont

from utils.common.reload_font import reload_font
from utils.common.save_font import save_font
from utils.optimizer.remove_black_circles import action_remove_black_circles
from utils.subsetter.create_subset import action_create_subset
from utils.subsetter.remove_empty_glyphs import action_remove_empty_glyphs


def main():
    parser = argparse.ArgumentParser(
        description="フォントへ各種最適化を施すためのツールボックス"
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
        "-o",
        "--output_font_file",
        type=str,
        help="ファイルの書き出し先",
    )
    parser.add_argument(
        "-s",
        "--subset_file",
        type=str,
        default="",
        help="サブセットファイル デフォルト: ''",
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


def action_optimize_for_swf(
    input_font_file: str, output_font_file: str, debug: bool = False, **_
):
    font_obj = TTFont(input_font_file)
    font_obj = optimize_for_swf(font_obj=font_obj, debug=debug)
    output_font_file = save_font(
        font_obj=font_obj, input_path=input_font_file, output_path=output_font_file
    )
    print(f"フォントを保存しました: {output_font_file}")


def optimize_for_swf(font_obj: TTFont, debug: bool = False) -> TTFont:
    """
    SWFに埋め込むためのフォントに最適化する

    :param font_obj: フォント
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: 最適化済みフォント
    :rtype: TTFont
    """
    # 縦書き関連などSWFに不要なテーブル
    drop_tables = [
        'mort',
        'vhea',
        'vmtx',
        'VORG',
        'BASE',
        'DSIG',
        'gasp',
        'hdmx',
        'LTSH',
        'PCLT',
        'GSUB',
        'GPOS',
    ]

    for table_tag in drop_tables:
        if table_tag in font_obj:
            del font_obj[table_tag]
            print(f"削除しました: {table_tag}")

    return reload_font(font_obj=font_obj)


ACTION_MAP = {
    "optimize_for_swf": action_optimize_for_swf,
    "create_subset": action_create_subset,
    "remove_empty_glyphs": action_remove_empty_glyphs,
    "remove_black_circles": action_remove_black_circles,
}

if __name__ == "__main__":
    main()
