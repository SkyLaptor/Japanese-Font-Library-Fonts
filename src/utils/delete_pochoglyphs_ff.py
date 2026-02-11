#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

DEFAULT_OUTPUTNAME_SUFFIX = "_cleaned"
DEFAULT_POCHO_SIZE = 350

def main(input_font_path, output_font_path="", pocho_size=None):
    """Remove the mysterious black circle glyph from the font.
           
           Weight adjustment is not recommended due to the high risk of glyph corruption.
           Width transformation is performed after size transformation.
           Height transformation is performed after Width transformation.
           If a font file named font_name.ttf.pre exists for the target font, it will be used preferentially.
           
           Args:
               input_font_path (str): Target font file path.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: ''
               pocho_size (int, optional): Size determined to be a black circle.
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Remove the mysterious black circle ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if pocho_size == None:
        print(f"INFO:The size of the black circle was not specified. It will default to {DEFAULT_POCHO_SIZE}.")
        pocho_size = DEFAULT_POCHO_SIZE

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")
    
    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")
    
    print("Begin deletion...")
    count = 0
    for glyph in font.glyphs():
        if glyph.isWorthOutputting():
            print(f"{glyph.glyphname:<50}",end="\r")
            bbox = glyph.boundingBox()
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            is_sanctuary = (0x3000 <= glyph.unicode <= 0x303F) or (glyph.unicode == 0x30FB)
            if width <= pocho_size and height <= pocho_size and not is_sanctuary:
                print(f"Remove: {glyph.glyphname:<50}")
                glyph.clear()
                count += 1

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Outputting optimized fonts...")
    if output_font_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of Remove the mysterious black circle ===")
    return output_font_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove the mysterious black circle glyph from the font.")
    
    parser.add_argument("-i", "--input", required=True, help="Target font file path.")
    parser.add_argument("-o", "--output", default="", help="Output font file path. The file extension must be ttf.")
    parser.add_argument("--pocho_size", type=int, help="Size determined to be a black circle.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output,
        pocho_size=args.pocho_size
    )