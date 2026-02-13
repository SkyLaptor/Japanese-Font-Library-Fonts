from fontTools.ttLib import TTFont

from utils import (
    convert_timestamp,
    is_cff,
    is_cff2,
)
from utils.models import AverageSizeResult, FontInfo, NameRecord


def get_outline_format(font_obj: TTFont) -> str:
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


def get_info(font_obj: TTFont) -> FontInfo:
    """
    # フォント情報を取得する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: フォント情報
    :rtype: FontInfo
    """

    table_names = font_obj.keys()
    print("テーブル一覧")
    print(table_names)

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
        print(f"OpenType機能数: {feature_count}")
    else:
        print("OpenType機能: なし")

    print(f"アウトラインフォーマット: {outline_format}")

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


def get_glyphs(font_obj: TTFont) -> str:
    """
    # フォントに含まれるグリフの一覧を取得する

    不正な空白グリフであっても有効として取得されます。
    必要に応じて不正な空白グリフは事前に消してから使用して下さい。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
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


def get_average_size(font_obj: TTFont) -> AverageSizeResult:
    # CFF/CFF2の場合は非対応
    if is_cff(font_obj) or is_cff2(font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")
    upm = font_obj.get('head').unitsPerEm

    total_width = 0
    total_height = 0
    count = 0

    glyf_table = font_obj["glyf"]
    glyph_names = font_obj.getGlyphOrder()

    for name in glyph_names:
        w, h = 0, 0
        glyph = glyf_table[name]
        if hasattr(glyph, "xMax"):
            w = glyph.xMax - glyph.xMin
            h = glyph.yMax - glyph.yMin

        # ドットやカンマなどの小さいグリフ、横棒などのアスペクトが極端なものは無視します。
        # if (h > upm * 0.4) and (0.5 < w / h < 1.5): # ひらがなとか比較的小さいグリフも含まれる可能性あり
        if (h > upm * 0.5) and (0.8 < w / h < 1.2):  # ほぼ正方形の漢字型のグリフが対象
            total_width += w
            total_height += h
            count += 1

    if count == 0:
        avg_w = 0
        avg_h = 0
    else:
        avg_w = total_width / count
        avg_h = total_height / count

    return AverageSizeResult(
        count=count,
        avg_w=avg_w,
        avg_h=avg_h,
    )
