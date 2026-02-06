#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

DEFAULT_OUTPUTNAME_SUFFIX = "_merged"

def main(base_font_path, sub_font_path, output_font_path):
    """Merge fonts and output them as a new font.
           
           Glyphs not present in the base font file are interpolated using glyphs from the interpolation font.
           
           Args:
               base_font_path (str): Base font file. The side that is interpolated.
               sub_font_path (str): Interpolation font file.
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Merge fonts ===")

    if not os.path.exists(base_font_path):
        msg = f"No such file: {base_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if not os.path.exists(sub_font_path):
        msg = f"No such file: {sub_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Opening font...")
    base_font = fontforge.open(base_font_path,("fstypepermitted",))
    base_font.encoding = "UnicodeFull"
    base_font.reencode("unicode")
    sub_font = fontforge.open(sub_font_path,("fstypepermitted",))
    sub_font.encoding = "UnicodeFull"
    sub_font.reencode("unicode")

    if base_font.em != sub_font.em:
        base_font.close()
        sub_font.close()
        msg = f"Font files have inconsistent EM sizes. Base:{base_font.em}, Sub:{sub_font.em}"
        logging.error(msg)
        raise ValueError(msg)

    glyph_count = len(list(base_font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Merge font...")
    base_font.mergeFonts(sub_font_path)

    glyph_count = len(list(base_font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Outputting optimized fonts...")
    if output_font_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(base_font_path) or "."
        base_name = os.path.splitext(os.path.basename(base_font_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    base_font.generate(output_font_path)

    base_font.close()
    sub_font.close()


    print("=== End of Merge fonts ===")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge fonts and output them as a new font.")
    
    parser.add_argument("-b", "--base", help="Base font file. The side that is interpolated.")
    parser.add_argument("-s", "--sub", help="Interpolation font file.")
    parser.add_argument("-o", "--output", help="Output font file path. The file extension must be ttf.", default="")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        base_font_path=args.base,
        sub_font_path=args.sub,
        output_font_path=args.output
    )