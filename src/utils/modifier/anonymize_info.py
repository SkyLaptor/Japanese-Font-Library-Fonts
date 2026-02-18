import argparse
import re
import sys
import time  # Unixタイムスタンプが必要

from fontTools.ttLib import TTFont

from utils.common.dprint import dprint
from utils.common.reload_font import reload_font
from utils.common.save_font import save_font
from utils.inspector.get_info import get_info

FONT_NAME = "Anonymous"
# Mac epoch (1904) と Unix epoch (1970) の差分: 2,082,844,800秒
EPOCH_DIFF = 2082844800


def main():
    parser = argparse.ArgumentParser(
        description="フォント情報から元フォントを特定できる情報を改変して匿名化する"
    )

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントファイルのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="匿名化済みフォントの書き出し先",
    )
    parser.add_argument(
        "-n",
        "--font_name",
        type=str,
        default=FONT_NAME,
        help=f"任意のフォント名。空白や記号類は使用できません。 デフォルト: {FONT_NAME}",
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

    action_anonymize_info(**vars(args))


def action_anonymize_info(
    input_path: str,
    output_path: str,
    font_name: str,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        anonymized_font_obj = anonymize_info(input_font_obj, font_name, debug)
        if output_path is not None:
            saved_output_path = save_font(
                font_obj=anonymized_font_obj,
                input_path=input_path,
                output_path=output_path,
                suffix="_anonymized",
            )
            print(f"フォントを保存しました: {saved_output_path}")


def anonymize_info(font_obj: TTFont, font_name: str, debug: bool = False) -> TTFont:
    """
    フォント情報から元フォントを特定できる情報を改変して匿名化する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param font_name: フォント名。空白や記号類は使用できません。
    :type font_name: str
    :param debug: デバッグモード
    :type debug: bool
    :return: 匿名化後のフォント
    :rtype: TTFont
    """
    sub_family = "Regular"
    if font_name == "" or re.search(r"[^\w]", font_name):
        raise ValueError("フォント名に空白や記号類は使用できません。")
    ps_name = font_name + "-" + sub_family

    # デバッグ情報
    dprint("=== 匿名化前のフォント情報", debug)
    dprint(get_info(font_obj), debug)

    # 匿名化に必要な情報だけを絞り込んで操作する（下手にいじるとフォントが壊れる場合があるので注意）
    # nameテーブルの更新
    name = font_obj['name']
    new_names = []
    for record in name.names:
        encoding = record.getEncoding()

        if record.nameID in [1, 16, 17]:  # Family Name
            record.string = font_name.encode(encoding)
        elif record.nameID in [2, 18]:  # Subfamily Name
            record.string = sub_family.encode(encoding)
        elif record.nameID == 3:  # Unique ID
            record.string = f"0.000;NONE;{ps_name}".encode(encoding)
        elif record.nameID == 4:  # Full Name
            record.string = f"{font_name} {sub_family}".encode(encoding)
        elif record.nameID == 5:  # Version
            record.string = "Version 0.000".encode(encoding)
        elif record.nameID == 6:  # PostScript Name
            record.string = ps_name.encode(encoding)
        else:
            # 著作権やURLなどは、空文字を入れるのではなく「リストに入れない」ことで削除
            continue

        new_names.append(record)

    name.names = new_names

    # headテーブルの更新
    head = font_obj['head']
    if head:
        now = int(time.time()) + EPOCH_DIFF
        head.created = now
        head.modified = now

    # OS/2テーブルの更新
    os2 = font_obj['OS/2']
    if os2:
        os2.achVendID = "NONE"

    # デバッグ情報
    dprint("=== 匿名化後のフォント情報", debug)
    dprint(get_info(font_obj), debug)

    return reload_font(font_obj)
