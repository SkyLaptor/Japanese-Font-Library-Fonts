#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_font_path, output_font_path=None):
    """Convert OpenTypeFont(OTF) to TrueTypeFont(TTF).
           
           Args:
               input_font_path (str): Font file paths subject to convert.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: None
           
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

    print("Implementation of CID Unification...")
    font.cidFlatten()

    print("Removing OpenType features...")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    print("Unmapped glyph deletion in progress...")
    unmapped_glyphs = []
    for glyph in font.glyphs():
        if glyph.unicode == -1 and glyph.glyphname != ".notdef":
            unmapped_glyphs.append(glyph.glyphname)
    for name in unmapped_glyphs:
        print(f"{name:<50}", end="\r")
        font.removeGlyph(name)

    # Disable cubic curve mode (required for TrueType output)
    font.layers[1].is_quadratic = True

    print("Outputting truetype fonts...")
    if output_font_path == "" or not output_font_path:
        logging.warning("Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of OTF to TTF Convert ===")
    return output_font_path

if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: fontforge -quiet -script convert_otf2ttf.py <input_font_path> [output_font_path]")
    else:
        main(*args)