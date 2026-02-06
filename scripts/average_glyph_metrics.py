#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

EMSIZE = 1024
ANALYZE_RANGE = (0x4E00, 0x9FFF + 1)

def main(input_font_path):
    """Calculate the average values of the glyph's width and height.
           
           Note that this value is adjusted for EM size (Default.1024).
           
           Args:
               input_font_path (str): Font file paths subject to calculate.
           
           Returns:
               taple: Average values. width, height.
    """
    print("=== Start of Calculate the Glyphs average ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Opening font...")
    font = fontforge.open(input_font_path, ("fstypepermitted",))
    
    try:
        font.em = EMSIZE
        font.encoding = "UnicodeFull"
        
        print("Unlinking references for precise calculation...")
        font.selection.all()
        font.unlinkReferences()

        total_width = 0
        total_height = 0
        glyph_count = 0
        
        print(f"Analyzing CJK range {hex(ANALYZE_RANGE[0])} - {hex(ANALYZE_RANGE[1]-1)}...")
        
        for i in range(*ANALYZE_RANGE):
            if i in font:
                glyph = font[i]
                if glyph.isWorthOutputting():
                    # bbox: (x_min, y_min, x_max, y_max)
                    bbox = glyph.boundingBox()
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    
                    if width > 0 and height > 0:
                        total_width += width
                        total_height += height
                        glyph_count += 1

        if glyph_count == 0:
            print("INFO: No target glyphs found in the specified range.")
            return 0, 0

        avg_width = round(total_width / glyph_count)
        avg_height = round(total_height / glyph_count)

        print(f"Result: Average Width = {avg_width}, Average Height = {avg_height} (Total: {glyph_count} glyphs)")
        
    finally:
        font.close()

    print("=== End of Calculate the Glyphs average ===")
    return avg_width, avg_height

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate the average values of the glyph's width and height.")
    
    parser.add_argument("-i", "--input", required=True, help="Font file paths subject to calculate.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input
    )
