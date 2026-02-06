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
SHIFT_HEIGHT_EVERY = -144
SHIFT_HEIGHT_BOOK = 0
SHIFT_HEIGHT_HAND = 0
RESIZE_MODE_V = "v"
RESIZE_MODE_VH = "vh"
RESIZE_MODE_HE = "he"

def main(input_font_path, output_font_path="", subset_chars_path="", mode_ui="", ratio_width=100, resize_mode=RESIZE_MODE_V):
    """Convert the specified font for Skyrim's UI

           Args:
               input_font_path (str): Font file paths subject to converion.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: ''
               subset_chars_path (str, Optional): Subset character file path. Default: ''
               mode_ui (str, optional): UI mode(every,book,hand). Default: ''
               ratio_width (int, optional): Width specification(%). Default: 100
               resize_mode (str, optional): Resize mode(v,vh,he). Default: 'v'

           Returns:
               str: Output font file path.
    """
    print("=== Start of Convert the specified font for Skyrim's UI ===")

    base_font_path = ""
    shift_height = 0
    if mode_ui == MODE_UI_EVERY:
        print("Convert for Everywhere UI.")
        base_font_path = BASE_FONT_EVERY
        shift_height = SHIFT_HEIGHT_EVERY
    elif mode_ui == MODE_UI_BOOK:
        print("Convert for Book UI.")
        base_font_path = BASE_FONT_BOOK
        shift_height = SHIFT_HEIGHT_BOOK
    elif mode_ui == MODE_UI_HAND:
        print("Convert for Handwritten UI.")
        base_font_path = BASE_FONT_HAND
        shift_height = SHIFT_HEIGHT_HAND
    else:
        msg = f"The UI mode is incorrect. Please select from the following options. {MODE_UI_EVERY}, {MODE_UI_BOOK}, {MODE_UI_HAND}"
        logging.error(msg)
        raise ValueError(msg)

    print("Calculating the resize factor...")
    base_result = average_glyph_metrics.main(base_font_path)
    input_result = average_glyph_metrics.main(input_font_path)

    ratio_total = 100
    if resize_mode == RESIZE_MODE_V:
        print(f"Vertical average value of the base font: {base_result[1]}units")
        print(f"Vertical average value of the input font: {input_result[1]}units")
        ratio_h = base_result[1] / input_result[1]
        ratio_total = round(ratio_h * 100)
    elif resize_mode == RESIZE_MODE_VH:
        print(f"Vertical average value of the base font: {base_result[1]}units")
        print(f"Vertical average value of the input font: {input_result[1]}units")
        print(f"Horizontal average value of the base font: {base_result[0]}units")
        print(f"Horizontal average value of the input font: {input_result[0]}units")
        ratio_h = base_result[1] / input_result[1]
        ratio_w = base_result[0] / input_result[0]
        ratio_total = round(((ratio_h + ratio_w) / 2) * 100)
    elif resize_mode == RESIZE_MODE_HE:
        print(f"Vertical average value of the base font: {base_result[1]}units")
        print(f"Vertical average value of the input font: {input_result[1]}units")
        ratio_h = base_result[1] / input_result[1]
        ratio_total = round(ratio_h * 100)
        ratio_width = round((base_result[0] / (input_result[0] * ratio_total)) * 100) + ratio_width
        print(f"Width factor is: {ratio_width}%")
    else:
        msg = f"The Resize mode is incorrect. Please select from the following options. {RESIZE_MODE_V}, {RESIZE_MODE_VH}, {RESIZE_MODE_HE}"
        logging.error(msg)
        raise ValueError(msg)

    print(f"Resize factor is: {ratio_total}%")

    print("Converting fonts...")
    output_font_path = optimize_font.main(input_font_path=input_font_path, output_font_path=output_font_path, subset_chars_path=subset_chars_path, ascent=ASCENT, descent=DESCENT, ratio_total=ratio_total, ratio_width=ratio_width, shift_height=shift_height)

    print("=== End of Convert the specified font for Skyrim's UI ===")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert the specified font for Skyrim's UI")
    
    parser.add_argument("-i", "--input", required=True, help="Font file paths subject to converion.")
    parser.add_argument("-o", "--output", default="", help="Output font file path. The file extension must be ttf.")
    parser.add_argument("--subset", default="", help="Subset character file path.")
    parser.add_argument("--mode_ui", default="", help="UI mode(every,book,hand).")
    parser.add_argument("--ratio_width", type=int, default=100, help=f"Width specification(%%).")
    parser.add_argument("--resize_mode", default="v", help="Resize mode(v,vh,he).")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output,
        subset_chars_path=args.subset,
        mode_ui=args.mode_ui,
        ratio_width=args.ratio_width,
        resize_mode=args.resize_mode
    )