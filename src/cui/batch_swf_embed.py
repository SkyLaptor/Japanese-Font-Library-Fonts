from __future__ import annotations

import argparse
import sys

from core.batch_processor import CLIArgs, run_batch


def parse_argv(argv: list[str]) -> CLIArgs:
    parser = argparse.ArgumentParser(
        description="YAMLレシピから一括SWF埋め込みを実行します。"
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
        print(f"[一括SWF埋め込み] 開始: {cli.recipe_path}")
        code = run_batch(cli)
    except Exception as e:
        print(f"[一括SWF埋め込み] 失敗: {e}")
        sys.exit(1)
    sys.exit(code)


if __name__ == "__main__":
    main()
