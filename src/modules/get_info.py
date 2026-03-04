# Dependencies: FFDec=False, FontForge=False
from datetime import datetime, timedelta

from fontTools.ttLib import TTFont

from models.font_info_result import FontInfoResult, NameRecord
from utils.dprint import dprint
from utils.file_io import save_text

TIME_FORMAT = "%Y/%m/%d %H:%M:%S (UTC)"


def action_get_info(input_path: str, output_path: str, debug: bool = False, **_):
    with TTFont(input_path) as input_font_obj:
        info = get_info(input_font_obj, debug)
        print(info)
        if output_path is not None:
            output_path = save_text(
                str(info),
                input_path,
                output_path,
                suffix="_info",
            )
            print(f"フォント情報を保存しました: {output_path}")


def get_info(font_obj: TTFont, debug: bool = False) -> FontInfoResult:
    is_ttf = False
    is_cff = False
    is_cff2 = False
    if 'glyf' in font_obj:
        is_ttf = True
    if 'CFF ' in font_obj:
        is_cff = True
    if 'CFF2' in font_obj:
        is_cff2 = True

    glyph_count_all = None
    glyph_count_uni = None
    if hasattr(font_obj, 'getGlyphOrder'):
        glyph_count_all = len(font_obj.getGlyphOrder())
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

    return FontInfoResult(
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
