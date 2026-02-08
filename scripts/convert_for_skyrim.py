#!/usr/bin/env fontforge
import sys
import os
import logging
import argparse

import average_glyph_metrics
import optimize_font

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

MODE_UI_EVERY = "every"
MODE_UI_BOOK = "book"
MODE_UI_HAND = "hand"
BASE_FONT_EVERY = "skyrim_jp_every_optimized.ttf"
BASE_FONT_BOOK = "skyrim_jp_book_optimized.ttf"
BASE_FONT_HAND = "skyrim_jp_hand_optimized.ttf"
ASCENT = 880
DESCENT = 144
MODE_WIDTH_AUTO = "auto"
MODE_WIDTH_CONDENSED = "cond"
MODE_WIDTH_SKINNY = "skin"
TARGET_RATIO_CONDENSED = 0.64
TARGET_RATIO_SKINNY = 0.42
SHIFT_HEIGHT_EVERY = -96
SHIFT_HEIGHT_BOOK = 0
SHIFT_HEIGHT_HAND = 0

def main(input_font_path, output_font_path="", subset_chars_path="", mode_ui=MODE_UI_EVERY, mode_width=MODE_WIDTH_AUTO, mode_mono=0, shift_height=None):
    """Convert the specified font for Skyrim's UI

           Args:
               input_font_path (str): Font file paths subject to converion.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: ''
               subset_chars_path (str, Optional): Subset character file path. Default: ''
               mode_ui (str, Optional): UI mode(every,book,hand). Default: 'every'
               mode_width (str, Optional): Width mode(auto,cond,skin). Default: 'auto'
               mode_mono (int, Optional): Monospace mode. For monospace fonts, changing only the character width is not performed when true(1). Default: 0
               shift_height (int, Optional): Height adjustment value(units). Thick for positive values, thin for negative values. Default: None

           Returns:
               str: Output font file path.
    """
    print("=== Start of Convert the specified font for Skyrim's UI ===")

    base_font_path = ""
    if mode_ui == MODE_UI_EVERY:
        print("Convert for Everywhere UI.")
        base_font_path = BASE_FONT_EVERY
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_EVERY
    elif mode_ui == MODE_UI_BOOK:
        print("Convert for Book UI.")
        base_font_path = BASE_FONT_BOOK
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_BOOK
    elif mode_ui == MODE_UI_HAND:
        print("Convert for Handwritten UI.")
        base_font_path = BASE_FONT_HAND
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_HAND
    else:
        msg = f"The UI mode is incorrect. Please select from the following options. {MODE_UI_EVERY}, {MODE_UI_BOOK}, {MODE_UI_HAND}"
        logging.error(msg)
        raise ValueError(msg)
    if mode_width != MODE_WIDTH_AUTO and mode_width != MODE_WIDTH_CONDENSED and mode_width != MODE_WIDTH_SKINNY:
        msg = f"The Width mode is incorrect. Please select from the following options. {MODE_WIDTH_AUTO}, {MODE_WIDTH_CONDENSED}, {MODE_WIDTH_SKINNY}"
        logging.error(msg)
        raise ValueError(msg)


    print("Calculating the resize factor...")
    base_result = average_glyph_metrics.main(base_font_path)
    input_result = average_glyph_metrics.main(input_font_path)
    print(f"Vertical average value of the base font: {base_result[1]}units")
    print(f"Horizontal average value of the base font: {base_result[0]}units")
    print(f"Vertical average value of the input font: {input_result[1]}units")
    print(f"Horizontal average value of the input font: {input_result[0]}units")
    ratio_h = base_result[1] / input_result[1]
    ratio_w = input_result[0] * ratio_h
    ratio_total = ratio_h * 100.0
    if mode_width == MODE_WIDTH_CONDENSED:
        ratio_width = base_result[0] * TARGET_RATIO_CONDENSED / ratio_w * 100.0
    elif mode_width == MODE_WIDTH_SKINNY:
        ratio_width = base_result[0] * TARGET_RATIO_SKINNY / ratio_w * 100.0
    else:
        ratio_width = base_result[0] / ratio_w * 100.0
    if ratio_width > 100.0:
        ratio_width = 100.0
    
    if mode_mono > 0:
        ratio_width = 100.0
    
    print(f"Resize factor is: {ratio_total}%")
    print(f"Width factor is: {ratio_width}% (WidthMode: {mode_width})")

    print("Converting fonts...")
    output_font_path = optimize_font.main(input_font_path=input_font_path, output_font_path=output_font_path, subset_chars_path=subset_chars_path, ascent=ASCENT, descent=DESCENT, ratio_total=ratio_total, ratio_width=ratio_width, shift_height=shift_height)

    print("=== End of Convert the specified font for Skyrim's UI ===")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the specified font for Skyrim's UI")
    
    parser.add_argument("-i", "--input", type=str, required=True, help="Font file paths subject to converion.")
    parser.add_argument("-o", "--output", type=str, default="", help="Output font file path. The file extension must be ttf.")
    parser.add_argument("-s", "--subset", type=str, default="", help="Subset character file path.")
    parser.add_argument("-m", "--mode_ui", type=str, default=MODE_UI_EVERY, help="UI mode(every,book,hand).")
    parser.add_argument("-w", "--mode_width", type=str, default=MODE_WIDTH_AUTO, help=f"Width mode(auto,cond,skin).")
    parser.add_argument("--mode_mono", type=int, default=0, help=f"Monospace mode. For monospace fonts, changing only the character width is not performed when true(1).")
    parser.add_argument("--shift_height", type=int, default=None, help=f"Height adjustment value(units). Thick for positive values, thin for negative values.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output,
        subset_chars_path=args.subset,
        mode_ui=args.mode_ui,
        mode_width=args.mode_width,
        mode_mono=args.mode_mono,
        shift_height=args.shift_height
    )
