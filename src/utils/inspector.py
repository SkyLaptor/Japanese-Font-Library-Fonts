import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from utils.common import (
    convert_timestamp,
    dprint,
    is_cff,
    is_cff2,
    is_ttf,
    load_text,
    save_text,
)
from utils.models import AverageSizeResult, FontInfo, NameRecord


def main():
    parser = argparse.ArgumentParser(
        description="フォントの検査を行うためのツールボックス"
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
        "--output_text_file",
        type=str,
        help="テキストの書き出し先",
    )
    parser.add_argument(
        "--subset_text_file",
        type=str,
        default="",
        help="サブセットテキストファイル",
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


def action_get_outline_format(
    input_font_file: str, output_text_file: str = "", debug: bool = False
):
    font_obj = TTFont(input_font_file)
    print(
        f"フォントのアウトラインフォーマット: {get_outline_format(font_obj=font_obj, debug=debug)}"
    )


def get_outline_format(font_obj: TTFont, debug: bool = False) -> str:
    outline_format = ""
    if 'CFF2' in font_obj:
        outline_format = "PostScript (CFF2 / Variable)"
    elif 'CFF ' in font_obj:
        outline_format = "PostScript (CFF)"
    elif 'glyf' in font_obj:
        outline_format = "TrueType"
    else:
        raise ValueError("フォントのアウトライン形式が不明です。")
    return outline_format


def action_check_fonttype(input, **_):
    ext = Path(input).suffix.lower()
    font_obj = TTFont(input)
    if is_cff(font_obj) or is_cff2(font_obj):
        if ".otf" != ext:
            print(
                f"拡張子は{ext}ですが、フォントの形式はOTFです。拡張子が間違っています。"
            )
        else:
            print("フォントの形式はOTFです。(正常)")
    elif is_ttf(font_obj):
        if ".ttf" != ext:
            print(
                f"拡張子は{ext}ですが、フォントの形式はTTFです。拡張子が間違っています。"
            )
        else:
            print("フォントの形式はTTFです。(正常)")
    else:
        print(
            "フォントの形式が判別できませんでした。本スクリプトでは正常に動作しない可能性が高いです。"
        )


def action_get_info(input_font_file: str, output_text_file: str, debug: bool = False):
    font_obj = TTFont(input_font_file)
    info = get_info(font_obj=font_obj, debug=debug)
    output_text_file = save_text(
        text=str(info), input=input_font_file, output=output_text_file, suffix="_info"
    )
    dprint(info, debug)
    print(f"フォント情報を保存しました: {output_text_file}")


def get_info(font_obj: TTFont, debug: bool = False) -> FontInfo:
    """
    # フォント情報を取得する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: フォント情報
    :rtype: FontInfo
    """

    table_names = font_obj.keys()
    dprint("テーブル一覧", debug)
    dprint(table_names, debug)

    # どのテーブルが存在するかでアウトライン形式を判定
    if 'CFF2' in font_obj:
        outline_format = "PostScript (CFF2 / Variable)"
    elif 'CFF ' in font_obj:
        outline_format = "PostScript (CFF)"
    elif 'glyf' in font_obj:
        outline_format = "TrueType"
    else:
        outline_format = "Unknown"

    if 'GSUB' in font_obj:
        gsub_table = font_obj['GSUB'].table
        feature_count = gsub_table.FeatureList.FeatureCount
        dprint(f"OpenType機能数: {feature_count}", debug)
    else:
        dprint("OpenType機能: なし", debug)

    dprint(f"アウトラインフォーマット: {outline_format}", debug)

    head = font_obj.get('head')
    created_time = None
    upm = None
    if head:
        created_time = convert_timestamp(head.created)
        modified_time = convert_timestamp(head.modified)
        upm = head.unitsPerEm

    glyph_count_all = len(font_obj.getGlyphOrder())
    glyph_count_uni = len(font_obj.getBestCmap().keys())

    os2 = font_obj.get('OS/2')
    os2_vendorid = None
    os2_winascent = None
    os2_windescent = None
    os2_windescent = None
    os2_typoascender = None
    os2_typodescender = None
    os2_typo_linegap = None
    os2_use_typometrics = None
    if os2:
        os2_vendorid = os2.achVendID
        os2_winascent = os2.usWinAscent
        os2_windescent = os2.usWinDescent
        os2_typoascender = os2.sTypoAscender
        os2_typodescender = os2.sTypoDescender
        os2_typo_linegap = os2.sTypoLineGap
        os2_use_typometrics = bool(os2.fsSelection & 0b10000000)

    hhea = font_obj.get('hhea')
    hhea_ascent = None
    hhea_descent = None
    hhea_linegap = None
    if hhea:
        hhea_ascent = hhea.ascent
        hhea_descent = hhea.descent
        hhea_linegap = hhea.lineGap

    name_table = font_obj.get('name')
    target_ids = {
        0: "Copyright",
        1: "Family Name",
        2: "Subfamily Name",
        3: "Unique ID",
        4: "Full Name",
        5: "Version",
        6: "PostScript Name",
        13: "License",
    }
    name_records = []
    if name_table:
        for name_id, label in target_ids.items():
            name_record = NameRecord()
            record = (
                name_table.getName(name_id, 3, 1, 0x411)
                or name_table.getName(name_id, 3, 1, 0x409)
                or name_table.getName(name_id, 1, 0, 0)
            )
            value = record.toUnicode() if record else "(Not Found)"
            name_record.name_id = name_id
            name_record.label = label
            name_record.value = value
            name_records.append(name_record)

    return FontInfo(
        created_time=created_time,
        modified_time=modified_time,
        glyph_count_all=glyph_count_all,
        glyph_count_uni=glyph_count_uni,
        upm=upm,
        os2_vendorid=os2_vendorid,
        os2_winascent=os2_winascent,
        os2_windescent=os2_windescent,
        os2_typoascender=os2_typoascender,
        os2_typodescender=os2_typodescender,
        os2_typo_linegap=os2_typo_linegap,
        os2_use_typometrics=os2_use_typometrics,
        hhea_ascent=hhea_ascent,
        hhea_descent=hhea_descent,
        hhea_linegap=hhea_linegap,
        name_records=name_records,
    )


def action_get_glyphs(
    input_font_file: str,
    output_text_file: str,
    subset_text_file: set = "",
    debug: bool = False,
):
    font_obj = TTFont(input_font_file)
    glyphs = get_glyphs(font_obj=font_obj, debug=debug)
    dprint(f"フォント内のグリフ数(Unicode割当済): {len(glyphs)}", debug)
    output_text_file = save_text(
        text=glyphs, input=input_font_file, output=output_text_file, suffix="_glyphs"
    )
    print(f"グリフの一覧を保存しました: {output_text_file}")


def get_glyphs(font_obj: TTFont, debug: bool = False) -> str:
    """
    # フォントに含まれるグリフの一覧を取得する

    不正な空白グリフであっても有効として取得されます。
    必要に応じて不正な空白グリフは事前に消してから使用して下さい。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: グリフ一覧
    :rtype: str

    """

    # cmap（文字コードとグリフ名の対応表）を取得
    cmap = font_obj.getBestCmap()

    # Unicode値(int)から文字(str)に変換
    # cmapのキーはUnicode値(整数)
    valid_chars = []
    for code in sorted(cmap.keys()):
        char = chr(code)
        valid_chars.append(char)

    # 文字列に変換
    glyph_text = "".join(valid_chars)

    return glyph_text


def action_get_average_size(
    input_font_file: str, output_text_file: str, debug: bool = False
):
    font_obj = TTFont(input_font_file)
    result = get_average_size(font_obj=font_obj, debug=debug)
    output_text_file = save_text(
        text=str(result),
        input=input_font_file,
        output=output_text_file,
        suffix="_average_size",
    )
    dprint(result, debug)
    print(f"平均値取得結果を保存しました: {output_text_file}")


def get_average_size(font_obj: TTFont, debug: bool = False) -> AverageSizeResult:
    # CFF/CFF2の場合は非対応
    if is_cff(font_obj) or is_cff2(font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    upm = font_obj.get('head').unitsPerEm
    cmap = font_obj.getBestCmap()
    glyf_table = font_obj["glyf"]

    total_width = 0
    total_height = 0
    count = 0

    # Unicode（コードポイント）でループを回す
    # 4E00 - 9FFF が一般的な漢字の範囲
    for code, name in cmap.items():
        if not (0x4E00 <= code <= 0x9FFF):
            continue

        if name not in glyf_table:
            continue

        glyph = glyf_table[name]
        w, h = 0, 0
        if hasattr(glyph, "xMax"):
            w = glyph.xMax - glyph.xMin
            h = glyph.yMax - glyph.yMin

        # 漢字範囲に絞っているので、条件は少し緩めても「変な文字」が混ざらなくなります
        # if h > upm * 0.2:
        #     total_width += w
        #     total_height += h
        #     count += 1
        total_width += w
        total_height += h
        count += 1

    if count == 0:
        avg_w, avg_h = 0, 0
    else:
        avg_w = total_width / count
        avg_h = total_height / count

    return AverageSizeResult(
        count=count,
        avg_w=avg_w,
        avg_h=avg_h,
    )


def action_validate_subset(
    input_font_file: str,
    output_text_file: str,
    subset_text_file: str,
    debug: bool = False,
):
    font_obj = TTFont(input_font_file)
    subset_text = load_text(text_path=subset_text_file)
    missing_glyphs = validate_subset(font_obj=font_obj, subset_text=subset_text)
    output_text_file = save_text(
        text=missing_glyphs,
        input=input_font_file,
        output=output_text_file,
        suffix="_missing_glyphs",
    )
    print(f"サブセットにあってフォントに無い文字列を出力しました: {output_text_file}")


def validate_subset(font_obj: TTFont, subset_text: str, debug: bool = False) -> str:
    # 1. フォントが持っている全Unicode文字を取得（すでに作成済みの get_glyphs を利用）
    # font_in_glyphs は set([ 'あ', 'い', 'う', ... ]) のような形式を想定
    font_in_glyphs_str = get_glyphs(font_obj=font_obj)
    font_in_glyphs = set(font_in_glyphs_str)  # ここで set に変換！

    # 2. サブセットテキストも一文字ずつの set にする
    subset_chars = set(subset_text)

    # 3. 差分を抽出： subset_chars にあって font_in_glyphs にないもの
    missing_chars = subset_chars - font_in_glyphs

    # 4. 結果の表示
    if not missing_chars:
        print(
            "[SUCCESS]: おめでとうございます！すべての文字がフォントに含まれています。"
        )
    else:
        print(
            f"[WARNING]: フォントに存在しない文字が {len(missing_chars)} 文字あります！"
        )

        # ソートして表示（何が足りないか見やすくする）
        sorted_missing = sorted(list(missing_chars))

        # あまりに多いとログが埋まるので、一部だけ出すか、デバッグ時のみ全出し
        display_text = "".join(sorted_missing)
        if len(display_text) > 100 and not debug:
            print(f"足りない文字（先頭100文字）: {display_text[:100]}...")
        else:
            print(f"足りない文字: {display_text}")

    # 欠落文字をソートしたリスト
    sorted_missing_list = sorted(list(missing_chars))
    # リストを一つの文字列に結合（これが必要！）
    sorted_missing_str = "".join(sorted_missing_list)

    return sorted_missing_str


ACTION_MAP = {
    "check_fonttype": action_check_fonttype,
    "get_outline_format": action_get_outline_format,
    "get_info": action_get_info,
    "get_glyphs": action_get_glyphs,
    "get_average_size": action_get_average_size,
    "validate_subset": action_validate_subset,
}

if __name__ == "__main__":
    main()
