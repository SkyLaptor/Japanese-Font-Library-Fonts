# Dependencies: FFDec=False, FontForge=False
import re
import time

from fontTools.ttLib import TTFont

from core.font_loader import reopen_font
from modules.get_info import get_info
from utils.dprint import dprint
from utils.file_io import save_font

FONT_NAME = "Anonymous"
EPOCH_DIFF = 2082844800


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


def anonymize_info(
    font_obj: TTFont, font_name: str = FONT_NAME, debug: bool = False
) -> TTFont:
    sub_family = "Regular"
    if font_name == "" or re.search(r"[^\w]", font_name):
        raise ValueError("フォント名に空白や記号類は使用できません。")
    ps_name = font_name + "-" + sub_family

    dprint("=== 匿名化前のフォント情報", debug)
    dprint(get_info(font_obj), debug)

    name = font_obj['name']
    new_names = []
    for record in name.names:
        encoding = record.getEncoding()

        if record.nameID in [1, 16, 17]:
            record.string = font_name.encode(encoding)
        elif record.nameID in [2, 18]:
            record.string = sub_family.encode(encoding)
        elif record.nameID == 3:
            record.string = f"0.000;NONE;{ps_name}".encode(encoding)
        elif record.nameID == 4:
            record.string = f"{font_name} {sub_family}".encode(encoding)
        elif record.nameID == 5:
            record.string = "Version 0.000".encode(encoding)
        elif record.nameID == 6:
            record.string = ps_name.encode(encoding)
        else:
            continue

        new_names.append(record)

    name.names = new_names

    head = font_obj['head']
    if head:
        now = int(time.time()) + EPOCH_DIFF
        head.created = now
        head.modified = now

    os2 = font_obj['OS/2']
    if os2:
        os2.achVendID = "NONE"

    dprint("=== 匿名化後のフォント情報", debug)
    dprint(get_info(font_obj), debug)

    return reopen_font(font_obj)
