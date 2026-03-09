"""
Command-line interface for removing empty glyphs (glyphs without outlines) from a font file.

Usage examples:
- Remove empty glyphs and save to file:
  uv run python -m src.cui.remove_empty_glyphs --input ./assets/fonts/target.ttf --output ./build/cleaned.ttf

- Remove empty glyphs with debug logging:
  uv run python -m src.cui.remove_empty_glyphs -i ./assets/fonts/target.ttf -o ./build/cleaned.ttf --debug
"""

import argparse
from typing import Optional

from modules.remove_empty_glyphs import action_remove_empty_glyphs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove empty glyphs (without outlines) from a font file to allow fallback to .notdef.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input font file path (TTF).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Output font file path.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode.",
    )
    return parser.parse_args()


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args()

    try:
        action_remove_empty_glyphs(
            input_path=args.input,
            output_path=args.output,
            debug=args.debug,
        )
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
