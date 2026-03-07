from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any, Mapping

from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf

from const import BLANK_GLYPHS, ENCODE, EXCLUDE_CHARS, NORMALIZED_UPM
from core.font_loader import reopen_font
from modules.anonymize_info import anonymize_info
from modules.change_weight import change_weight
from modules.create_subset import create_subset
from modules.get_info import get_info
from modules.harmonize_font_metrics import apply_font_transform, harmonize_font_metrics
from modules.merge_font import merge_font
from modules.remove_empty_glyphs import remove_empty_glyphs
from utils.file_io import load_text, save_font


def is_otf_path(path_like: str | Path) -> bool:
    p = Path(str(path_like))
    return p.suffix.lower() == ".otf"


def count_missing_subset_glyphs(
    font_obj: TTFont, subset_text: str
) -> tuple[int, int, int, int, list[int], list[int]]:
    target_codes = {ord(ch) for ch in subset_text}
    target_total = len(target_codes)
    if target_total == 0:
        return 0, 0, 0, 0, [], []

    cmap = font_obj.getBestCmap()
    has_glyf = "glyf" in font_obj
    glyf_table = font_obj["glyf"] if has_glyf else None

    missing_unmapped = 0
    missing_no_outline = 0
    missing_unmapped_codes: list[int] = []
    missing_no_outline_codes: list[int] = []

    for code in target_codes:
        glyph_name = cmap.get(code)
        is_intended_blank = code in BLANK_GLYPHS or (
            glyph_name is not None and glyph_name in BLANK_GLYPHS
        )
        if is_intended_blank:
            continue

        if glyph_name is None:
            missing_unmapped += 1
            missing_unmapped_codes.append(code)
            continue

        if not has_glyf or glyf_table is None:
            continue

        if glyph_name not in glyf_table:
            missing_unmapped += 1
            missing_unmapped_codes.append(code)
            continue

        glyph = glyf_table[glyph_name]
        number_of_contours = getattr(glyph, "numberOfContours", 0)
        has_outline = number_of_contours > 0 or (
            number_of_contours < 0 and bool(getattr(glyph, "components", None))
        )
        if not has_outline:
            missing_no_outline += 1
            missing_no_outline_codes.append(code)

    missing_total = missing_unmapped + missing_no_outline
    return (
        missing_total,
        missing_unmapped,
        missing_no_outline,
        target_total,
        sorted(missing_unmapped_codes),
        sorted(missing_no_outline_codes),
    )


def format_codepoint_list(codes: list[int]) -> list[str]:
    lines: list[str] = []
    for code in codes:
        char = chr(code)
        display_char = repr(char)[1:-1]
        try:
            unicode_name = unicodedata.name(char)
        except ValueError:
            unicode_name = "<NO_UNICODE_NAME>"
        lines.append(f"U+{code:04X}\t{display_char}\t{unicode_name}")
    return lines


def build_metrics_override(
    params: Mapping[str, Any],
    base_font_obj: TTFont,
) -> tuple[dict[str, dict[str, int]] | None, float]:
    """メトリクス値を fontTools 用の辞書へ整形する。

    - hhea: ascent, descent, lineGap
    - OS/2: sTypoAscender, sTypoDescender, sTypoLineGap
    - post: underlinePosition, underlineThickness
    指定が無い値は含めない。
    """
    has_any_metric = any(
        k in params
        for k in (
            "ascent",
            "descent",
            "line_gap",
            "u_pos",
            "u_thick",
            "underline_position",
            "underline_thickness",
        )
    )

    # ベースフォントのデフォルト値取得
    def _base_metrics() -> tuple[int, int, int, int, int]:
        os2_table = base_font_obj.get("OS/2")
        hhea_table = base_font_obj.get("hhea")
        post_table = base_font_obj.get("post")
        if os2_table is not None:
            asc = int(os2_table.sTypoAscender)
            desc = int(os2_table.sTypoDescender)
            lg = int(os2_table.sTypoLineGap)
        elif hhea_table is not None:
            asc = int(hhea_table.ascent)
            desc = int(hhea_table.descent)
            lg = int(hhea_table.lineGap)
        else:
            asc, desc, lg = 0, 0, 0
        upos = 0
        uth = 1
        if post_table is not None:
            upos = int(post_table.underlinePosition)
            uth = int(post_table.underlineThickness)
        return asc, desc, lg, upos, uth

    base_asc, base_desc, base_lg, base_upos, base_uth = _base_metrics()

    def _to_int(x: Any) -> int:
        try:
            return int(round(float(x)))
        except Exception:
            return int(x)

    ascent = params.get("ascent")
    descent = params.get("descent")
    line_gap = params.get("line_gap")
    u_pos = params.get("u_pos", params.get("underline_position"))
    u_thick = params.get("u_thick", params.get("underline_thickness"))

    factor: float = 1.0
    try:
        if ascent is not None and descent is not None:
            asc_f = float(ascent)
            desc_f = float(descent)
        else:
            asc_f = float(base_asc)
            desc_f = float(base_desc)
        input_sum = asc_f + abs(desc_f)
        if input_sum > 0:
            factor = NORMALIZED_UPM / input_sum
    except Exception:
        factor = 1.0

    metrics: dict[str, dict[str, int]] = {}
    hhea_vals: dict[str, int] = {}
    os2_vals: dict[str, int] = {}
    post_vals: dict[str, int] = {}

    asc_out = float(ascent) if ascent is not None else float(base_asc)
    desc_out = float(descent) if descent is not None else float(base_desc)
    lg_out = float(line_gap) if line_gap is not None else float(base_lg)
    upos_out = float(u_pos) if u_pos is not None else float(base_upos)
    uth_out = float(u_thick) if u_thick is not None else float(base_uth)

    v = _to_int(asc_out * factor)
    hhea_vals["ascent"] = v
    os2_vals["sTypoAscender"] = v

    v = _to_int(desc_out * factor)
    hhea_vals["descent"] = v
    os2_vals["sTypoDescender"] = v

    v = _to_int(lg_out * factor)
    hhea_vals["lineGap"] = v
    os2_vals["sTypoLineGap"] = v

    post_vals["underlinePosition"] = _to_int(upos_out * factor)
    post_vals["underlineThickness"] = _to_int(uth_out * factor)

    if hhea_vals:
        metrics["hhea"] = hhea_vals
    if os2_vals:
        metrics["os2"] = os2_vals
    if post_vals:
        metrics["post"] = post_vals

    if not bool(params.get("modify_metrics", False)) and not has_any_metric:
        return None, factor
    return (metrics if metrics else None), factor


def process_font(params: Mapping[str, Any]) -> None:
    """フォントを読み込み→変形→順次合成→空白削除→匿名化→保存する単一フォント加工。"""
    debug = bool(params.get("debug", False))

    # 入力/出力パス
    input_font_path = params.get("input_font_path")
    if not input_font_path:
        raise ValueError("input_font_path が必要です")

    output_path = params.get("output_font_path") or params.get("output_name")
    if not output_path:
        raise ValueError("output_font_path もしくは output_name が必要です")

    # 変形パラメータ
    scale_width_pct = float(params.get("scale_width", 100.0))
    scale_height_pct = float(params.get("scale_height", 100.0))
    scale_width = scale_width_pct / 100.0
    scale_height = scale_height_pct / 100.0

    raw_offset_width = float(params.get("offset_width", 0))
    raw_offset_height = float(params.get("offset_height", 0))

    # サブセットテキスト
    subset_text: str | None = None
    subset_text_path = params.get("subset_text_path")
    if subset_text_path:
        try:
            subset_text = load_text(str(subset_text_path), EXCLUDE_CHARS)
        except Exception as e:
            raise ValueError(
                f"サブセットテキストの読み込みに失敗: {subset_text_path}: {e}"
            )

    weight_offset = int(round(float(params.get("weight_offset", 0))))

    # 1) 入力フォント読み込み
    with TTFont(str(input_font_path)) as base_font_obj:
        if is_otf_path(input_font_path):
            if debug:
                print("入力フォントをTTFに変換しています...")
            otf_to_ttf(base_font_obj)

        if subset_text:
            if debug:
                print("入力フォントをサブセット化しています...")
            base_font_obj = create_subset(base_font_obj, subset_text, debug)

        if weight_offset != 0:
            if debug:
                print(f"入力フォントの太さを変更しています...: {weight_offset}")
            base_font_obj = change_weight(
                base_font_obj, offset_weight=weight_offset, debug=debug
            )

        # メトリクス辞書と正規化係数の決定
        metrics_override, factor = build_metrics_override(params, base_font_obj)

        offset_width = int(round(raw_offset_width * factor))
        offset_height = int(round(raw_offset_height * factor))

        # 2) 変形適用
        if debug:
            print("入力フォントを変形しています...")

        # 基準フォントモードの場合は自動調整を最初に行う
        ref_font_path = params.get("base_font_path")
        mode_val = str(params.get("mode", "")).strip().lower()
        use_base_mode = (mode_val == "base") or (
            bool(ref_font_path) and mode_val in {"", "auto"}
        )
        if use_base_mode and ref_font_path:
            with TTFont(str(ref_font_path)) as ref_font_obj:
                base_font_obj = harmonize_font_metrics(
                    target_font_obj=base_font_obj,
                    base_font_obj=ref_font_obj,
                    scale_width_manual=scale_width,
                    scale_height_manual=scale_height,
                    offset_width=offset_width,
                    offset_height=offset_height,
                    debug=debug,
                ).font_obj
        else:
            # マニュアルモードまたは基準フォント未指定
            base_font_obj = apply_font_transform(
                target_font_obj=base_font_obj,
                scale_width=scale_width * factor,
                scale_height=scale_height * factor,
                offset_width=offset_width,
                offset_height=offset_height,
                new_upm=NORMALIZED_UPM,
                metrics_override=metrics_override,
            )

        # 3) 空白削除
        if bool(params.get("remove_blank_glyphs", True)):
            base_font_obj = remove_empty_glyphs(base_font_obj, debug=debug)

        # 4) マージ
        merge_list = params.get("merge_fonts") or []
        if not isinstance(merge_list, list):
            raise ValueError("merge_fonts はリストである必要があります")

        for i, item in enumerate(merge_list, start=1):
            if not isinstance(item, Mapping):
                raise ValueError("merge_fonts の各要素はマップである必要があります")
            sub_path = item.get("font_path")
            if not sub_path:
                continue
            with TTFont(str(sub_path)) as sub_font_obj:
                print(
                    f"マージフォントを処理しています...: ({i}/{len(merge_list)}) {sub_path}"
                )

                if is_otf_path(sub_path):
                    otf_to_ttf(sub_font_obj)
                if subset_text:
                    sub_font_obj = create_subset(
                        font_obj=sub_font_obj, subset_text=subset_text, debug=debug
                    )

                if bool(params.get("remove_blank_glyphs", True)):
                    sub_font_obj = remove_empty_glyphs(sub_font_obj, debug=debug)

                item_weight_offset = int(round(float(item.get("weight_offset", 0))))
                if item_weight_offset != 0:
                    sub_font_obj = change_weight(
                        sub_font_obj, offset_weight=item_weight_offset, debug=debug
                    )

                item_offset_width = int(
                    round(float(item.get("offset_width", 0)) * factor)
                )
                item_offset_height = int(
                    round(float(item.get("offset_height", 0)) * factor)
                )
                item_scale_width = float(item.get("scale_width", 100.0)) / 100.0
                item_scale_height = float(item.get("scale_height", 100.0)) / 100.0

                # ベースフォントの現在のサイズに自動調和させる
                sub_font_obj = harmonize_font_metrics(
                    target_font_obj=sub_font_obj,
                    base_font_obj=base_font_obj,
                    scale_width_manual=item_scale_width,
                    scale_height_manual=item_scale_height,
                    offset_width=item_offset_width,
                    offset_height=item_offset_height,
                    debug=debug,
                ).font_obj

                base_font_obj = merge_font(
                    base_font=base_font_obj,
                    interp_font=sub_font_obj,
                    debug=debug,
                )
                base_font_obj = reopen_font(base_font_obj)

        # 5) 匿名化
        if bool(params.get("anonymize", False)):
            font_name = params.get("font_name") or "Anonymous"
            base_font_obj = anonymize_info(
                base_font_obj, font_name=str(font_name), debug=debug
            )

        # 6) 保存
        saved_output = save_font(
            font_obj=base_font_obj,
            input_path=str(input_font_path),
            output_path=str(output_path),
        )
        print(f"フォントを保存しました: {saved_output}")

        # レポート出力
        if bool(params.get("output_font_info", False)):
            report_path = Path(str(output_path)).with_suffix(".txt")
            info_text = str(get_info(base_font_obj, debug=False))
            lines: list[str] = [info_text]
            if subset_text:
                (
                    missing_total,
                    missing_unmapped,
                    missing_no_outline,
                    target_total,
                    missing_unmapped_codes,
                    missing_no_outline_codes,
                ) = count_missing_subset_glyphs(base_font_obj, subset_text)
                print(
                    f"出力直前サブセット欠損確認: {missing_total}/{target_total} (未マップ={missing_unmapped}, アウトライン無し={missing_no_outline})"
                )
                lines.extend(
                    [
                        "",
                        "[サブセット欠損レポート]",
                        f"対象コードポイント数: {target_total}",
                        f"欠損総数: {missing_total}",
                        f"未マップ数: {missing_unmapped}",
                        f"アウトライン無し数: {missing_no_outline}",
                        "",
                        "[未マップ]",
                    ]
                )
                lines.extend(
                    format_codepoint_list(missing_unmapped_codes)
                    if missing_unmapped_codes
                    else ["(なし)"]
                )
                lines.append("")
                lines.append("[アウトライン無し]")
                lines.extend(
                    format_codepoint_list(missing_no_outline_codes)
                    if missing_no_outline_codes
                    else ["(なし)"]
                )
            report_path.write_text("\n".join(lines), encoding=ENCODE)
            print(f"レポートを出力: {report_path}")
