# Dependencies: FFDec=False, FontForge=False
from collections.abc import Mapping

from fontTools.misc.transform import Transform
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from const import NORMALIZED_UPM
from core.font_processor import reopen_font
from models.harmonize_font_metrics_result import HarmonizeFontMetricsResult
from modules.get_average_size import get_average_size
from modules.get_info import get_info
from utils.dprint import dprint
from utils.file_io import save_font

LOG_PREFIX = "[harmonize_font_metrics]"


def _is_cff_font(font_obj: TTFont) -> bool:
    return 'CFF ' in font_obj or 'CFF2' in font_obj


def _build_consistent_base_metrics_override(
    base_font_obj: TTFont,
    target_upm: int,
) -> dict[str, dict[str, int]]:
    base_upm = int(base_font_obj['head'].unitsPerEm)
    scale = 1.0
    if base_upm > 0:
        scale = float(target_upm) / float(base_upm)

    os2_table = base_font_obj.get('OS/2')
    hhea_table = base_font_obj.get('hhea')
    post_table = base_font_obj.get('post')

    ascent: int | None = None
    descent: int | None = None
    line_gap: int | None = None

    if os2_table is not None:
        ascent = int(round(int(os2_table.sTypoAscender) * scale))
        descent = int(round(int(os2_table.sTypoDescender) * scale))
        line_gap = int(round(int(os2_table.sTypoLineGap) * scale))
    elif hhea_table is not None:
        ascent = int(round(int(hhea_table.ascent) * scale))
        descent = int(round(int(hhea_table.descent) * scale))
        line_gap = int(round(int(hhea_table.lineGap) * scale))

    metrics_override: dict[str, dict[str, int]] = {}
    if ascent is not None and descent is not None and line_gap is not None:
        metrics_override["os2"] = {
            "usWinAscent": ascent,
            "usWinDescent": abs(descent),
            "sTypoAscender": ascent,
            "sTypoDescender": descent,
            "sTypoLineGap": line_gap,
        }
        metrics_override["hhea"] = {
            "ascent": ascent,
            "descent": descent,
            "lineGap": line_gap,
        }

    if post_table is not None:
        metrics_override["post"] = {
            "underlinePosition": int(round(int(post_table.underlinePosition) * scale)),
            "underlineThickness": int(
                round(int(post_table.underlineThickness) * scale)
            ),
        }

    return metrics_override


def _apply_metrics_override(
    target_font_obj: TTFont, metrics_override: Mapping[str, object] | None
) -> None:
    if not metrics_override:
        return

    os2_table = target_font_obj.get('OS/2')
    if os2_table is not None:
        os2_values = metrics_override.get("os2")
        if isinstance(os2_values, Mapping):
            for key in (
                "usWinAscent",
                "usWinDescent",
                "sTypoAscender",
                "sTypoDescender",
                "sTypoLineGap",
            ):
                if key in os2_values:
                    setattr(os2_table, key, int(os2_values[key]))

        for key in (
            "usWinAscent",
            "usWinDescent",
            "sTypoAscender",
            "sTypoDescender",
            "sTypoLineGap",
        ):
            if key in metrics_override:
                setattr(os2_table, key, int(metrics_override[key]))

    hhea_table = target_font_obj.get('hhea')
    if hhea_table is not None:
        hhea_values = metrics_override.get("hhea")
        if isinstance(hhea_values, Mapping):
            for key in ("ascent", "descent", "lineGap"):
                if key in hhea_values:
                    setattr(hhea_table, key, int(hhea_values[key]))

        for key in ("ascent", "descent", "lineGap"):
            if key in metrics_override:
                setattr(hhea_table, key, int(metrics_override[key]))

    post_table = target_font_obj.get('post')
    if post_table is not None:
        post_values = metrics_override.get("post")
        if isinstance(post_values, Mapping):
            for key in ("underlinePosition", "underlineThickness"):
                if key in post_values:
                    setattr(post_table, key, int(post_values[key]))

        for key in ("underlinePosition", "underlineThickness"):
            if key in metrics_override:
                setattr(post_table, key, int(metrics_override[key]))


def _derive_upm_from_metrics_override(
    metrics_override: Mapping[str, object] | None,
) -> int | None:
    if not metrics_override:
        return None

    ascent: int | None = None
    descent: int | None = None

    hhea_values = metrics_override.get("hhea")
    if isinstance(hhea_values, Mapping):
        if "ascent" in hhea_values and "descent" in hhea_values:
            ascent = int(hhea_values["ascent"])
            descent = int(hhea_values["descent"])

    if ascent is None or descent is None:
        if "ascent" in metrics_override and "descent" in metrics_override:
            ascent = int(metrics_override["ascent"])
            descent = int(metrics_override["descent"])

    if ascent is None or descent is None:
        os2_values = metrics_override.get("os2")
        if isinstance(os2_values, Mapping):
            if "sTypoAscender" in os2_values and "sTypoDescender" in os2_values:
                ascent = int(os2_values["sTypoAscender"])
                descent = int(os2_values["sTypoDescender"])

    if ascent is None or descent is None:
        return None

    derived_upm = int(ascent) + abs(int(descent))
    if derived_upm <= 0:
        return None
    return derived_upm


def apply_font_transform(
    target_font_obj: TTFont,
    scale_x: float,
    scale_y: float,
    offset_x: int,
    offset_y: int,
    new_upm: int | None = None,
    metrics_override: Mapping[str, object] | None = None,
) -> TTFont:
    if _is_cff_font(target_font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    if new_upm is not None:
        target_font_obj['head'].unitsPerEm = int(new_upm)

    _apply_metrics_override(target_font_obj, metrics_override)

    glyph_set = target_font_obj.getGlyphSet()
    glyph_order = target_font_obj.getGlyphOrder()

    transform = Transform(scale_x, 0, 0, scale_y, offset_x, offset_y)
    glyf_table = target_font_obj['glyf']

    for name in glyph_order:
        if name not in glyf_table:
            continue

        tt_pen = TTGlyphPen(glyph_set)
        trans_pen = TransformPen(tt_pen, transform)
        glyph_set[name].draw(trans_pen)
        glyf_table.glyphs[name] = tt_pen.glyph()

    if 'hmtx' in target_font_obj:
        hmtx = target_font_obj['hmtx']
        for name in hmtx.metrics:
            advance_width, lsb = hmtx.metrics[name]
            new_width = int(round(advance_width * scale_x))
            new_lsb = int(round(lsb * scale_x)) + offset_x
            hmtx.metrics[name] = (new_width, new_lsb)

    for glyph in glyf_table.glyphs.values():
        if hasattr(glyph, "recalcBounds"):
            glyph.recalcBounds(glyf_table)

    return reopen_font(target_font_obj)


def action_harmonize_font_metrics(
    input_path: str,
    output_path: str,
    base_path: str | None,
    scale_width: float,
    scale_height: float,
    offset_width: int,
    offset_height: int,
    mode: str = "base",
    new_upm: int | None = None,
    metrics_override: Mapping[str, object] | None = None,
    debug: bool = False,
    **_,
):
    with TTFont(input_path) as input_font_obj:
        dprint(f"{LOG_PREFIX}[before] 変形前のターゲットフォントの情報", debug)
        input_font_info = get_info(input_font_obj, debug)
        dprint(str(input_font_info), debug)

        if mode == "manual":
            derived_upm = _derive_upm_from_metrics_override(metrics_override)
            effective_upm = int(new_upm) if new_upm is not None else derived_upm

            harmonized_input_font_obj = apply_font_transform(
                target_font_obj=input_font_obj,
                scale_x=scale_width,
                scale_y=scale_height,
                offset_x=offset_width,
                offset_y=offset_height,
                new_upm=effective_upm,
                metrics_override=metrics_override,
            )
            result = HarmonizeFontMetricsResult(
                font_obj=harmonized_input_font_obj,
                is_upm_change=(
                    effective_upm is not None
                    and int(effective_upm) != int(input_font_info.upm)
                ),
                final_scale_width=scale_width,
                final_scale_height=scale_height,
            )
        else:
            if not base_path:
                raise ValueError("ベース基準モードでは base_path が必要です。")

            with TTFont(base_path) as base_font_obj:
                result = harmonize_with_base(
                    target_font_obj=input_font_obj,
                    base_font_obj=base_font_obj,
                    scale_width_manual=scale_width,
                    scale_height_manual=scale_height,
                    offset_width=offset_width,
                    offset_height=offset_height,
                    debug=debug,
                )
                harmonized_input_font_obj = result.font_obj

        print(f"{LOG_PREFIX}[after] 変形後のターゲットフォントの情報")
        harmonized_input_font_info = get_info(harmonized_input_font_obj)
        print(str(harmonized_input_font_info))

        scale_for_upm = 1.0
        if result.is_upm_change:
            scale_for_upm = harmonized_input_font_info.upm / input_font_info.upm
            print(
                f"{LOG_PREFIX}[upm] ターゲットフォントのUPMが変更されました: 元:{input_font_info.upm}, 現在:{harmonized_input_font_info.upm}"
            )

        print(
            f"{LOG_PREFIX}[scale] UPMによる拡大縮小率: x{scale_for_upm}, 手動横拡大縮小率: x{scale_width:.3f}, 手動縦拡大縮小率: x{scale_height}"
        )
        print(
            f"{LOG_PREFIX}[scale] 実際に処理された拡大縮小率: 横:x{result.final_scale_width:.3f}, 縦:x{result.final_scale_height:.3f}"
        )
        harmonized_input_avg_size_result = get_average_size(harmonized_input_font_obj)
        print(
            f"{LOG_PREFIX}[avg] 処理後のターゲットフォントのグリフ平均サイズ: 横: {harmonized_input_avg_size_result.avg_w:.1f}, 縦: {harmonized_input_avg_size_result.avg_h:.1f}"
        )

        if output_path is not None:
            saved_output_path = save_font(
                font_obj=harmonized_input_font_obj,
                input_path=input_path,
                output_path=output_path,
                suffix="_harmonized",
            )
            print(f"{LOG_PREFIX}[save] フォントを保存しました: {saved_output_path}")


def harmonize_with_base(
    target_font_obj: TTFont,
    base_font_obj: TTFont,
    scale_width_manual: float = 1.0,
    scale_height_manual: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    debug: bool = False,
) -> HarmonizeFontMetricsResult:
    if _is_cff_font(target_font_obj) or _is_cff_font(base_font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    base_font_info = get_info(base_font_obj, debug)
    target_font_info = get_info(target_font_obj, debug)

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

    if target_avg_size_result.avg_h == 0:
        print(
            f"ターゲットフォントの平均高さが {target_avg_size_result.avg_h:.1f} です。拡大率は 1.0 として計算します。",
        )
        scale_height_pure = 1.0
    else:
        scale_height_pure = base_avg_size_result.avg_h / target_avg_size_result.avg_h

    if target_avg_size_result.avg_w == 0:
        print(
            f"ターゲットフォントの平均幅が {target_avg_size_result.avg_w:.1f} です。拡大率は 1.0 として計算します。",
        )
        scale_width_pure = 1.0
    else:
        scale_width_pure = base_avg_size_result.avg_w / target_avg_size_result.avg_w

    dprint(
        f"自動拡大率(平均サイズ比較): 横:x{scale_width_pure:.3f}, 縦:x{scale_height_pure:.3f}",
        debug,
    )
    dprint(
        f"手動拡大率: 横:x{scale_width_manual:.3f}, 縦:x{scale_height_manual:.3f}",
        debug,
    )

    base_upm = base_font_info.upm
    target_upm = target_font_info.upm

    new_upm = NORMALIZED_UPM
    scale_for_upm = new_upm / target_upm
    is_upm_change = int(target_upm) != int(new_upm)
    if is_upm_change:
        dprint(f"UPMを変更: {target_upm} -> {new_upm}", debug)

    metrics_override = _build_consistent_base_metrics_override(
        base_font_obj=base_font_obj,
        target_upm=int(new_upm),
    )
    dprint(
        f"ベースメトリクスをUPM{NORMALIZED_UPM}へ正規化して適用します。",
        debug,
    )

    final_scale_width = scale_width_pure / scale_for_upm * scale_width_manual
    final_scale_height = scale_height_pure / scale_for_upm * scale_height_manual

    dprint(
        f"UPM倍率: x{scale_for_upm:.3f}",
        debug,
    )
    dprint(
        f"最終拡大縮小率: 横:x{final_scale_width:.3f}, 縦:x{final_scale_height:.3f}",
        debug,
    )

    if (
        final_scale_width == 1.0
        and final_scale_height == 1.0
        and offset_width == 0
        and offset_height == 0
        and new_upm is None
        and not metrics_override
    ):
        dprint("変形の必要が無いため、処理をスキップしました。", debug)
        return HarmonizeFontMetricsResult(
            font_obj=reopen_font(target_font_obj),
            is_upm_change=is_upm_change,
            final_scale_width=final_scale_width,
            final_scale_height=final_scale_height,
        )

    transformed_font_obj = apply_font_transform(
        target_font_obj=target_font_obj,
        scale_x=final_scale_width,
        scale_y=final_scale_height,
        offset_x=offset_width,
        offset_y=offset_height,
        new_upm=new_upm,
        metrics_override=metrics_override,
    )

    return HarmonizeFontMetricsResult(
        font_obj=transformed_font_obj,
        is_upm_change=is_upm_change,
        final_scale_width=final_scale_width,
        final_scale_height=final_scale_height,
    )


def harmonize_font_metrics(
    target_font_obj: TTFont,
    base_font_obj: TTFont,
    scale_width_manual: float = 1.0,
    scale_height_manual: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    debug: bool = False,
) -> HarmonizeFontMetricsResult:
    return harmonize_with_base(
        target_font_obj=target_font_obj,
        base_font_obj=base_font_obj,
        scale_width_manual=scale_width_manual,
        scale_height_manual=scale_height_manual,
        offset_width=offset_width,
        offset_height=offset_height,
        debug=debug,
    )
