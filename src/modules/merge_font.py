# Dependencies: FFDec=False, FontForge=False
from io import BytesIO

from fontTools.merge import Merger
from fontTools.ttLib import TTFont

from modules.anonymize_info import anonymize_info
from modules.get_average_size import get_average_size
from modules.harmonize_font_metrics import apply_font_transform
from modules.remove_empty_glyphs import remove_empty_glyphs
from utils.file_io import save_font


def _font_to_buffer(font_obj: TTFont) -> BytesIO:
    buffer = BytesIO()
    font_obj.save(buffer)
    buffer.seek(0)
    return buffer


def _get_base_metrics_override(base_font_obj: TTFont) -> dict[str, dict[str, int]]:
    metrics_override: dict[str, dict[str, int]] = {}

    base_os2 = base_font_obj.get('OS/2')
    if base_os2 is not None:
        metrics_override["os2"] = {
            "usWinAscent": int(base_os2.usWinAscent),
            "usWinDescent": int(base_os2.usWinDescent),
            "sTypoAscender": int(base_os2.sTypoAscender),
            "sTypoDescender": int(base_os2.sTypoDescender),
            "sTypoLineGap": int(base_os2.sTypoLineGap),
        }

    base_hhea = base_font_obj.get('hhea')
    if base_hhea is not None:
        metrics_override["hhea"] = {
            "ascent": int(base_hhea.ascent),
            "descent": int(base_hhea.descent),
            "lineGap": int(base_hhea.lineGap),
        }

    base_post = base_font_obj.get('post')
    if base_post is not None:
        metrics_override["post"] = {
            "underlinePosition": int(base_post.underlinePosition),
            "underlineThickness": int(base_post.underlineThickness),
        }

    return metrics_override


def _remove_overlapping_cmap_entries(
    base_font_obj: TTFont,
    interpolation_font_obj: TTFont,
    *,
    debug: bool = False,
) -> TTFont:
    base_cmap = base_font_obj.getBestCmap()
    target_cmap = interpolation_font_obj.getBestCmap()

    overlap_codes = [code for code in target_cmap if code in base_cmap]
    if not overlap_codes:
        return interpolation_font_obj

    for code in overlap_codes:
        del target_cmap[code]

    if debug:
        print(
            "[merge_font][dedupe] "
            f"base重複コードポイントを除外: {len(overlap_codes)} 件"
        )

    return interpolation_font_obj


def _select_scaling_baseline(
    base_avg,
    target_avg,
) -> tuple[float, float, str]:
    if target_avg.count and target_avg.avg_w and target_avg.avg_h:
        baseline_base_w = base_avg.avg_w
        baseline_base_h = base_avg.avg_h
        baseline_target_w = target_avg.avg_w
        baseline_target_h = target_avg.avg_h
        baseline_name = "CJK"
    elif target_avg.count_latin and target_avg.avg_w_latin and target_avg.avg_h_latin:
        baseline_base_w = base_avg.avg_w_latin
        baseline_base_h = base_avg.avg_h_latin
        baseline_target_w = target_avg.avg_w_latin
        baseline_target_h = target_avg.avg_h_latin
        baseline_name = "Latin"
    else:
        baseline_base_w = 0
        baseline_base_h = 0
        baseline_target_w = 0
        baseline_target_h = 0
        baseline_name = "Fallback(1.0)"

    auto_scale_x = 1.0
    auto_scale_y = 1.0

    if baseline_target_w and baseline_base_w:
        auto_scale_x = baseline_base_w / baseline_target_w

    if baseline_target_h and baseline_base_h:
        auto_scale_y = baseline_base_h / baseline_target_h

    return auto_scale_x, auto_scale_y, baseline_name


def _prepare_interpolation_font_for_merge(
    base_font_obj: TTFont,
    interpolation_font_obj: TTFont,
    *,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    remove_empty: bool = False,
    anonymize: bool = False,
    anonymize_font_name: str = "Anonymous",
    debug: bool = False,
) -> TTFont:
    prepared_font_obj = interpolation_font_obj

    # Step 1: 自動サイズ適合
    base_avg = get_average_size(base_font_obj)
    target_avg = get_average_size(prepared_font_obj)

    auto_scale_x, auto_scale_y, baseline_name = _select_scaling_baseline(
        base_avg=base_avg,
        target_avg=target_avg,
    )

    if debug:
        print(
            "[merge_font][auto_scale] "
            f"baseline={baseline_name}, "
            f"scale_x={auto_scale_x:.3f}, scale_y={auto_scale_y:.3f}, "
            f"target_cjk={target_avg.count}, target_latin={target_avg.count_latin}"
        )

    prepared_font_obj = apply_font_transform(
        target_font_obj=prepared_font_obj,
        scale_x=auto_scale_x,
        scale_y=auto_scale_y,
        offset_x=0,
        offset_y=0,
        new_upm=None,
    )

    # Step 2: メトリクス強制同期（Ascent/Descent/LineGap/Underline/UPM）
    base_upm = int(base_font_obj['head'].unitsPerEm)
    metrics_override = _get_base_metrics_override(base_font_obj)
    prepared_font_obj = apply_font_transform(
        target_font_obj=prepared_font_obj,
        scale_x=1.0,
        scale_y=1.0,
        offset_x=0,
        offset_y=0,
        new_upm=base_upm,
        metrics_override=metrics_override,
    )

    # Step 3: ユーザーパラメータ適用
    prepared_font_obj = apply_font_transform(
        target_font_obj=prepared_font_obj,
        scale_x=scale_width,
        scale_y=scale_height,
        offset_x=offset_width,
        offset_y=offset_height,
        new_upm=None,
    )

    # Step 4: クリーンアップと合体（合体前のクリーンアップ）
    if remove_empty:
        prepared_font_obj = remove_empty_glyphs(prepared_font_obj)

    if anonymize:
        prepared_font_obj = anonymize_info(
            prepared_font_obj,
            font_name=anonymize_font_name,
        )

    prepared_font_obj = _remove_overlapping_cmap_entries(
        base_font_obj=base_font_obj,
        interpolation_font_obj=prepared_font_obj,
        debug=debug,
    )

    return prepared_font_obj


def action_merge_font(
    base_path: str,
    interpolation_path: str,
    output_path: str,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    remove_empty: bool = False,
    anonymize: bool = False,
    anonymize_font_name: str = "Anonymous",
    debug: bool = False,
    **_,
):
    merged_font = merge_font(
        base_path=base_path,
        interpolation_path=interpolation_path,
        scale_width=scale_width,
        scale_height=scale_height,
        offset_width=offset_width,
        offset_height=offset_height,
        remove_empty=remove_empty,
        anonymize=anonymize,
        anonymize_font_name=anonymize_font_name,
        debug=debug,
    )
    if output_path is not None:
        saved_output_path = save_font(
            font_obj=merged_font,
            input_path=base_path,
            output_path=output_path,
            suffix="_merged",
            debug=debug,
        )
        print(f"フォントを保存しました: {saved_output_path}")


def merge_font_objects(
    base_font_obj: TTFont,
    interpolation_font_obj: TTFont,
    *,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    remove_empty: bool = False,
    anonymize: bool = False,
    anonymize_font_name: str = "Anonymous",
    debug: bool = False,
) -> TTFont:
    prepared_interpolation_font_obj = _prepare_interpolation_font_for_merge(
        base_font_obj=base_font_obj,
        interpolation_font_obj=interpolation_font_obj,
        scale_width=scale_width,
        scale_height=scale_height,
        offset_width=offset_width,
        offset_height=offset_height,
        remove_empty=remove_empty,
        anonymize=anonymize,
        anonymize_font_name=anonymize_font_name,
        debug=debug,
    )

    merger = Merger()
    base_buffer = _font_to_buffer(base_font_obj)
    prepared_buffer = _font_to_buffer(prepared_interpolation_font_obj)

    try:
        return merger.merge(
            [
                base_buffer,
                prepared_buffer,
            ]
        )
    except AssertionError as e:
        raise ValueError(
            "fontToolsによるマージに失敗しました。"
            "入力フォントのメトリクスや内部情報の整合性を確認してください。"
        ) from e


def merge_font(
    base_path: str,
    interpolation_path: str,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    offset_width: int = 0,
    offset_height: int = 0,
    remove_empty: bool = False,
    anonymize: bool = False,
    anonymize_font_name: str = "Anonymous",
    debug: bool = False,
) -> TTFont:
    with TTFont(base_path) as base_font_obj, TTFont(interpolation_path) as sub_font_obj:
        return merge_font_objects(
            base_font_obj=base_font_obj,
            interpolation_font_obj=sub_font_obj,
            scale_width=scale_width,
            scale_height=scale_height,
            offset_width=offset_width,
            offset_height=offset_height,
            remove_empty=remove_empty,
            anonymize=anonymize,
            anonymize_font_name=anonymize_font_name,
            debug=debug,
        )
