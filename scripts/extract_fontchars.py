#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

PROTECTED_BLANKGLYPHS = [
    "space", "uni3000", "ideographicspace", ".notdef", 
    "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
    "emspace", "enspace", "thinspace", "hairspace",
    "uni2003", "uni2002", "uni2009", "uni200A",
    "zerowidthspace", "uni200B"
]
DEFAULT_OUTPUTNAME_SUFFIX = "_chars"

def main(input_font_path, output_chars_path=""):
    """Output the characters contained in the font to text.

           Unintended blank glyphs are ignored in the count.

           Args:
               input_font_path (str): Font file paths subject to convert.
               output_chars_path (str, optional): Output chars file path. The file extension must be txt. Default: ''
           
           Returns:
               str: Output chars file path.
    """
    print("=== Start of Extracting characters from font ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print(f"Removing unintended blank glyphs...")
    font.selection.none()
    for glyph in font.glyphs(): 
        print(f"{glyph.glyphname:<50}",end="\r")
        if glyph.glyphname in PROTECTED_BLANKGLYPHS:
            continue
        if len(glyph.layers[1]) == 0:
            print(f"Remove: {glyph.glyphname:<50}")
            font.selection.select(("more",), glyph.glyphname)
    font.clear()

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Analyzing glyphs...")
    characters = []
    for glyph in font.glyphs():
        if glyph.unicode > 0:
            print(f"{glyph.glyphname:<50}",end="\r")
            characters.append(chr(glyph.unicode))
    characters = sorted(list(set(characters)))

    print("Outputting contained chars...")
    if output_chars_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_chars_path = os.path.join(directory, output_file_name+".txt")
    with open(output_chars_path, "w", encoding="utf-8") as f:
        f.write("".join(characters))

    print("=== End of Extracting characters from font ===")
    font.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract all Unicode characters from a font file.")

    parser.add_argument("-i", "--input", required=True, help="Input font file path.")
    parser.add_argument("-o", "--output", default="", help="Output chars file path. The file extension must be txt.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
        
    args = parser.parse_args()

    main(
        input_font_path=args.input,
        output_chars_path=args.output
    )
