"""
Command-line interface for text merging utilities.

Usage examples:
- Save merged unique characters from .txt files under a directory:
  uv run python -m src.cui.merge_text --input-dir ./data/texts --output ./build/merged.txt

- Print merged unique characters to stdout (no output path):
  uv run python -m src.cui.merge_text -i ./data/texts
"""

import argparse
from typing import Optional

from modules.merge_text import action_merge_text, merge_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge all .txt files in a directory, remove excluded characters, and output unique sorted characters.",
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        required=True,
        help="Directory containing .txt files to merge.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output file path. If omitted, prints result to stdout.",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Enable debug output.",
    )
    return parser.parse_args()


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args()

    if args.output:
        action_merge_text(
            input_dir=args.input_dir,
            output_path=args.output,
            debug=args.debug,
        )
    else:
        result = merge_text(args.input_dir, debug=args.debug)
        # Print to stdout when no output path is provided
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
