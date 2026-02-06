#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging

import constants
import convert_otf2ttf

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_font_path, metrics=constants.DEFAULT_METRICS, output_font_path=None):
    """Pre-optimize the font and output it as a TTF font.
           
           Args:
               input_font_path (str): Font file paths subject to pre-optimization.
               metrics (Union[str, tuple, list], Optional): Ascent value, Descent value. For strings, use comma-separated values. Default: ConstantValue
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: None
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Font Pre-Optimization ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if metrics is None or metrics == "":
        print("INFO:Since the metric values (Ascent, Descent) were not provided, the default value are used.")
        ascent, descent = constants.DEFAULT_METRICS
    elif isinstance(metrics, str):
        try:
            a_str, d_str = metrics.split(',')
            ascent, descent = int(a_str), int(d_str)
        except ValueError:
            msg = f"An unknown error occurred during the metric-type conversion."
            logging.error(msg)
            raise RuntimeError(msg)
    elif isinstance(metrics, (tuple, list)):
        ascent, descent = metrics
    else:
        msg = f"An unknown error occurred during the metric-type conversion."
        logging.error(msg)
        raise RuntimeError(msg)

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

    print(f"Removing unintended blank glyphs...")
    target_names = set()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in constants.PROTECTED_BLANKGLYPHS:
            continue
        if len(glyph.layers[1]) == 0:
            target_names.add(glyph.glyphname)
    for name in target_names:
        try:
            font.removeGlyph(name)
        except:
            continue

    print("Metrics adjustment in progress...")
    font.em = constants.EMSIZE
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
    font.os2_subxsize = int(constants.EMSIZE * 0.635)
    font.os2_subysize = int(constants.EMSIZE * 0.6)
    font.os2_subxoff = 0
    font.os2_subyoff = int(constants.EMSIZE * 0.075)
    font.os2_supxsize = int(constants.EMSIZE * 0.635)
    font.os2_supysize = int(constants.EMSIZE * 0.6)
    font.os2_supxoff = 0
    font.os2_supyoff = int(constants.EMSIZE * 0.34)
    font.os2_strikeysize = int(constants.EMSIZE * 0.050)
    font.os2_strikeypos = int(constants.EMSIZE * 0.03)
    font.hasvmetrics = False
    font.upos = -100
    font.uwidth = 50

    # Anonymization
    #font.sfnt_names = ()
    font.gasp = ()
    font.sfntRevision = constants.FONT_VERSION
    font.fontname = "PreOptimizedFont"
    font.fullname = "PreOptimizedFont"
    font.familyname = "PreOptimizedFont"
    font.uniqueid = constants.FONT_ID
    font.version = f"{constants.FONT_VERSION}"
    font.copyright = constants.FONT_COPYRIGHT
    font.os2_vendor = constants.FONT_VENDOR

    print(f"Removing overlapping paths...")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        print(f"{glyph.glyphname:<50}",end="\r")
        glyph.removeOverlap()
        glyph.round()

    print("Cleaning before output...")
    font.selection.all()
    processed_glyphs = set()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in processed_glyphs:
                continue
        print(f"{glyph.glyphname:<50}",end="\r")
        glyph.simplify(constants.SIMPLIFY, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        processed_glyphs.add(glyph.glyphname)
        glyph.round()

    # Disable cubic curve mode (required for TrueType output)
    font.layers[1].is_quadratic = True

    print("Outputting optimized fonts...")
    if output_font_path == "" or not output_font_path:
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name}_merged"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of Font Pre-Optimization ===")
    return output_font_path


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: fontforge -quiet -script preoptimize_font.py <input_font_path> [metrics] [output_font_path]")
    else:
        main(*args)