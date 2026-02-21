import argparse
import sys
from dataclasses import dataclass
from typing import Optional

from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from utils.common.dprint import dprint
from utils.common.reload_font import reload_font
from utils.common.save_font import save_font
from utils.inspector.get_average_size import get_average_size
from utils.inspector.get_info import get_info


@dataclass
class Result:
    font_obj: Optional[TTFont] = None
    is_upm_change: Optional[bool] = None
    final_scale_width: Optional[float] = None
    final_scale_height: Optional[float] = None

    def __str__(self):
        output = "[フォントメトリクス更新結果]\n"
        output += f"UPMの変更: {self.is_upm_change}\n"
        output += f"最終的な横倍率: x{self.final_scale_width}\n"
        output += f"最終的な縦倍率: x{self.final_scale_height}\n"
        return output


def main():
    parser = argparse.ArgumentParser(
        description="渡されたベースフォント及びカスタムパラメーターに従いフォントメトリクスを更新する"
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
        help="処理後のフォントの書き出し先",
    )
    parser.add_argument(
        "-b",
        "--base_path",
        type=str,
        help="ベースとなるフォントファイルのパス",
    )
    parser.add_argument(
        "--scale_width",
        type=float,
        default=1.0,
        help="横幅の拡大率",
    )
    parser.add_argument(
        "--scale_height",
        type=float,
        default=1.0,
        help="縦幅の拡大率",
    )
    parser.add_argument(
        "--offset_width",
        type=int,
        default=0,
        help="横方向の移動量",
    )
    parser.add_argument(
        "--offset_height",
        type=int,
        default=0,
        help="縦方向の移動量",
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

    action_harmonize_font_metrics(**vars(args))


def action_harmonize_font_metrics(
    input_path: str,
    output_path: str,
    base_path: str,
    scale_width: float,
    scale_height: float,
    offset_width: int,
    offset_height: int,
    debug: bool = False,
    **_,
):
    with TTFont(base_path) as base_font_obj, TTFont(input_path) as input_font_obj:
        dprint("=== 変形前のターゲットフォントの情報"), debug
        input_font_info = get_info(input_font_obj, debug)
        dprint(str(input_font_info), debug)

        result = harmonize_font_metrics(
            target_font_obj=input_font_obj,
            base_font_obj=base_font_obj,
            scale_width_manual=scale_width,
            scale_height_manual=scale_height,
            offset_width=offset_width,
            offset_height=offset_height,
            debug=debug,
        )
        harmonized_input_font_obj = result.font_obj

        print("=== 変形後のターゲットフォントの情報")
        harmonized_input_font_info = get_info(harmonized_input_font_obj)
        print(str(harmonized_input_font_info))

        scale_for_upm = 1.0
        if result.is_upm_change:
            scale_for_upm = (
                harmonized_input_font_info.upm / input_font_info.upm
            )  # 例: 1000 → 1024になったのであれば、1024 / 1000 = 1.024になるはず。
            print(
                f"ターゲットフォントのUPMが変更されました: 元:{input_font_info.upm}, 現在:{harmonized_input_font_info.upm}"
            )

        print(
            f"UPMによる拡大縮小率: x{scale_for_upm}, 手動横拡大縮小率: x{scale_width:.3f}, 手動縦拡大縮小率: x{scale_height}"
        )
        print(
            f"実際に処理された拡大縮小率: 横:x{result.final_scale_width:.3f}, 縦:x{result.final_scale_height:.3f}"
        )
        harmonized_input_avg_size_result = get_average_size(harmonized_input_font_obj)
        print(
            f"処理後のターゲットフォントのグリフ平均サイズ: 横: {harmonized_input_avg_size_result.avg_w:.1f}, 縦: {harmonized_input_avg_size_result.avg_h:.1f}"
        )

        if output_path is not None:
            saved_output_path = save_font(
                font_obj=harmonized_input_font_obj,
                input_path=input_path,
                output_path=output_path,
                suffix="_harmonized",
            )
            print(f"フォントを保存しました: {saved_output_path}")


def harmonize_font_metrics(
    target_font_obj: TTFont,
    base_font_obj: TTFont,
    scale_width_manual: float = 1.0,
    scale_height_manual: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    debug: bool = False,
) -> Result:
    """
    渡されたベースフォント及びカスタムパラメーターに従いフォントメトリクスを更新する

    :param target_font_obj: ターゲットフォント
    :type target_font_obj: TTFont
    :param base_font_obj: ベースフォント
    :type base_font_obj: TTFont
    :param scale_width_manual: 横方向の拡大率（手動）
    :type scale_width_manual: float
    :param scale_height_manual: 縦方向の拡大率（手動）
    :type scale_height_manual: float
    :param offset_width: 横方向オフセット量
    :type offset_width: int
    :param offset_height: 縦方向オフセット量
    :type offset_height: int
    :param debug: デバッグモード
    :type debug: bool
    :return: 処理結果
    :rtype: Result
    """
    # CFF/CFF2の場合は非対応
    if 'CFF ' in target_font_obj or 'CFF2' in target_font_obj:
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    base_font_info = get_info(base_font_obj, debug)
    target_font_info = get_info(target_font_obj, debug)

    # デバッグ表示
    # dprint("=== ベースフォントの情報", debug)
    # dprint(base_font_info, debug)
    # dprint("=== ターゲットフォントの情報", debug)
    # dprint(target_font_info, debug)

    # ベースフォントとターゲットフォントのグリフサイズ平均を取得し、どれだけ拡大縮小すればいいか算出します。
    base_avg_size_result = get_average_size(base_font_obj)
    target_avg_size_result = get_average_size(target_font_obj)

    dprint(
        f"ベースフォントのグリフ平均サイズ: 横: {base_avg_size_result.avg_w:.1f}units, 縦: {base_avg_size_result.avg_h:.1f}units",
        debug,
    )
    dprint(
        f"ターゲットフォントのグリフ平均サイズ: 横: {target_avg_size_result.avg_w:.1f}units, 縦: {target_avg_size_result.avg_h:.1f}units",
        debug,
    )

    # ターゲットフォントの平均高さが 0 の場合、計算不能なので 1.0 (等倍) に強制する
    if target_avg_size_result.avg_h == 0:
        print(
            f"ターゲットフォントの平均高さが {target_avg_size_result.avg_h:.1f} です。拡大率は 1.0 として計算します。",
        )
        scale_height_pure = 1.0
    else:
        scale_height_pure = base_avg_size_result.avg_h / target_avg_size_result.avg_h

    # 横方向も同様にガード（もし get_average_size の仕様で avg_w も 0 になり得るなら）
    if target_avg_size_result.avg_w == 0:
        print(
            f"ターゲットフォントの平均幅が {target_avg_size_result.avg_w:.1f} です。拡大率は 1.0 として計算します。",
        )
        scale_width_pure = scale_height_pure  # 高さの倍率を流用
    else:
        # もともとこのロジックは縦を基準にしているので、
        # 基本的には上の scale_height_pure を使う形でOK
        scale_width_pure = scale_height_pure

    # 横方向の拡大縮小率は縦方向を基準とします。（縦に伸びるとUI破綻を起こすが、横は伸びてもそこまで影響なし。）
    scale_width_pure = scale_height_pure
    dprint(
        f"平均サイズ比較により算出した拡大縮小率: 横:x{scale_width_pure:.3f}, 縦:x{scale_height_pure:.3f}",
        debug,
    )

    # UPMをベースフォントに合わせる
    base_upm = base_font_info.upm
    target_upm = target_font_info.upm

    scale_for_upm = base_upm / target_upm  # 例: 1024 / 1000 = x1.024 float型
    is_upm_change = False
    if scale_for_upm != 1.0:
        # UPMの差異によって倍率を変更する必要がありますが、ここでは一旦情報のみ書き換えます。
        target_font_obj['head'].unitsPerEm = base_upm
        dprint(f"UPMを変更: {target_upm} -> {base_upm}", debug)
        is_upm_change = True

    # ターゲットフォントのメトリクス情報をベースフォントと同じように書き換えます。
    os2 = target_font_obj.get('OS/2')
    base_os2 = base_font_obj.get('OS/2')
    os2.usWinAscent = base_os2.usWinAscent
    os2.usWinDescent = base_os2.usWinDescent
    os2.sTypoAscender = base_os2.sTypoAscender
    os2.sTypoDescender = base_os2.sTypoDescender
    os2.sTypoLineGap = base_os2.sTypoLineGap
    hhea = target_font_obj.get('hhea')
    base_hhea = base_font_obj.get('hhea')
    hhea.ascent = base_hhea.ascent
    hhea.descent = base_hhea.descent
    hhea.lineGap = base_hhea.lineGap

    # サイズ比較倍率、UPM倍率及び手動倍率をもって最終的な拡大縮小率を算出する
    # 例: サイズ比較の結果 x0.9、UPM変更の結果 x1.024、手動横倍率が x0.64(長体にしたいという意思)だった場合、
    # 0.9 / 1.024 * 0.64 = x0.563
    final_scale_width = scale_width_pure / scale_for_upm * scale_width_manual
    # 例: サイズ比較の結果 x0.9、UPM変更の結果 x1.024、手動縦倍率が x1.0(普通変更する必要なし)だった場合、
    # 0.9 / 1.024 * 1.00 = x0.879
    final_scale_height = scale_height_pure / scale_for_upm * scale_height_manual

    dprint(
        f"サイズ比較倍率、UPM倍率、手動倍率による最終拡大縮小率: 横:x{final_scale_width:.3f}, 縦:x{final_scale_height:.3f}",
        debug,
    )

    # 奇跡的に拡大縮小率及びオフセット値が全て変更なしなら変形処理をスキップする。
    if (
        final_scale_width == 1.0
        and final_scale_height == 1.0
        and offset_width == 0
        and offset_height == 0
    ):
        dprint("変形の必要が無いため、処理をスキップしました。", debug)
        return Result(
            font_obj=reload_font(target_font_obj),
            is_upm_change=is_upm_change,
            final_scale_width=final_scale_width,
            final_scale_height=final_scale_height,
        )

    glyph_set = target_font_obj.getGlyphSet()
    glyph_order = target_font_obj.getGlyphOrder()

    # 変換行列の作成（原点を中心に拡大/縮小）
    t = Transform(
        final_scale_width, 0, 0, final_scale_height, offset_width, offset_height
    )

    # # 変換
    # glyf_table = target_font_obj['glyf']
    # for name in glyph_order:
    #     if name not in glyf_table:
    #         continue

    #     # TTGlyphPenを初期化
    #     # (glyphSetを渡すと複合グリフを適切に分解してスケーリングできます)
    #     tt_pen = TTGlyphPen(glyph_set)

    #     # 変換行列を噛ませたTransformPenを作成
    #     trans_pen = TransformPen(tt_pen, t)

    #     # 既存のグリフをTransformPen経由で描画（これで変形しながらtt_penに録画される）
    #     glyph_set[name].draw(trans_pen)
    #     glyf_table[name] = tt_pen.glyph()

    # # hmtx (水平メトリクス) の調整
    # # これをしないと、グリフだけ大きくなって文字同士が重なってしまう
    # if 'hmtx' in target_font_obj:
    #     hmtx = target_font_obj['hmtx']
    #     for name in hmtx.metrics:
    #         advance_width, lsb = hmtx.metrics[name]
    #         # 送り幅と左余白をスケーリング
    #         hmtx.metrics[name] = (
    #             int(round(advance_width * final_scale_width)),
    #             int(round(lsb * final_scale_width)) + offset_width,
    #         )

    # 変換
    glyf_table = target_font_obj['glyf']
    for name in glyph_order:
        if name not in glyf_table:
            continue

        # TTGlyphPenを初期化
        tt_pen = TTGlyphPen(glyph_set)

        # 変換行列を噛ませたTransformPenを作成
        trans_pen = TransformPen(tt_pen, t)

        # 描画（変形実行）
        glyph_set[name].draw(trans_pen)

        # --- 修正: __setitem__ を避けて直接代入 ---
        glyf_table.glyphs[name] = tt_pen.glyph()

    # hmtx (水平メトリクス) の調整
    if 'hmtx' in target_font_obj:
        hmtx = target_font_obj['hmtx']
        for name in hmtx.metrics:
            advance_width, lsb = hmtx.metrics[name]
            # 送り幅と左余白をスケーリング
            # offset_width（移動量）も考慮
            new_width = int(round(advance_width * final_scale_width))
            new_lsb = int(round(lsb * final_scale_width)) + offset_width
            hmtx.metrics[name] = (new_width, new_lsb)

    # --- 境界ボックスの再計算 (これがないと表示がバグる場合があります) ---
    for glyph in glyf_table.glyphs.values():
        if hasattr(glyph, "recalcBounds"):
            glyph.recalcBounds(glyf_table)

    return Result(
        font_obj=reload_font(target_font_obj),
        is_upm_change=is_upm_change,
        final_scale_width=final_scale_width,
        final_scale_height=final_scale_height,
    )


if __name__ == "__main__":
    main()
