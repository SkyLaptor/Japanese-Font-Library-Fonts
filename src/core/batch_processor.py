from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path
from typing import Any, Mapping

import yaml
from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf
from pydantic import BaseModel, Field, field_validator

from const import BLANK_GLYPHS, ENCODE, EXCLUDE_CHARS, NORMALIZED_UPM
from modules.anonymize_info import anonymize_info
from modules.change_weight import change_weight
from modules.create_subset import create_subset
from modules.get_info import get_info
from modules.harmonize_font_metrics import apply_font_transform
from modules.merge_font import merge_font_objects
from modules.remove_empty_glyphs import remove_empty_glyphs
from utils.dprint import dprint
from utils.file_io import load_text, save_font


def _expand_and_resolve(path_like: str | Path) -> Path:
    if isinstance(path_like, Path):
        p = path_like
    else:
        # 環境変数とユーザーディレクトリ展開
        p = Path(Path(str(path_like)).expanduser())
    # Windowsでも .resolve() は絶対化してくれる（存在しないパスもOK）
    return Path(str(p)).expanduser().resolve()


def _resolve_relative(value: str | Path | None, base: Path | None) -> Path | None:
    if value is None or value == "":
        return None
    p = Path(str(value))
    if p.is_absolute():
        return _expand_and_resolve(p)
    if base is None:
        return _expand_and_resolve(p)
    return _expand_and_resolve(base / p)


def _classify_key_role(key: str) -> str:
    """キー名から解決ロールを判定する。

    - 入力系: *_path, input_dir
    - 出力系: output_name, output_dir
    それ以外: none
    """
    k = key.lower()
    if k in {"output_name", "output_dir", "output_font_path"}:
        return "output"
    if k.endswith("_path") or k == "input_dir" or k == "merge_conf":
        return "input"
    return "none"


def _normalize_paths_recursive(data: Any, base_in: Path, base_out: Path) -> Any:
    """辞書/リストを再帰的に走査し、キー規則に従って絶対パス化する。

    - 入力系（*_path, input_dir）は base_in 基準
    - 出力系（output_name, output_dir）は base_out 基準
    - ネスト/配列も再帰し、merge_fonts 内の font_path なども対象
    """
    if isinstance(data, dict):
        new_dict: dict[str, Any] = {}
        for k, v in data.items():
            # 先に中身を再帰処理（深い所の辞書・リストも対象）
            processed = _normalize_paths_recursive(v, base_in, base_out)

            role = _classify_key_role(str(k))
            if role == "input" and isinstance(processed, (str, Path)):
                new_dict[k] = _resolve_relative(processed, base_in)
            elif role == "output" and isinstance(processed, (str, Path)):
                new_dict[k] = _resolve_relative(processed, base_out)
            else:
                new_dict[k] = processed
        return new_dict
    if isinstance(data, list):
        return [_normalize_paths_recursive(item, base_in, base_out) for item in data]
    return data


def _is_otf_path(path_like: str | Path) -> bool:
    p = Path(str(path_like))
    return p.suffix.lower() == ".otf"


def _count_missing_subset_glyphs(
    font_obj: TTFont, subset_text: str
) -> tuple[int, int, int, int, list[int], list[int]]:
    target_codes = {ord(ch) for ch in subset_text}
    target_total = len(target_codes)
    if target_total == 0:
        return 0, 0, 0, 0, [], []

    cmap = font_obj.getBestCmap()
    has_glyf = 'glyf' in font_obj
    glyf_table = font_obj['glyf'] if has_glyf else None

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


def _format_codepoint_list(codes: list[int]) -> list[str]:
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


class CLIArgs(BaseModel):
    # レシピYAMLの場所（必須）
    recipe_path: Path
    # 入力の相対パス解決の基準（未指定時は recipe_path.parent）
    input_dir: Path | None = Field(default=None, alias="input_path")
    # 出力ルート（YAML側の output_dir で上書き可能）
    output_dir: Path | None = None
    # 追加のデバッグ出力を有効化
    debug: bool = False

    @field_validator("recipe_path", mode="before")
    @classmethod
    def _coerce_recipe_path(cls, v: Any) -> Path:
        if isinstance(v, Path):
            return _expand_and_resolve(v)
        return _expand_and_resolve(str(v))

    @field_validator("input_dir", mode="before")
    @classmethod
    def _coerce_input_dir(cls, v: Any) -> Any:
        # エイリアス input_path から来る値もここを通る
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def _coerce_output_dir(cls, v: Any) -> Any:
        return v


class FontProcessingRecipeModel(BaseModel):
    # グローバル既定
    base_line: int = 0
    merge_conf: Path | None = None
    anonymize: bool = False
    output_font_info: bool = False
    debug: bool = False
    steps: list[str | dict[str, Any]] | None = None

    # 入力側（YAML内にある場合）
    input_dir: Path | None = None
    # 出力側（YAML内にある場合）
    output_dir: Path | None = None

    model_config = {"extra": "allow"}


def _load_recipe_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding=ENCODE) as f:
        data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError("YAMLのルートはマップ形式である必要があります")
        return data


def _compose_runtime_config(
    cli: CLIArgs, recipe_dict: dict[str, Any]
) -> tuple[Path, Path, dict[str, Any], list[dict[str, Any]]]:
    # input_dir / output_dir の決定（GUIからのパラメーター優先→レシピ内設定→デフォルト）
    input_dir = cli.input_dir or recipe_dict.get("input_dir") or cli.recipe_path.parent
    output_dir = (
        cli.output_dir
        or recipe_dict.get("output_dir")
        or (cli.recipe_path.parent / "output")
    )
    input_dir = _expand_and_resolve(input_dir)
    output_dir = _expand_and_resolve(output_dir)

    # stepsの正規化（action 概念は廃止）
    steps: list[dict[str, Any]] = []
    if "steps" in recipe_dict and recipe_dict["steps"] is not None:
        raw_steps = recipe_dict["steps"]
        if isinstance(raw_steps, list):
            for item in raw_steps:
                if isinstance(item, dict):
                    steps.append({**item})
                else:
                    raise ValueError("steps の各要素はマップである必要があります")
        elif isinstance(raw_steps, dict):
            steps.append({**raw_steps})
        else:
            raise ValueError("steps は配列またはマップである必要があります")
    else:
        raise ValueError("recipe.yml に steps が見つかりません")

    # グローバル設定（継承元）: レシピ直下のキーをそのまま持ち回す（steps/actions は除外）
    global_params: dict[str, Any] = {
        k: v for k, v in recipe_dict.items() if k not in {"steps", "actions"}
    }
    # CLI の --debug は常に上書き
    global_params["debug"] = bool(recipe_dict.get("debug", False) or cli.debug)

    return input_dir, output_dir, global_params, steps


def _build_metrics_override_from_step(
    step: Mapping[str, Any],
    base_font_obj: TTFont,
) -> tuple[dict[str, dict[str, int]] | None, float]:
    """レシピのメトリクス値を fontTools 用の辞書へ整形する。

    - hhea: ascent, descent, lineGap
    - OS/2: sTypoAscender, sTypoDescender, sTypoLineGap
    - post: underlinePosition, underlineThickness
    指定が無い値は含めない。
    """
    # modify_metrics が真、または個別キーが1つでも与えられていれば辞書を生成
    has_any_metric = any(
        k in step
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
        os2_table = base_font_obj.get('OS/2')
        hhea_table = base_font_obj.get('hhea')
        post_table = base_font_obj.get('post')
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

    ascent = step.get("ascent")
    descent = step.get("descent")
    line_gap = step.get("line_gap")
    # 同義語対応（apricotレシピのキー名）
    u_pos = step.get("u_pos", step.get("underline_position"))
    u_thick = step.get("u_thick", step.get("underline_thickness"))

    # スケーリング係数の算出: factor = NORMALIZED_UPM / (ascent + abs(descent))
    factor: float = 1.0
    try:
        if ascent is not None and descent is not None:
            asc_f = float(ascent)
            desc_f = float(descent)
        else:
            # どちらか欠けている場合は入力フォントの値で正規化
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

    # 値が未指定(None)のものは入力フォントの値を使用し、全て factor 倍
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

    # metrics を生成するのは modify_metrics 真 or 明示指定がある場合のみ
    if not bool(step.get("modify_metrics", False)) and not has_any_metric:
        return None, factor
    return (metrics if metrics else None), factor


def action_merge_font(**kwargs: Any) -> None:
    """レシピ辞書に基づき、フォントを読み込み→変形→順次合成→空白削除→匿名化→保存。

    期待キー（assets/recipe/recipe_full.yml 構造）:
    - base_font_path: str | Path
    - scale_width: float(%) / scale_height: float(%)
    - offset_width: float(em) / offset_height: float(em)
    - modify_metrics: bool + ascent/descent/line_gap/u_pos/u_thick
    - merge_fonts: list[{font_path: str}]
    - anonymize: bool, font_name: str
    - remove_blank_glyphs: bool
    - output_name: str | Path
    """
    debug = bool(kwargs.get("debug", False))

    # 入力フォント（apricot形式の input_font_path を優先）
    base_font_path = kwargs.get("input_font_path") or kwargs.get("base_font_path")
    if not base_font_path:
        raise ValueError("steps.input_font_path または steps.base_font_path が必要です")

    # 出力フォント（apricot形式の output_font_path を優先）
    output_path = kwargs.get("output_font_path") or kwargs.get("output_name")
    if not output_path:
        raise ValueError("steps.output_font_path もしくは steps.output_name が必要です")

    # 新仕様のキー名（後方互換を維持）
    scale_width_pct = float(kwargs.get("scale_width", 100.0))
    scale_height_pct = float(kwargs.get("scale_height", 100.0))
    # apply_font_transform は倍率を1.0=100%で受け取る
    scale_width = scale_width_pct / 100.0
    scale_height = scale_height_pct / 100.0

    # オフセット（em）: 後段で factor を算出してから正規化
    raw_offset_width = float(kwargs.get("offset_width", 0))
    raw_offset_height = float(kwargs.get("offset_height", 0))

    # サブセットテキストの準備（任意）
    subset_text: str | None = None
    subset_text_path = kwargs.get("subset_text_path")
    if subset_text_path:
        try:
            subset_text = load_text(str(subset_text_path), EXCLUDE_CHARS)
        except Exception as e:
            raise ValueError(
                f"サブセットテキストの読み込みに失敗: {subset_text_path}: {e}"
            )

    weight_offset = int(round(float(kwargs.get("weight_offset", 0))))

    # 1) 入力フォント読み込み
    with TTFont(str(base_font_path)) as base_font_obj:
        # OTF入力ならオンメモリ変換
        if _is_otf_path(base_font_path):
            if debug:
                print("入力フォントをTTFに変換しています...")
            otf_to_ttf(base_font_obj)

        # 任意前処理: サブセット/太さ変更
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

        # メトリクス辞書と正規化係数の決定（未指定は入力フォントから補完/正規化）
        metrics_override, factor = _build_metrics_override_from_step(
            kwargs, base_font_obj
        )

        # オフセット適用値へ正規化係数を反映
        offset_width = int(round(raw_offset_width * factor))
        offset_height = int(round(raw_offset_height * factor))

        # 2) 変形適用（スケール・オフセット・メトリクス）
        if debug:
            print("入力フォントを変形しています...")
        base_font_obj = apply_font_transform(
            target_font_obj=base_font_obj,
            scale_width=scale_width,
            scale_height=scale_height,
            offset_width=offset_width,
            offset_height=offset_height,
            new_upm=None,  # TODO: これいる？
            metrics_override=metrics_override,
        )

        # 3) マージフォントの順次処理と合成
        merge_list = kwargs.get("merge_fonts") or []
        if not isinstance(merge_list, list):
            raise ValueError("steps.merge_fonts はリストである必要があります")

        item_count = 1
        for item in merge_list:
            if not isinstance(item, Mapping):
                raise ValueError("merge_fonts の各要素はマップである必要があります")
            sub_path = item.get("font_path")
            if not sub_path:
                continue
            with TTFont(str(sub_path)) as sub_font_obj:
                print(
                    f"マージフォントを処理しています...: ({item_count}/{len(merge_list)}) {sub_path}"
                )

                if debug:
                    print(
                        f"[DEBUG]: マージ前の入力フォントのグリフ数(Unicodeマップ済): {get_info(base_font_obj, debug=False).glyph_count_uni}"
                    )

                # マージフォントがOTFならTTF変換
                if _is_otf_path(sub_path):
                    if debug:
                        print("マージフォントをTTFに変換しています...")
                    otf_to_ttf(sub_font_obj)
                # マージフォントのサブセット化
                if subset_text:
                    if debug:
                        print("マージフォントをサブセット化しています...")
                    sub_font_obj = create_subset(
                        font_obj=sub_font_obj, subset_text=subset_text, debug=debug
                    )
                # マージフォントの太さ変更
                item_weight_offset = int(round(float(item.get("weight_offset", 0))))
                if item_weight_offset != 0:
                    if debug:
                        print(
                            f"マージフォントの太さを変更しています...: {item_weight_offset}"
                        )
                    sub_font_obj = change_weight(
                        sub_font_obj, offset_weight=item_weight_offset, debug=debug
                    )

                # マージフォントの変形（正規化係数を反映）
                item_offset_width = int(
                    round(float(item.get("offset_width", 0)) * factor)
                )
                item_offset_height = int(
                    round(float(item.get("offset_height", 0)) * factor)
                )
                if debug:
                    print("マージフォントを変形しています...")
                sub_font_obj = apply_font_transform(
                    target_font_obj=sub_font_obj,
                    scale_width=scale_width,  # マージフォントは入力フォントと同じスケールを適用
                    scale_height=scale_height,  # マージフォントは入力フォントと同じスケールを適用
                    offset_width=item_offset_width,
                    offset_height=item_offset_height,
                    new_upm=None,  # TODO: これいる？
                    metrics_override=metrics_override,
                )

                # マージ実行
                base_font_obj = merge_font_objects(
                    base_font_obj=base_font_obj,
                    interpolation_font_obj=sub_font_obj,
                    debug=debug,
                )

                if debug:
                    print(
                        f"[DEBUG]: マージ後の入力フォントのグリフ数(Unicodeマップ済): {get_info(base_font_obj, debug=False).glyph_count_uni}"
                    )

                item_count += 1

        # 4) 空白削除・匿名化
        if bool(kwargs.get("remove_blank_glyphs", True)):
            base_font_obj = remove_empty_glyphs(base_font_obj, debug=debug)

        if bool(kwargs.get("anonymize", False)):
            font_name = kwargs.get("font_name") or "Anonymous"
            base_font_obj = anonymize_info(
                base_font_obj, font_name=str(font_name), debug=debug
            )

        # 5) 保存
        saved_output = save_font(
            font_obj=base_font_obj,
            input_path=str(base_font_path),
            output_path=str(output_path),
        )
        print(f"[一括フォント加工]フォントを保存しました: {saved_output}")

        # 6) 出力情報レポート（output_font_info=true の場合）
        if bool(kwargs.get("output_font_info", False)):
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
                ) = _count_missing_subset_glyphs(base_font_obj, subset_text)
                print(
                    f"[一括フォント加工]出力直前サブセット欠損確認: {missing_total}/{target_total} (未マップ={missing_unmapped}, アウトライン無し={missing_no_outline})"
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
                    _format_codepoint_list(missing_unmapped_codes)
                    if missing_unmapped_codes
                    else ["(なし)"]
                )
                lines.append("")
                lines.append("[アウトライン無し]")
                lines.extend(
                    _format_codepoint_list(missing_no_outline_codes)
                    if missing_no_outline_codes
                    else ["(なし)"]
                )
            report_path.write_text("\n".join(lines), encoding=ENCODE)
            print(f"[一括フォント加工]レポートを出力: {report_path}")


def run_batch(cli: CLIArgs, debug: bool = False) -> int:
    # CLI引数から入力/出力の基準を決める
    base_in = _expand_and_resolve(cli.input_dir or cli.recipe_path.parent)
    base_out = _expand_and_resolve(
        cli.output_dir or (cli.recipe_path.parent / "output")
    )

    # YAML を読み込み、全体を再帰的に絶対パス化
    raw = _load_recipe_yaml(cli.recipe_path)
    normalized = _normalize_paths_recursive(raw, base_in, base_out)

    # 最終のランタイム構成を合成
    input_dir, output_dir, global_params, steps = _compose_runtime_config(
        cli, normalized
    )

    # 出力先のルートだけ先に作成（アクション側でも必要に応じて作成される）
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{i}] の形式が不正です: {step}")

        # ステップ固有パラメータでグローバルを上書き
        run_kwargs = {**global_params, **step}
        print(f"[一括フォント加工] 実行 ({i}/{len(steps)})")
        dprint(f"run_kwargs = {run_kwargs}", debug)
        action_merge_font(**run_kwargs)

    print(f"[一括フォント加工] 完了: {cli.recipe_path}")
    return 0


def parse_argv(argv: list[str]) -> CLIArgs:
    parser = argparse.ArgumentParser(
        description="YAMLレシピから一括フォント生成を実行します。"
    )
    parser.add_argument("--recipe", required=True, help="レシピYAMLのパス")
    # 新推奨: --input-dir、後方互換: --input-path（alias）
    group_in = parser.add_mutually_exclusive_group()
    group_in.add_argument(
        "--input-dir",
        dest="input_dir",
        help="入力の相対パス解決の基準ディレクトリ（未指定時はレシピのディレクトリ）",
    )
    group_in.add_argument(
        "--input-path",
        dest="input_path",
        help="[互換] 入力の相対パス解決の基準ディレクトリ",
    )
    parser.add_argument(
        "--output-dir",
        dest="output_dir",
        help="出力ルート（YAML内の output_dir で上書き可能）",
    )
    parser.add_argument("--debug", action="store_true", help="デバッグ出力を有効化")

    ns = parser.parse_args(argv[1:])
    input_dir_val = ns.input_dir or ns.input_path
    return CLIArgs.model_validate(
        {
            "recipe_path": ns.recipe,
            "input_path": input_dir_val,  # alias 経由で input_dir に入る
            "output_dir": ns.output_dir,
            "debug": ns.debug,
        }
    )


def main() -> None:
    cli = parse_argv(sys.argv)
    try:
        code = run_batch(cli)
    except Exception as e:
        print(f"[一括処理] 失敗: {e}")
        sys.exit(1)
    sys.exit(code)


if __name__ == "__main__":
    main()
