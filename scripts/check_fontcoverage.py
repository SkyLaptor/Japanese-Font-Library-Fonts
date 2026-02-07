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

def main(target_font_path, subset_chars_path):
    """Check whether the font file contains a subset string.
           
           Unintended blank glyphs are ignored during inspection.
           
           Args:
               target_font_path (str): Path to the font file you want to inspect.
               subset_chars_path (str): Path to the subset file to be inspected.
           
           Returns:
               str: List of non-existent glyph names.
    """
    print("=== Start of Glyph Containment Inspection ===")

    if not os.path.exists(target_font_path):
        msg = f"No such file: {target_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if not os.path.exists(subset_chars_path):
        msg = f"No such file: {subset_chars_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Opening font...")
    font = fontforge.open(target_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    print("Removing OpenType features...")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    print("Removing hint commands...")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.manualHints = 0
        glyph.removePosSub("*")
        glyph.dhints = ()
        glyph.hhints = ()
        glyph.vhints = ()

    print("Unlink referencies...")
    font.unlinkReferences()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.unlinkRef()

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

    missing_chars = []
    with open(subset_chars_path, 'r', encoding='utf-8') as f:
        chars = set(f.read().strip())
    for char in chars:
        codepoint = ord(char)
        if font.findEncodingSlot(codepoint) == -1:
            print(f"Missing glyph: '{char}' (U+{codepoint:04X})")
            missing_chars.append(char)

    if not missing_chars:
        print("There are no missing glyphs.")
    else:
        print(f"There were {len(missing_chars)} missing glyphs.")

    print("=== End of Glyph Containment Inspection ===")
    return missing_chars


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check whether the font file contains a subset string.")
    
    parser.add_argument("-t", "--target", required=True, help="Path to the font file you want to inspect.")
    parser.add_argument("-s", "--subset", required=True, help="Path to the subset file to be inspected.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        target_font_path=args.target,
        subset_chars_path=args.subset
    )
