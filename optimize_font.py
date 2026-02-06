#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging

import constants
import preoptimize_font

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

PREFLAG = ".pre"

def main(input_font_path, subset_chars_path=None, ratio_total=100, ratio_width=100, weight_offset=0, metrics=constants.DEFAULT_METRICS, output_font_path=None):
    """Apply various processing and optimization to the font and output it as a TTF font.
           
           Weight adjustment is not recommended due to the high risk of glyph corruption.
           Width transformation is performed after size transformation.
           If a font file named font_name.ttf.pre exists for the target font, it will be used preferentially.
           
           Args:
               input_font_path (str): Font file paths subject to pre-optimization.
               subset_chars_path (str, Optional): Subset character file path. Default: None
               ratio_total (Union[str, int], optional): Size specification(%). Default: 100
               ratio_width (Union[str, int], optional): Width specification(%). Default: 100
               weight_offset (Union[str, int], optional): Weight adjustment value(em). Thick for positive values, thin for negative values. Default: 0
               metrics (Union[str, tuple, list], Optional): Ascent value, Descent value. For strings, use comma-separated values. Default: ConstantValue
               output_font_path (str, optional): Output font file path. The file extension must be ttf. Default: None
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Font Optimization ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if subset_chars_path and not os.path.exists(subset_chars_path):
        msg = f"No such file: {subset_chars_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    ratio_total = float(ratio_total) / 100
    ratio_width = float(ratio_width) / 100
    weight_offset = float(weight_offset)
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

    if not os.path.exists(input_font_path + PREFLAG):
        input_font_path = preoptimize_font.main(input_font_path, metrics, input_font_path + PREFLAG)
    else:
        input_font_path = input_font_path + PREFLAG

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    # Switch to cubic curve mode. (for high-precision machining)
    font.layers[1].is_quadratic = False

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print(f"Execute the subset...")
    with open(subset_chars_path, 'r', encoding='utf-8') as f:
        subset_content = f.read()
    allowed_unichars = set(ord(c) for c in subset_content)
    for glyph in list(font.glyphs()):
        if glyph.unicode not in allowed_unichars:
            font.removeGlyph(glyph)

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    print(f"Remove unintended blank glyphs...")
    protected_glyphs = [
        "space", "uni3000", "ideographicspace", ".notdef", 
        "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
        "emspace", "enspace", "thinspace", "hairspace",
        "uni2003", "uni2002", "uni2009", "uni200A",
        "zerowidthspace", "uni200B"
    ]
    target_names = set()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in protected_glyphs:
            continue
        if len(glyph.layers[1]) == 0:
            target_names.add(glyph.glyphname)
    for name in target_names:
        try:
            font.removeGlyph(name)
        except:
            continue

    glyph_count = len(list(font.glyphs()))
    print(f"Current total number of glyphs: {glyph_count}")

    if ratio_total != 1.0:
        print(f"Resizing ({ratio_total * 100}%) in progress...")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.transform(psMat.scale(ratio_total),)
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    if ratio_width != 1.0:
        print(f"Expand width ({ratio_width * 100}%) in progress...")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.transform(psMat.scale(ratio_width,1.0),)
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    if weight_offset != 0:
        print(f"Adjusting font weight ({weight_offset}em)...")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.changeWeight(weight_offset,"auto",0,0,"squish")
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    print("Final optimization in progress...")
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
        output_file_name = f"{base_name}_optimized"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of Font Optimization ===")
    return output_font_path


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: fontforge -quiet -script optimize_font.py <input_font_path> [subset_chars_path] [ratio_total] [ratio_width] [weight_offset] [metrics] [output_font_path]")
    else:
        main(*args)