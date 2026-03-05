"""
Command-line interface for generating subset text presets.

Usage examples:
- Generate JP full subset and save to file:
  uv run python -m src.cui.subset_generator --type jp-full --output ./build/subsets/jp_full.txt

- Print JIS X 0208 subset to stdout with validNameChars escaping:
  uv run python -m src.cui.subset_generator -t jisx0208 --escape-validnamechars
"""

import argparse
from typing import Optional

from modules.subset_generator import (
    generate_subset_jp_full,
    generate_subset_jp_jisx0208,
)
from utils.file_io import save_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Japanese subset text (JP full or JIS X 0208).",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["jp-full", "jisx0208"],
        required=True,
        help="Subset type to generate: 'jp-full' or 'jisx0208'.",
    )
    parser.add_argument(
        "-e",
        "--escape-validnamechars",
        "--validnamechars-escape",
        dest="validnamechars_escape",
        action="store_true",
        help="Escape characters for FontForge validNameChars.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path. If omitted, prints result to stdout.",
    )
    return parser.parse_args()


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args()

    if args.type == "jp-full":
        content = generate_subset_jp_full(
            validnamechars_escape=args.validnamechars_escape
        )
    else:  # "jisx0208"
        content = generate_subset_jp_jisx0208(
            validnamechars_escape=args.validnamechars_escape
        )

    if args.output:
        saved = save_text(content, output_path=args.output)
        print(f"サブセットテキストを出力しました。: {saved}")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
