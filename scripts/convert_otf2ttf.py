#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

SIMPLIFY = 0.5

def main(input_font_path, output_font_path=""):
    """Convert OpenTypeFont(OTF) to TrueTypeFont(TTF).
           
           Args:
               input_font_path (str): Font file paths subject to convert.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: ''
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of OTF to TTF Convert ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    print("Implementation of CID Unification...")
    font.cidFlatten()
    font.encoding = "UnicodeFull"
    font.reencode("unicode")
    
    print("Clearing Unicode Variation Sequences to avoid cmap format 14 errors...")
    for glyph in font.glyphs():
        glyph.altuni = None
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    print("Removing OpenType features...")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Unmapped glyph deletion in progress...")
    font.selection.none()
    for glyph in font.glyphs():
        if glyph.unicode == -1 and glyph.glyphname != ".notdef":
            font.selection.select(("more",), glyph.glyphname)
    font.clear()

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    # Disable cubic curve mode (required for TrueType output)
    font.layers[1].is_quadratic = True

    print("Cleaning before output...")
    font.selection.all()
    processed_glyphs = set()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in processed_glyphs:
                continue
        print(f"{glyph.glyphname:<50}",end="\r")
        glyph.simplify(SIMPLIFY, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        processed_glyphs.add(glyph.glyphname)
        glyph.correctDirection()
        glyph.round()

    print("Outputting TrueType fonts...")
    if output_font_path == "" or not output_font_path:
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path, flags=("opentype",))

    font.close()

    print("=== End of OTF to TTF Convert ===")
    return output_font_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert OpenTypeFont(OTF) to TrueTypeFont(TTF).")
    
    parser.add_argument("-i", "--input", required=True, help="Font file paths subject to convert.")
    parser.add_argument("-o", "--output", default="", help="Output font file path. The file extension must be ttf.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output
    )
