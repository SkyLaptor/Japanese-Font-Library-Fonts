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
    if k in {"output_name", "output_dir", "output_font_path"}:
        return "output"
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
        raise ValueError("recipe.yml に steps が見つかりません")

    global_params: dict[str, Any] = {
        k: v for k, v in recipe_dict.items() if k not in {"steps", "actions"}
    }
    global_params["debug"] = bool(recipe_dict.get("debug", False) or cli.debug)

    return input_dir, output_dir, global_params, steps


def run_batch(cli: CLIArgs, debug: bool = False) -> int:
    base_in = _expand_and_resolve(cli.input_dir or cli.recipe_path.parent)
    base_out = _expand_and_resolve(
        cli.output_dir or (cli.recipe_path.parent / "output")
    )

    raw = _load_recipe_yaml(cli.recipe_path)
    normalized = _normalize_paths_recursive(raw, base_in, base_out)

    input_dir, output_dir, global_params, steps = _compose_runtime_config(
        cli, normalized
    )

    output_dir.mkdir(parents=True, exist_ok=True)

    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"steps[{i}] の形式が不正です: {step}")

        run_kwargs = {**global_params, **step}
        print(f"[一括フォント加工] 実行 ({i}/{len(steps)})")
        dprint(f"run_kwargs = {run_kwargs}", debug)
        # 個別処理を呼び出し
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
