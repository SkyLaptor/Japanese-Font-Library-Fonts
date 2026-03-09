"""
Command-line interface for extracting all available glyph characters from a font file.

Usage examples:
- Extract glyphs and save to file:
  uv run python -m src.cui.get_glyphs --input ./assets/fonts/target.ttf --output ./build/glyphs.txt

- Print glyphs to stdout:
  uv run python -m src.cui.get_glyphs -i ./assets/fonts/target.ttf
"""

import argparse
from typing import Optional

from fontTools.ttLib import TTFont
from modules.get_glyphs import get_glyphs
from utils.file_io import save_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract all characters (glyphs) from a font file.",
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input font file path (TTF or OTF).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output text file path. If omitted, prints result to stdout.",
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
        with TTFont(args.input) as font_obj:
            glyphs = get_glyphs(font_obj, debug=args.debug)
            
            if args.output:
                # 既存のsave_textユーティリティを使用して保存
                saved_path = save_text(glyphs, args.input, args.output, "_glyphs")
                print(f"文字数: {len(glyphs)}")
                print(f"フォントに含まれる文字を保存しました: {saved_path}")
            else:
                print(glyphs)
                
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
