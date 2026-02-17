import argparse
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from fontTools.ttLib import TTFont

from utils.common.dprint import dprint
from utils.common.save_text import (
    save_text,
)

# 時刻フォーマット
TIME_FORMAT = "%Y/%m/%d %H:%M:%S (UTC)"


@dataclass
class NameRecord:
    name_id: Optional[int] = None
    label: Optional[str] = None
    value: Optional[str] = None

    def __str__(self):
        output = f"[NAMEレコード] {self.name_id}, {self.label}, {self.value}\n"
        return output


@dataclass
class Result:
    is_ttf: Optional[bool] = None
    is_cff: Optional[bool] = None
    is_cff2: Optional[bool] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    glyph_count_all: Optional[int] = None
    glyph_count_uni: Optional[int] = None
    upm: Optional[int] = None
    os2_vendorid: Optional[str] = None
    os2_winascent: Optional[int] = None
    os2_windescent: Optional[int] = None
    os2_typoascender: Optional[int] = None
    os2_typodescender: Optional[int] = None
    os2_typo_linegap: Optional[int] = None
    os2_use_typometrics: Optional[bool] = None
    hhea_ascent: Optional[int] = None
    hhea_descent: Optional[int] = None
    hhea_linegap: Optional[int] = None
    opentype_feature_count: Optional[int] = None
    name_records: list[NameRecord] = field(default_factory=list)

    def __str__(self):
        output = "[フォント情報]\n"
        output += f"TrueType: {self.is_ttf}\n"
        output += f"PostScript (CFF): {self.is_cff}\n"
        output += f"PostScript (CFF2 / Variable): {self.is_cff2}\n"
        output += f"作成日時: {self.created_time}\n"
        output += f"更新日時: {self.modified_time}\n"
        output += f"総グリフ数: {self.glyph_count_all}\n"
        output += f"グリフ数(Unicode割当済): {self.glyph_count_uni}\n"
        output += f"UPM: {self.upm}\n"
        output += f"OS/2 ベンダーID: {self.os2_vendorid}\n"
        output += f"OS/2 WinAscent: {self.os2_winascent}\n"
        output += f"OS/2 WinDescent: {self.os2_windescent}\n"
        output += f"OS/2 TypoAscender: {self.os2_typoascender}\n"
        output += f"OS/2 TypoDescender: {self.os2_typodescender}\n"
        output += f"OS/2 Typo LineGap: {self.os2_typo_linegap}\n"
        output += f"OS/2 Use TypoMetrics: {self.os2_use_typometrics}\n"
        output += f"HHEA Ascent: {self.hhea_ascent}\n"
        output += f"HHEA Descent: {self.hhea_descent}\n"
        output += f"HHEA LineGap: {self.hhea_linegap}\n"
        output += f"OpenType機能数: {self.opentype_feature_count}\n"
        output += "NAMEテーブル\n"
        for name in self.name_records:
            output += str(name)
        return output


def main():
    parser = argparse.ArgumentParser(description="フォント情報を取得する")

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントファイルのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="フォント情報の書き出し先",
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

    action_get_info(**vars(args))


def action_get_info(input_path: str, output_path: str, debug: bool = False, **_):
    font_obj = TTFont(input_path)
    info = get_info(font_obj, debug)
    print(info)
    if output_path is not None:
        output_path = save_text(
            str(info),
            input_path,
            output_path,
            suffix="_info",
        )
        print(f"フォント情報を保存しました: {output_path}")


def get_info(font_obj: TTFont, debug: bool = False) -> Result:
    """
    フォント情報を取得する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: フォント情報
    :rtype: FontInfo
    """

    # アウトライン形式判定
    is_ttf = False
    is_cff = False
    is_cff2 = False
    if 'glyf' in font_obj:
        is_ttf = True
    if 'CFF ' in font_obj:
        is_cff = True
    if 'CFF2' in font_obj:
        is_cff2 = True

    # グリフ数
    glyph_count_all = None
    glyph_count_uni = None
    if hasattr(font_obj, 'getGlyphOrder'):
        glyph_count_all = len(font_obj.getGlyphOrder())
    # MAXPテーブルがあればそちらから取得できる可能性があります。
    elif 'maxp' in font_obj and hasattr(font_obj['maxp'], 'numGlyphs'):
        dprint("MAXPテーブルから総グリフ数を取得しました。", debug)
        glyph_count_all = font_obj['maxp'].numGlyphs
    else:
        dprint("総グリフ数を取得できませんでした。", debug)
    try:
        glyph_count_uni = len(font_obj.getBestCmap().keys())
    except:
        dprint(
            "グリフ数(Unicode割当済)を取得できませんでした。CMAPを判定できていないため、フォントが壊れている可能性があります。",
            debug,
        )

    # HEADテーブル
    created_time = None
    modified_time = None
    upm = None
    if 'head' in font_obj:
        head = font_obj['head']
        created_time = (
            datetime(1904, 1, 1) + timedelta(seconds=head.created)
        ).strftime(TIME_FORMAT)
        modified_time = (
            datetime(1904, 1, 1) + timedelta(seconds=head.modified)
        ).strftime(TIME_FORMAT)
        upm = head.unitsPerEm
    else:
        dprint(
            "HEADテーブルを取得できませんでした。フォントが壊れている可能性があります。",
            debug,
        )

    # OS2テーブル
    os2_vendorid = None
    os2_winascent = None
    os2_windescent = None
    os2_windescent = None
    os2_typoascender = None
    os2_typodescender = None
    os2_typo_linegap = None
    os2_use_typometrics = None
    if 'OS/2' in font_obj:
        os2 = font_obj['OS/2']
        os2_vendorid = os2.achVendID
        os2_winascent = os2.usWinAscent
        os2_windescent = os2.usWinDescent
        os2_typoascender = os2.sTypoAscender
        os2_typodescender = os2.sTypoDescender
        os2_typo_linegap = os2.sTypoLineGap
        os2_use_typometrics = bool(os2.fsSelection & 0b10000000)
    else:
        dprint(
            "OS/2テーブルを取得できませんでした。フォントが壊れている可能性があります。",
            debug,
        )

    # HHEAテーブル
    hhea_ascent = None
    hhea_descent = None
    hhea_linegap = None
    if 'hhea' in font_obj:
        hhea = font_obj['hhea']
        hhea_ascent = hhea.ascent
        hhea_descent = hhea.descent
        hhea_linegap = hhea.lineGap
    else:
        dprint(
            "HHEAテーブルを取得できませんでした。フォントが壊れている可能性があります。",
            debug,
        )

    # GSUBテーブル
    opentype_feature_count = 0
    if 'GSUB' in font_obj and hasattr(font_obj['GSUB'], 'table'):
        gsub_table = font_obj['GSUB'].table
        if hasattr(gsub_table, 'FeatureList') and gsub_table.FeatureList:
            opentype_feature_count = gsub_table.FeatureList.FeatureCount
    else:
        dprint(
            "GSUBテーブルおよびOpentype機能テーブルを取得できませんでした。",
            debug,
        )

    # NAMEテーブル
    name_records = None
    if 'name' in font_obj:
        name = font_obj['name']
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
        if name:
            for name_id, label in target_ids.items():
                name_record = NameRecord()
                record = (
                    name.getName(name_id, 3, 1, 0x411)
                    or name.getName(name_id, 3, 1, 0x409)
                    or name.getName(name_id, 1, 0, 0)
                )
                value = record.toUnicode() if record else "(Not Found)"
                name_record.name_id = name_id
                name_record.label = label
                name_record.value = value
                name_records.append(name_record)
    else:
        dprint(
            "NAMEテーブルを取得できませんでした。フォントが壊れている可能性があります。",
            debug,
        )

    return Result(
        is_ttf=is_ttf,
        is_cff=is_cff,
        is_cff2=is_cff2,
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
        opentype_feature_count=opentype_feature_count,
        name_records=name_records,
    )


if __name__ == "__main__":
    main()
