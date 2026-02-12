from fontTools.pens.boundsPen import ControlBoundsPen
from fontTools.ttLib import TTFont

from utils import BLANK_GLYPHS, MSG_FONTTYPE_UNIDENT, convert_timestamp, is_otf, is_ttf
from utils.models import AverageSizeResult, FontInfo, NameRecord


def get_info(font_obj: TTFont) -> FontInfo:
    """
    # フォント情報を取得する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: フォント情報
    :rtype: FontInfo
    """
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
    hhea_ascender = None
    hhea_descender = None
    hhea_linegap = None
    if hhea:
        hhea_ascender = hhea.ascender
        hhea_descender = hhea.descender
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
        hhea_ascender=hhea_ascender,
        hhea_descender=hhea_descender,
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
    """
    # フォント内の各グリフのサイズを解析して平均値を取得する

    フォントのUPMと比例する値のため、異なるUPMのフォントと比較する際にはUPSを合わせてしてから比較して下さい。
    * ノーマライズ計算式 (UPM1024に揃える場合)
    ```
    ノーマライズ横幅平均値 = (元の横幅平均値 / 元フォントのUPM) * 1024
    ノーマライズ縦幅平均値 = (元の縦幅平均値 / 元フォントのUPM) * 1024
    ```

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 平均値測定結果
    :rtype: AverageSizeResult
    """
    head = font_obj.get('head')
    upm = head.unitsPerEm

    total_width = 0
    total_height = 0
    count = 0

    # TTFの場合、glyf_tableを取り出す際にグリフ数分の参照が発生するため、
    # メインループの外で取り出しておくことで高速化します。
    if is_ttf(font_obj):
        glyf_table = font_obj["glyf"]

    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()

    for name in glyph_names:
        w, h = 0, 0
        if is_ttf(font_obj):
            # TTFの場合
            glyph = glyf_table[name]
            if hasattr(glyph, "xMax"):
                w = glyph.xMax - glyph.xMin
                h = glyph.yMax - glyph.yMin
        elif is_otf(font_obj):
            # OTFの場合
            glyph = glyph_set[name]
            # ControlBoundsPen はベジェ曲線の制御点を含むので高速です。
            pen = ControlBoundsPen(glyph_set)
            glyph.draw(pen)
            if pen.bounds:
                w = pen.bounds[2] - pen.bounds[0]
                h = pen.bounds[3] - pen.bounds[1]
        else:
            raise ValueError(MSG_FONTTYPE_UNIDENT)

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
        upm=upm,
        count=count,
        avg_w=avg_w,
        avg_h=avg_h,
    )


def get_empty_glyphs(font_obj: TTFont) -> set:
    """
    # フォント内の空白グリフ一覧を取得する

    サブセット作成や空白グリフ削除といった内部でサブセッターを使っているものは、
    同一のフォントオブジェクトに対して2回サブセッターを通すと不具合が発生します。
    例えば空白グリフ削除（サブセッター使用）してからサブセット作成（サブセッター使用）すると不具合が発生します。
    そのため本メソッドで空白グリフ判定部分を共通化し、それぞれの機能で利用します。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 空白グリフ一覧
    :rtype: set
    """
    empty_names = set()
    all_glyphs = font_obj.getGlyphOrder()

    if is_ttf(font_obj):  # TTF
        glyf_table = font_obj['glyf']
        for name in all_glyphs:
            if name in BLANK_GLYPHS:
                continue
            glyph = glyf_table[name]
            if glyph.numberOfContours == 0 and not hasattr(glyph, "components"):
                empty_names.add(name)

    elif is_otf(font_obj):  # OTF
        charstrings = font_obj['CFF '].cff.topDictIndex[0].CharStrings
        for name in all_glyphs:
            if name in BLANK_GLYPHS:
                continue
            if len(charstrings[name].bytecode) <= 1:
                empty_names.add(name)

    else:
        raise ValueError(MSG_FONTTYPE_UNIDENT)

    return empty_names
