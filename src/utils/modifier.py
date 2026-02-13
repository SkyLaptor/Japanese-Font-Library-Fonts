import argparse
import math
import re
import sys
import time

from fontTools.misc.transform import Transform
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from pathops import Path

from utils import (
    is_cff,
    is_cff2,
    reload_font,
    save_font,
)
from utils.inspector import get_average_size, get_info


def main():
    parser = argparse.ArgumentParser(
        description="フォントへ各種更新を施すためのツールボックス"
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
        "-b",
        "--base_font_file",
        type=str,
        help="ベースとなるフォントファイル",
    )
    parser.add_argument(
        "-o",
        "--output_font_file",
        type=str,
        help="ファイルの書き出し先",
    )
    parser.add_argument(
        "--scale_width",
        type=float,
        default=1.0,
        help="横方向の拡大縮小率 デフォルト: 1.0",
    )

    parser.add_argument(
        "--scale_height",
        type=float,
        default=1.0,
        help="縦方向の拡大縮小率 デフォルト: 1.0",
    )
    parser.add_argument(
        "--offset_width",
        type=int,
        default=0,
        help="横方向の移動量 デフォルト: 0",
    )
    parser.add_argument(
        "--offset_height",
        type=int,
        default=0,
        help="縦方向の移動量 デフォルト: 0",
    )
    parser.add_argument(
        "--offset_weight",
        type=int,
        default=0,
        help="文字の太さ調整量 デフォルト: 0",
    )
    parser.add_argument(
        "--family_name",
        type=str,
        help="フォントファミリー名",
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


def action_harmonize_font_metrics(
    input_font_file,
    output_font_file,
    scale_width,
    scale_height,
    offset_width,
    offset_height,
    base_font_file,
    **_,
):
    font_obj = TTFont(input_font_file)
    base_font_obj = TTFont(base_font_file)
    # print(f"アウトライン形式: {get_outline_format(font_obj)}")
    # print("カスタム拡大縮小率: 横:x{scale_width:.3f}, 縦:x{scale_height:.3f} ※最終的な倍率ではありません。")
    # print(f"移動量: 横:{offset_width}units, 縦:{offset_height}units")
    # print("処理前の操作対象フォント情報")
    # print(get_info(font_obj=font_obj))
    # print("ベースフォント情報")
    # print(get_info(font_obj=base_font_obj))
    font_obj = harmonize_font_metrics(
        src_font_obj=font_obj,
        scale_width=scale_width,
        scale_height=scale_height,
        offset_width=offset_width,
        offset_height=offset_height,
        base_font_obj=base_font_obj,
    )
    # print("処理後の操作対象フォント情報")
    # print(get_info(font_obj))
    output_font_file = save_font(
        font_obj=font_obj,
        input=input_font_file,
        output=output_font_file,
        suffix="_harmonized",
    )
    print(f"フォントを保存しました: {output_font_file}")


def harmonize_font_metrics(
    src_font_obj: TTFont,
    base_font_obj: TTFont,
    scale_width: float,
    scale_height: float,
    offset_width: int,
    offset_height: int,
) -> TTFont:
    """
    渡されたベースフォント及びカスタムパラメーターに従いフォントメトリクスを更新する

    :param src_font_obj: 処理対象のフォント
    :type src_font_obj: TTFont
    :param base_font_obj: ベースとなるフォント
    :type base_font_obj: TTFont
    :param scale_width: 横方向の拡大率
    :type scale_width: float
    :param scale_height: 縦方向の拡大率
    :type scale_height: float
    :param offset_width: 横方向オフセット
    :type offset_width: int
    :param offset_height: 縦方向オフセット
    :type offset_height: int
    :return: 処理後のフォント
    :rtype: TTFont
    """
    # CFF/CFF2の場合は非対応
    if is_cff(font_obj=src_font_obj) or is_cff2(font_obj=src_font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    # ベースフォントとフォントのグリフサイズ平均を取得し、どれだけ拡大縮小すればいいか算出します。
    # 拡大縮小率は縦幅を基準とします。（縦に伸びるとUI破綻を起こしやすいが、横は伸びてもそこまで影響なし。）
    src_avg_result = get_average_size(font_obj=src_font_obj)
    base_avg_result = get_average_size(font_obj=base_font_obj)
    # print("DEBUG:元フォント")
    # print(src_avg_result)
    # print("DEBUG:ベースフォント")
    # print(base_avg_result)
    scale_height_calc = base_avg_result.avg_h / src_avg_result.avg_h
    scale_width_calc = scale_height
    # print(
    #     f"DEBUG: 平均値比較により算出した拡大縮小率: 横:x{scale_width_calc:.3f}, 縦:x{scale_height_calc:.3f}"
    # )

    # 手動での拡大縮小率を適用する
    scale_width = scale_width_calc * scale_width
    scale_height = scale_height_calc * scale_height
    # print(
    #     f"DEBUG: カスタム拡大縮小率を適用後の拡大縮小率: 横:x{scale_width:.3f}, 縦:x{scale_height:.3f}"
    # )

    # UPMをベースフォントに合わせる
    src_upm = src_font_obj.get('head').unitsPerEm
    base_upm = base_font_obj.get('head').unitsPerEm
    if src_upm != base_upm:
        # UPMの変更
        src_font_obj.get('head').unitsPerEm = base_upm
        # 拡大縮小率の算出
        scale_width = scale_width * base_upm / src_upm
        scale_height = scale_height * base_upm / src_upm
        # print(f"DEBUG: UPMが変更されます。{base_upm}")
        # print(
        #     f"DEBUG: UPM変更に伴い、拡大率も変更されました: 横:x{scale_width:.3f}, 縦:x{scale_height:.3f}"
        # )

    # メトリクス各種をベースフォントと同じにする
    os2 = src_font_obj.get('OS/2')
    base_os2 = base_font_obj.get('OS/2')
    os2.usWinAscent = base_os2.usWinAscent
    os2.usWinDescent = base_os2.usWinDescent
    os2.sTypoAscender = base_os2.sTypoAscender
    os2.sTypoDescender = base_os2.sTypoDescender
    os2.sTypoLineGap = base_os2.sTypoLineGap
    hhea = src_font_obj.get('hhea')
    base_hhea = base_font_obj.get('hhea')
    hhea.ascent = base_hhea.ascent
    hhea.descent = base_hhea.descent
    hhea.lineGap = base_hhea.lineGap

    # 奇跡的に拡大縮小率及びオフセット値が全て変更なしなら変形処理をスキップする。
    if (
        scale_width == 1.0
        and scale_height == 1.0
        and offset_width == 0
        and offset_height == 0
    ):
        # print("変形の必要が無いため、処理をスキップします。")
        return reload_font(font_obj=src_font_obj)

    glyph_set = src_font_obj.getGlyphSet()
    glyph_order = src_font_obj.getGlyphOrder()

    # 変換行列の作成（原点を中心に拡大/縮小）
    t = (
        Transform()
        .scale(scale_width, scale_height)
        .translate(offset_width, offset_height)
    )

    # 変換
    glyf_table = src_font_obj['glyf']
    for name in glyph_order:
        if name not in glyf_table:
            continue

        # TTGlyphPenを初期化
        # (glyphSetを渡すと複合グリフを適切に分解してスケーリングできます)
        tt_pen = TTGlyphPen(glyph_set)

        # 変換行列を噛ませたTransformPenを作成
        trans_pen = TransformPen(tt_pen, t)

        # 既存のグリフをTransformPen経由で描画（これで変形しながらtt_penに録画される）
        glyph_set[name].draw(trans_pen)

        # 正しいメソッド名は glyph() です
        glyf_table[name] = tt_pen.glyph()

    # hmtx (水平メトリクス) の調整
    # これをしないと、絵だけ大きくなって文字同士が重なる
    if 'hmtx' in src_font_obj:
        hmtx = src_font_obj['hmtx']
        for name in hmtx.metrics:
            advance_width, lsb = hmtx.metrics[name]
            # 送り幅と左余白をスケーリング
            hmtx.metrics[name] = (
                int(round(advance_width * scale_width)),
                int(round(lsb * scale_width)) + offset_width,
            )

    return reload_font(src_font_obj)


def action_anonymize_info(input_font_file, output_font_file, family_name, **_):
    font_obj = TTFont(input_font_file)
    print("匿名化前のフォント情報")
    print(get_info(font_obj))
    font_obj = anonymize_info(font_obj=font_obj, family_name=family_name)
    print("匿名化後のフォント情報")
    print(get_info(font_obj))
    output_font_file = save_font(
        font_obj=font_obj,
        input=input_font_file,
        output=output_font_file,
        suffix="_anonymized",
    )
    print(f"フォントを保存しました: {output_font_file}")


def anonymize_info(font_obj: TTFont, family_name: str = "Anonymous") -> TTFont:
    """
    フォント情報を匿名化する

    :param font_obj: フォント
    :type font_obj: TTFont
    :param family_name: フォントファミリー名。空白や記号類は使用できません。 デフォルト: Anonymous
    :type family_name: str
    :return: 匿名化後のフォント
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
    if is_cff(font_obj):
        cff = font_obj['CFF '].cff
        for font_name in cff.fontNames:
            top_dict = cff[font_name]
            top_dict.FullName = f"{family_name} {sub_family}"
            top_dict.FamilyName = family_name
            top_dict.Weight = sub_family

    return reload_font(font_obj)


def action_change_weight(input_font_file, output_font_file, offset_weight, **_):
    font_obj = TTFont(input_font_file)
    font_obj = change_weight(font_obj=font_obj, offset_weight=offset_weight)
    output_font_file = save_font(
        font_obj=font_obj,
        input=input_font_file,
        output=output_font_file,
        suffix="_weight_changed",
    )
    print(f"フォントを保存しました: {output_font_file}")


def change_weight(font_obj: TTFont, offset_weight: int) -> TTFont:
    """
    文字の太さを変更する

    負荷が高く不安定な処理です。可能な限り公式が提供しているウェイトフォントを使用することをお勧めします。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param offset_weight: 太さ調整値。正の値で太く、負の値で細くなります。
    :type offset_weight: int
    :return: 変形後のフォントオブジェクト
    :rtype: TTFont
    """

    # CFF/CFF2の場合は非対応
    if is_cff(font_obj=font_obj) or is_cff2(font_obj=font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    if offset_weight == 0:
        return reload_font(font_obj=font_obj)

    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()
    actual_offset = -offset_weight

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

        # 重なりを合体させて白抜けを防ぐ
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

    return reload_font(font_obj)


ACTION_MAP = {
    "harmonize_font_metrics": action_harmonize_font_metrics,
    "anonymize_info": action_anonymize_info,
    "change_weight": action_change_weight,
}

if __name__ == "__main__":
    main()
