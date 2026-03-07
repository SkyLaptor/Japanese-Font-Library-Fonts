from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from const import ENCODE
from core.font_processor import process_font
from utils.dprint import dprint


def _expand_and_resolve(path_like: str | Path) -> Path:
    if isinstance(path_like, Path):
        p = path_like
    else:
        p = Path(Path(str(path_like)).expanduser())
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
    k = key.lower()
    if k in {"output_name", "output_dir", "output_font_path", "output_swf_path"}:
        return "output"
    # output_*_path は上で捕捉済み。それ以外の *_path は入力系として扱う。
    if k.endswith("_path") or k == "input_dir" or k == "merge_conf":
        return "input"
    return "none"


def _normalize_paths_recursive(data: Any, base_in: Path, base_out: Path) -> Any:
    if isinstance(data, dict):
        new_dict: dict[str, Any] = {}
        for k, v in data.items():
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


class CLIArgs(BaseModel):
    recipe_path: Path
    input_dir: Path | None = Field(default=None, alias="input_path")
    output_dir: Path | None = None
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
        return v

    @field_validator("output_dir", mode="before")
    @classmethod
    def _coerce_output_dir(cls, v: Any) -> Any:
        return v


def _load_recipe_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding=ENCODE) as f:
        data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ValueError("YAMLのルートはマップ形式である必要があります")
        return data


def _compose_runtime_config(
    cli: CLIArgs, recipe_dict: dict[str, Any]
) -> tuple[Path, Path, dict[str, Any], list[dict[str, Any]]]:
    input_dir = cli.input_dir or recipe_dict.get("input_dir") or cli.recipe_path.parent
    output_dir = (
        cli.output_dir
        or recipe_dict.get("output_dir")
        or (cli.recipe_path.parent / "output")
    )
    input_dir = _expand_and_resolve(input_dir)
    output_dir = _expand_and_resolve(output_dir)

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
        # steps が無い場合は SWF 埋め込みモードの可能性があるため、ここでは例外を投げない。
        steps = []

    global_params: dict[str, Any] = {
        k: v for k, v in recipe_dict.items() if k not in {"steps", "actions"}
    }
    global_params["debug"] = bool(recipe_dict.get("debug", False) or cli.debug)

    return input_dir, output_dir, global_params, steps


def run_batch(cli: CLIArgs, debug: bool = False) -> int:
    base_in = _expand_and_resolve(cli.input_dir or cli.recipe_path.parent)
    # output_dir が .swf で終わっている場合は、パス解決の基準は親フォルダを使用する
    swf_override_path: Path | None = None
    if cli.output_dir is not None:
        od = _expand_and_resolve(cli.output_dir)
        if od.suffix.lower() == ".swf":
            swf_override_path = od
            base_out = od.parent
        else:
            base_out = od
    else:
        base_out = _expand_and_resolve(cli.recipe_path.parent / "output")

    raw = _load_recipe_yaml(cli.recipe_path)
    normalized = _normalize_paths_recursive(raw, base_in, base_out)

    # SWF 埋め込みモード（embeds）があるか先に判定
    if "embeds" in normalized and normalized.get("embeds") is not None:
        from core.swf_processor import process_swf

        # ルートの基準入出力を計算（steps 無しでも基準は必要）
        base_input_dir = normalized.get("input_dir") or base_in
        base_output_dir = normalized.get("output_dir") or base_out
        base_input_dir = _expand_and_resolve(base_input_dir)
        base_output_dir = _expand_and_resolve(base_output_dir)

        # 正規化を既に実施済みなので、ここでは items 形式へ変換のみ実施
        raw_items = normalized.get("embeds")
        if isinstance(raw_items, dict):
            raw_items = [raw_items]
        if not isinstance(raw_items, list) or not raw_items:
            raise ValueError("embeds は1件以上の配列である必要があります")

        items: list[dict[str, Any]] = []
        for entry in raw_items:
            if not isinstance(entry, dict):
                raise ValueError("embeds の各要素はマップである必要があります")
            # レシピ側のキー名をコア処理が期待するキー名へ変換
            # input_font_path -> font_path, internal_font_name -> internal_name
            font_path = entry.get("input_font_path") or entry.get("font_path")
            internal_name = entry.get("internal_font_name") or entry.get(
                "internal_name"
            )
            if not font_path:
                continue
            items.append(
                {
                    "font_path": font_path,
                    "internal_name": internal_name,
                }
            )

        if not items:
            raise ValueError("埋め込み対象フォントが見つかりません")

        output_swf_path = normalized.get("output_swf_path")
        # GUI から .swf のフルパスが指定されていれば、それを最優先で使用
        if swf_override_path is not None:
            output_swf_path = swf_override_path
        if not output_swf_path:
            raise ValueError("output_swf_path がレシピ内に指定されていません")

        run_kwargs: dict[str, Any] = {
            # グローバル指定（debug など）
            "debug": bool(normalized.get("debug", False) or cli.debug or debug),
            # 出力先
            "output_swf_path": output_swf_path,
            # アイテム
            "items": items,
        }

        # 出力先ディレクトリを作成
        out_parent = Path(str(output_swf_path)).resolve().parent
        out_parent.mkdir(parents=True, exist_ok=True)

        print("[一括SWF埋め込み] 実行 (1/1)")
        dprint(f"run_kwargs = {run_kwargs}", debug)
        process_swf(run_kwargs)
        print(f"[一括SWF埋め込み] 完了: {cli.recipe_path}")
        return 0

    # 通常のフォント加工モード（steps）
    input_dir, output_dir, global_params, steps = _compose_runtime_config(
        cli, normalized
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{i}] の形式が不正です: {step}")

        # SWF埋め込みステップ判定（embed_fonts / embeds いずれかを含む）
        if (
            ("embed_fonts" in step and step.get("embed_fonts") is not None)
            or ("embeds" in step and step.get("embeds") is not None)
            or (
                # 後方互換: output_swf_path のみ存在する場合も埋め込み扱い
                "output_swf_path" in step
                and not step.get("input_font_path")
            )
        ):
            from core.swf_processor import process_swf

            raw_items = step.get("embed_fonts")
            if raw_items is None:
                raw_items = step.get("embeds")
            if isinstance(raw_items, dict):
                raw_items = [raw_items]
            if not isinstance(raw_items, list) or not raw_items:
                raise ValueError(
                    "embed_fonts/embeds は1件以上の配列である必要があります"
                )

            items: list[dict[str, Any]] = []
            for entry in raw_items:
                if not isinstance(entry, dict):
                    raise ValueError(
                        "embed_fonts/embeds の各要素はマップである必要があります"
                    )
                font_path = entry.get("input_font_path") or entry.get("font_path")
                internal_name = entry.get("internal_font_name") or entry.get(
                    "internal_name"
                )
                if not font_path:
                    continue
                items.append({"font_path": font_path, "internal_name": internal_name})

            if not items:
                raise ValueError("埋め込み対象フォントが見つかりません")

            output_swf_path = step.get("output_swf_path") or global_params.get(
                "output_swf_path"
            )
            # GUI から .swf のフルパスが渡されていればそれを最優先で適用
            if 'swf_override_path' in locals() and swf_override_path is not None:
                output_swf_path = swf_override_path
            if not output_swf_path:
                raise ValueError(
                    "output_swf_path が指定されていません（ステップ/グローバル）"
                )

            run_kwargs = {
                "output_swf_path": output_swf_path,
                "items": items,
                "debug": bool(global_params.get("debug", False) or debug),
            }
            print(f"[一括SWF埋め込み] 実行 ({i}/{len(steps)})")
            dprint(f"run_kwargs = {run_kwargs}", debug)
            process_swf(run_kwargs)
            continue

        # デフォルトはフォント加工ステップ
        run_kwargs = {**global_params, **step}
        print(f"[一括フォント加工] 実行 ({i}/{len(steps)})")
        dprint(f"run_kwargs = {run_kwargs}", debug)
        process_font(run_kwargs)

    print(f"[一括フォント加工] 完了: {cli.recipe_path}")
    return 0


def parse_argv(argv: list[str]) -> CLIArgs:
    parser = argparse.ArgumentParser(
        description="YAMLレシピから一括フォント生成を実行します。"
    )
    parser.add_argument("--recipe", required=True, help="レシピYAMLのパス")
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
            "input_path": input_dir_val,
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
