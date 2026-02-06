#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

import convert_otf2ttf

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

EMSIZE = 1024
DEFAULT_OUTPUTNAME_SUFFIX = "_preopt"
PROTECTED_BLANKGLYPHS = [
        "space", "uni3000", "ideographicspace", ".notdef", 
        "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
        "emspace", "enspace", "thinspace", "hairspace",
        "uni2003", "uni2002", "uni2009", "uni200A",
        "zerowidthspace", "uni200B"
    ]
SIMPLIFY = 0.5

def main(input_font_path, output_font_path=None, ascent=None, descent=None):
    """Pre-optimize the font and output it as a TTF font.
           
           Args:
               input_font_path (str): Font file paths subject to pre-optimization.
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: None
               ascent (int, Optional): Ascent value. If no value is entered, the font value will be used. Default: None
               descent (int, Optional): Descent value. If no value is entered, the font value will be used. Default: None
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Font Pre-Optimization ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if ascent is not None and descent is not None:
        if (ascent + descent) != EMSIZE:
            msg = f"Metric inconsistency detected: Ascent({ascent}) + Descent({descent}) = {ascent + descent}. Must be equal to EMSIZE({EMSIZE})."
            logging.error(msg)
            raise ValueError(msg)

    # If an OTF file is provided, convert it to TTF.
    ext = os.path.splitext(input_font_path)[1].lower()
    if ext == ".otf":
        input_font_path = convert_otf2ttf.main(input_font_path)
        if not os.path.exists(input_font_path):
            msg = f"No such file: {input_font_path}. The conversion from OTF to TTF may have failed."
            logging.error(msg)
            raise FileNotFoundError(msg)

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    # Switch to cubic curve mode. (for high-precision machining)
    font.layers[1].is_quadratic = False

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
        if glyph.glyphname in PROTECTED_BLANKGLYPHS:
            continue
        if len(glyph.layers[1]) == 0:
            font.selection.select(("more",), glyph.glyphname)
    font.clear()

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print("Metrics adjustment in progress...")
    font.em = EMSIZE
    if ascent == None:
        ascent = font.ascent
    if descent == None:
        descent = font.descent
    font.os2_use_typo_metrics = True
    font.ascent = ascent
    font.os2_typoascent = ascent
    font.os2_winascent = ascent
    font.hhea_ascent = ascent
    font.descent = descent
    font.os2_typodescent = -descent
    font.os2_windescent = descent
    font.hhea_descent = -descent
    font.os2_typolinegap = 0
    font.os2_subxsize = int(EMSIZE * 0.635)
    font.os2_subysize = int(EMSIZE * 0.6)
    font.os2_subxoff = 0
    font.os2_subyoff = int(EMSIZE * 0.075)
    font.os2_supxsize = int(EMSIZE * 0.635)
    font.os2_supysize = int(EMSIZE * 0.6)
    font.os2_supxoff = 0
    font.os2_supyoff = int(EMSIZE * 0.34)
    font.os2_strikeysize = int(EMSIZE * 0.050)
    font.os2_strikeypos = int(EMSIZE * 0.03)
    font.hasvmetrics = False
    font.upos = -100
    font.uwidth = 50
    anonumous_fontname = "PreOptimizedFont"
    font.gasp = ()
    font.sfntRevision = 1.000
    font.fontname = anonumous_fontname
    font.fullname = anonumous_fontname
    font.familyname = anonumous_fontname
    font.uniqueid = 1
    font.version = "1.000"
    font.copyright = ""
    font.os2_vendor = "    "
    new_names = []
    for lang in ("English (US)",):
        new_names.append((lang, "Copyright", font.copyright))
        new_names.append((lang, "Family", anonumous_fontname))
        new_names.append((lang, "SubFamily", "Regular"))
        new_names.append((lang, "Fullname", anonumous_fontname))
        new_names.append((lang, "Version", f"Version {font.version}"))
        new_names.append((lang, "PostScriptName", anonumous_fontname))
    font.sfnt_names = tuple(new_names)

    print(f"Removing overlapping paths...")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        print(f"{glyph.glyphname:<50}",end="\r")
        glyph.removeOverlap()
        glyph.round()

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

    print("Outputting optimized fonts...")
    if output_font_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of Font Pre-Optimization ===")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Font Pre-Optimization Script")
    
    # 引数の定義
    parser.add_argument("-i", "--input", help="Font file paths subject to pre-optimization.")
    parser.add_argument("-o", "--output", help="Output font file path. The file extension must be ttf.", default="")
    parser.add_argument("--ascent", type=int, help=f"Ascent value. Ensure that the total with descent is {EMSIZE}. If no value is entered, the font value will be used.", default=None)
    parser.add_argument("--descent", type=int, help=f"Descent value. Ensure that the total with ascent is {EMSIZE}. If no value is entered, the font value will be used.", default=None)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output,
        ascent=args.ascent,
        descent=args.descent
    )