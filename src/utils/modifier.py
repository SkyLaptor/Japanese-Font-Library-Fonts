import math
import re
import time

from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import Path

from models import MetricsSetResult
from utils import MSG_FONTTYPE_UNIDENT, is_otf, is_ttf


def transform_glyphs(
    font_obj: TTFont,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    width_offset: int = 0,
    height_offset: int = 0,
) -> TTFont:
    """
    # グリフの変形を行う

    本処理後のフォントオブジェクトはメトリクス情報が正しく取得できなくなります。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param scale_width: 横幅拡大率
    :type scale_width: float
    :param scale_height: 縦幅拡大率
    :type scale_height: float
    :param width_offset: 横移動(正の値で右、負の値で左)
    :type width_offset: int
    :param height_offset: 縦移動(正の値で上、負の値で下)
    :type height_offset: int
    :return: 変形後のフォントオブジェクト
    :rtype: TTFont
    """
    upm = font_obj['head'].unitsPerEm
    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()
    hmtx_table = font_obj['hmtx']

    # 中央寄せのための移動量を算出
    dx = ((upm * (1.0 - scale_width)) / 2) + width_offset
    dy = ((upm * (1.0 - scale_height)) / 2) + height_offset
    transformation = (scale_width, 0, 0, scale_height, dx, dy)

    # 既存のキャッシュをクリア
    if hasattr(font_obj, "_glyphSet"):
        del font_obj._glyphSet

    for name in glyph_names:
        old_glyph = glyph_set[name]
        # 元の幅とLSBを取得
        old_width, old_lsb = hmtx_table[name]

        # 新しい幅とLSBを計算（OTF/TTF共通で使用する）
        new_width = int(round(old_width * scale_width))
        new_lsb = int(round(old_lsb * scale_width + dx))

        # 輪郭(Outline)の変形
        if is_ttf(font_obj):
            # TTFの場合
            new_pen = TTGlyphPen(glyph_set)
            trans_pen = TransformPen(new_pen, transformation)
            old_glyph.draw(trans_pen)
            new_glyph = new_pen.glyph()
            new_glyph.recalcBounds(font_obj['glyf'])
            font_obj['glyf'][name] = new_glyph
        elif is_otf(font_obj):
            # OTF (CFF) の処理
            cff = font_obj['CFF '].cff if "CFF " in font_obj else font_obj['CFF2'].cff
            old_charstring = cff.topDictIndex[0].CharStrings[name]
            new_pen = T2CharStringPen(new_width, glyph_set)
            trans_pen = TransformPen(new_pen, transformation)
            old_glyph.draw(trans_pen)

            # 【ここが重要】新しいオブジェクトを代入せず、既存のプログラム(bytecode)だけを上書きする
            # これにより、private参照やCIDのFontDict割り当てが維持されます
            new_cs = new_pen.getCharString()
            old_charstring.program = new_cs.program
        else:
            raise ValueError(MSG_FONTTYPE_UNIDENT)

        # メトリクス(hmtx)の更新
        hmtx_table[name] = (new_width, new_lsb)

    if is_otf(font_obj):
        # BBox再計算
        cff = font_obj['CFF '].cff if "CFF " in font_obj else font_obj['CFF2'].cff
        cff.topDictIndex[0].recalcFontBBox()

    return font_obj


def set_metrics(font_obj: TTFont, ascent: int, descent: int) -> MetricsSetResult:
    """
    # 入力されたメトリクス値をフォント情報に設定する

    Descentは負の値にして下さい。
    Ascent,Descent及びその合算値であるUPMは8の倍数とする必要があります。1024が最適値です。
    この処理ではフォント情報の書き換えのみ行うため、もしUPMが変更となる場合はその倍率分を変形メソッドに依頼して下さい。
    UPMのみ変更しサイズ変更を行わなかった場合、SWF投入時に不具合が発生します。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param ascent: Ascent値。8の倍数にして下さい。
    :type ascent: int
    :param descent: Descent値。8の倍数にして下さい。
    :type descent: int
    :return: メトリクス設定結果
    :rtype: MetricsSetResult
    """

    # Ascent,Descentペアのチェック
    if ascent is not None and descent is None:
        raise ValueError(
            f"AscentとDescentは対で入力して下さい。: Ascent: {ascent}, Descent: {descent}"
        )
    if ascent is None and descent is not None:
        raise ValueError(
            f"AscentとDescentは対で入力して下さい。: Ascent: {ascent}, Descent: {descent}"
        )

    new_upm = ascent + abs(descent)

    # 8の倍数チェック
    if new_upm % 8 != 0 or ascent % 8 != 0 or descent % 8 != 0:
        raise ValueError(
            f"入力値が正しくありません。: Ascent({ascent}) + Descent({descent}) = UPM({new_upm}). "
            f"各数値は8の倍数にして下さい。Ascent=880,Descent=-144,UPM=1024が最適値です。"
        )

    old_upm = font_obj['head'].unitsPerEm
    need_scale_size = new_upm / old_upm

    # head テーブルの更新
    font_obj['head'].unitsPerEm = new_upm

    # 4. OS/2 テーブル (Windows 用)
    if "OS/2" in font_obj:
        os2 = font_obj['OS/2']

        # バージョンが古い（4未満）場合は、4に引き上げる
        if os2.version < 4:
            # バージョン 2 で追加された項目
            if not hasattr(os2, "sxHeight"):
                os2.sxHeight = 0
            if not hasattr(os2, "sCapHeight"):
                os2.sCapHeight = 0
            if not hasattr(os2, "usDefaultChar"):
                os2.usDefaultChar = 0
            if not hasattr(os2, "usBreakChar"):
                os2.usBreakChar = 32  # 半角スペース
            if not hasattr(os2, "usMaxContext"):
                os2.usMaxContext = 0
            os2.version = 4

        os2.sTypoAscender = ascent
        os2.sTypoDescender = descent
        os2.usWinAscent = abs(ascent)
        os2.usWinDescent = abs(descent)
        os2.sTypoLineGap = 0
        # OS/2のメトリクス設定を優先させるフラグ
        os2.fsSelection |= 1 << 7

    # hhea テーブル
    if "hhea" in font_obj:
        hhea = font_obj['hhea']
        hhea.ascent = ascent
        hhea.descender = descent
        hhea.lineGap = 0

    # post テーブル (下線の位置と太さ)
    if "post" in font_obj:
        post = font_obj['post']
        # UPM変更に合わせてスケールさせる
        if need_scale_size != 1.0:
            post.underlinePosition = int(
                round(post.underlinePosition * need_scale_size)
            )
            post.underlineThickness = int(
                round(post.underlineThickness * need_scale_size)
            )

    return MetricsSetResult(
        font_obj=font_obj,
        old_upm=old_upm,
        new_upm=new_upm,
        need_scale_size=need_scale_size,
    )


def anonymize_info(font_obj: TTFont, family_name: str = "Anonymous") -> TTFont:
    """
    # フォント情報を匿名化する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param family_name: フォントファミリー名。空白や記号類は使用できません。
    :type family_name: str
    :return: 匿名化後のフォントオブジェクト
    :rtype: TTFont
    """
    sub_family = "Regular"
    if family_name == "" or re.search(r"[^\w]", family_name):
        raise ValueError("フォントファミリ名に空白や記号類は使用できません。")
    ps_name = family_name + "-" + sub_family

    # nameテーブルの再構築
    name_table = font_obj['name']
    new_names = []

    # 必須のIDだけを絞り込んで再定義する
    for record in name_table.names:
        encoding = record.getEncoding()

        if record.nameID in [1, 16, 17]:  # Family Name
            record.string = family_name.encode(encoding)
        elif record.nameID in [2, 18]:  # Subfamily Name
            record.string = sub_family.encode(encoding)
        elif record.nameID == 3:  # Unique ID
            record.string = f"0.000;NONE;{ps_name}".encode(encoding)
        elif record.nameID == 4:  # Full Name
            record.string = f"{family_name} {sub_family}".encode(encoding)
        elif record.nameID == 5:  # Version
            record.string = "Version 0.000".encode(encoding)
        elif record.nameID == 6:  # PostScript Name
            record.string = ps_name.encode(encoding)
        else:
            # 著作権やURLなどは、空文字を入れるのではなく「リストに入れない」ことで削除
            continue

        new_names.append(record)

    name_table.names = new_names

    # headテーブルの更新
    head = font_obj['head']
    if head:
        # Mac epoch (1904) と Unix epoch (1970) の差分: 2,082,844,800秒
        now = int(time.time()) + 2082844800
        head.created = now
        head.modified = now

    # OS/2テーブルの更新
    os2 = font_obj['OS/2']
    if os2:
        os2.achVendID = "NONE"

    # OTFの内部情報も書き換える
    if is_otf(font_obj):
        cff = font_obj['CFF '].cff
        for font_name in cff.fontNames:
            top_dict = cff[font_name]
            top_dict.FullName = f"{family_name} {sub_family}"
            top_dict.FamilyName = family_name
            top_dict.Weight = sub_family

    return font_obj


def change_weight(font_obj: TTFont, weight_offset: int) -> TTFont:
    """
    # 文字の太さを変更する

    負荷が高く不安定な処理です。可能な限り公式が提供しているウェイトフォントを使用することをお勧めします。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param weight_offset: 太さ調整値。正の値で太く、負の値で細くなります。
    :type weight_offset: int
    :return: 変形後のフォントオブジェクト
    :rtype: TTFont
    """
    if weight_offset == 0:
        return font_obj

    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()
    actual_offset = -weight_offset

    # OTFの場合は CFF テーブルを直接取得
    cff = None
    char_strings = None
    if is_otf(font_obj):
        cff = font_obj['CFF '].cff if "CFF " in font_obj else font_obj['CFF2'].cff
        char_strings = cff.topDictIndex[0].CharStrings

    # OTFの場合はTTFと法線の向きが逆なので、TTFと調整量を逆にします。
    if is_otf(font_obj):
        actual_offset = weight_offset  # OTF用

    def get_normal(dx, dy):
        l = math.sqrt(dx * dx + dy * dy)
        return (dy / l, -dx / l) if l != 0 else (0, 0)

    for name in glyph_names:
        # OTF/TTF問わず、TTF形式のペンで座標を取り出す
        # これで計算可能な coordinates リストが手に入る
        temp_pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(temp_pen)
        temp_glyph = temp_pen.glyph()

        if temp_glyph.numberOfContours <= 0:
            continue

        # 肉付けロジック
        coords = list(temp_glyph.coordinates)
        new_coords = list(coords)
        start_idx = 0
        for end_idx in temp_glyph.endPtsOfContours:
            contour_indices = list(range(start_idx, end_idx + 1))
            n = len(contour_indices)
            if n >= 2:
                for i in range(n):
                    curr_idx = contour_indices[i]
                    prev_idx = contour_indices[(i - 1) % n]
                    next_idx = contour_indices[(i + 1) % n]
                    x0, y0 = coords[prev_idx]
                    x1, y1 = coords[curr_idx]
                    x2, y2 = coords[next_idx]
                    v1x, v1y = x1 - x0, y1 - y0
                    v2x, v2y = x2 - x1, y2 - y1
                    n1x, n1y = get_normal(v1x, v1y)
                    n2x, n2y = get_normal(v2x, v2y)
                    nx, ny = n1x + n2x, n1y + n2y
                    n_len = math.sqrt(nx * nx + ny * ny)
                    if n_len != 0:
                        new_coords[curr_idx] = (
                            round(
                                x1 + (nx / n_len) * actual_offset, 2
                            ),  # 小数点以下2桁程度に
                            round(y1 + (ny / n_len) * actual_offset, 2),
                        )
            start_idx = end_idx + 1

        temp_glyph.coordinates = type(temp_glyph.coordinates)(new_coords)

        # 書き戻し
        if is_ttf(font_obj):
            # TTFでも重なりを合体させて白抜けを防ぐ
            rec_pen = RecordingPen()
            temp_glyph.draw(rec_pen, font_obj['glyf'])

            path = Path()
            pen = path.getPen()
            rec_pen.replay(pen)

            try:
                path.simplify()
            except Exception as e:
                print(e)
                print(f"警告: グリフ '{name}' の簡略化に失敗したためスキップします。")

            tt_pen = TTGlyphPen(glyph_set)
            path.draw(tt_pen)
            font_obj['glyf'][name] = tt_pen.glyph()
        elif is_otf(font_obj):
            # 肉付け後のパスを RecordingPen に記録
            rec_pen = RecordingPen()
            temp_glyph.draw(rec_pen, glyfTable={})

            # RecordingPen の内容を Path オブジェクトに流し込む
            path = Path()
            pen = path.getPen()
            rec_pen.replay(pen)

            # パス簡略化
            try:
                path.simplify()
            except Exception as e:
                # simplifyに失敗しても止まらないようにする
                print(e)
                print(f"警告: グリフ '{name}' の簡略化に失敗したためスキップします。")

            # T2CharStringPen に書き戻す
            old_width = font_obj['hmtx'][name][0]
            new_pen = T2CharStringPen(old_width, glyph_set)
            path.draw(new_pen)  # Pathオブジェクトはそのまま描画可能

            char_strings[name].setProgram(new_pen.getCharString().program)

    # 全体の境界線を再計算
    if is_otf(font_obj):
        cff.topDictIndex[0].recalcFontBBox()

    return font_obj
