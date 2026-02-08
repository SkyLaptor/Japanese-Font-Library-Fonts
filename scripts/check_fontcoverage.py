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

DEFAULT_OUTPUTNAME_SUFFIX = "_result"

def main(target_font_path, subset_chars_path, result_file_path=""):
    """Check whether the font file contains a subset string.
           
           Unintended blank glyphs are ignored during inspection.
           
           Args:
               target_font_path (str): Path to the font file you want to inspect.
               subset_chars_path (str): Path to the subset file to be inspected.
               result_file_path (str, Optional): Path to the logfile.
           
           Returns:
               str: List of missing glyph names.
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
            #print(f"Remove: {glyph.glyphname:<50}")
            font.selection.select(("more",), glyph.glyphname)
    font.clear()

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Finalizing Unicode mapping for Kanji stability (Extended)...")
    for glyph in font.glyphs():
        # Force the radical area (2E80-2FDF or 3400-4DBF or F900-FAFF) to be relocated to the kanji area (4E00-9FFF).
        if 0x2E80 <= glyph.unicode <= 0x2FDF or 0x3400 <= glyph.unicode <= 0x4DBF or 0xF900 <= glyph.unicode <= 0xFAFF:
            if glyph.altuni:
                for alt_code, alt_vid, alt_rev in glyph.altuni:
                    if 0x4E00 <= alt_code <= 0x9FFF:
                        #print(f"  Switching mapping: {glyph.glyphname} {glyph.unicode:04X} -> {alt_code:04X}")
                        glyph.unicode = alt_code
                        break

    print(f"Comparing fonts and subsets......")
    present_unicodes = set()
    for glyph in font.glyphs():
        if glyph.isWorthOutputting() or glyph.glyphname in PROTECTED_BLANKGLYPHS:
            if glyph.unicode != -1:
                present_unicodes.add(glyph.unicode)
    with open(subset_chars_path, 'r', encoding='utf-8') as f:
        target_chars = set(f.read().replace('\n', '').replace('\r', ''))
    missing_chars = []
    for char in sorted(target_chars):
        if ord(char) not in present_unicodes:
            #print(f"Missing: {char} (U+{ord(char):04X})")
            missing_chars.append(char)

    print("Outputting result logs...")
    if result_file_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(target_font_path) or "."
        font_base_name = os.path.splitext(os.path.basename(target_font_path))[0]
        subset_base_name = os.path.splitext(os.path.basename(subset_chars_path))[0]
        output_file_name = f"{font_base_name + '_' + subset_base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        result_file_path = os.path.join(directory, output_file_name+".log")
    with open(result_file_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"Inspection Result for: {os.path.basename(target_font_path)}\n")
        log_file.write(f"Subset used: {os.path.basename(subset_chars_path)}\n")
        log_file.write(f"Missing glyph count: {len(missing_chars)}\n")
        log_file.write("-" * 30 + "\n")
        log_file.write("".join(missing_chars))

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
    parser.add_argument("-l", "--log", default="", help="Path to the logfile.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        target_font_path=args.target,
        subset_chars_path=args.subset,
        result_file_path=args.log
    )
