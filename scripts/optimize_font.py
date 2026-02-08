#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

EMSIZE = 1024
SIMPLIFY = 0.5
PROTECTED_BLANKGLYPHS = [
    "space", "uni3000", "ideographicspace", ".notdef", 
    "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
    "emspace", "enspace", "thinspace", "hairspace",
    "uni2003", "uni2002", "uni2009", "uni200A",
    "zerowidthspace", "uni200B"
]
DEFAULT_OUTPUTNAME_SUFFIX = "_optimized"
FONTNAME = "OptimizedFont"

def main(input_font_path, output_font_path="", subset_chars_path="", ascent=None, descent=None, ratio_total=100.0, ratio_width=100.0, weight_offset=0, shift_height=0, proc_overlap=0):
    """Apply various processing and optimization to the font and output it as a TTF font.
           
           Weight adjustment is not recommended due to the high risk of glyph corruption.
           Width transformation is performed after size transformation.
           Height transformation is performed after Width transformation.
           If a font file named font_name.ttf.pre exists for the target font, it will be used preferentially.
           
           Args:
               input_font_path (str): Font file paths subject to pre-optimization.
               output_font_path (str, Optional): Output font file path. The file extension must be ttf. Default: ''
               subset_chars_path (str, Optional): Subset character file path. Default: ''
               ascent (int, Optional): Ascent value. If no value is entered, the font value will be used. Default: None
               descent (int, Optional): Descent value. If no value is entered, the font value will be used. Default: None
               ratio_total (float, Optional): Size specification(%). Default: 100.0
               ratio_width (float, Optional): Width specification(%). Default: 100.0
               weight_offset (int, Optional): Weight adjustment value(units). Thick for positive values, thin for negative values. Default: 0
               shift_height (int, Optional): Height adjustment value(units). Thick for positive values, thin for negative values. Default: 0
               proc_overlap (int, Optional): Overlap removal. Unless there are issues in the overlapping areas, there is no need to enable it. Default: 0
           
           Returns:
               str: Output font file path.
    """
    print("=== Start of Font Optimization ===")

    if not os.path.exists(input_font_path):
        msg = f"No such file: {input_font_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if subset_chars_path != "" and not os.path.exists(subset_chars_path):
        msg = f"No such file: {subset_chars_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if ascent is not None and descent is not None:
        if (ascent + descent) != EMSIZE:
            msg = f"Metric inconsistency detected: Ascent({ascent}) + Descent({descent}) = {ascent + descent}. Must be equal to EMSIZE({EMSIZE})."
            logging.error(msg)
            raise ValueError(msg)

    print("Opening font...")
    font = fontforge.open(input_font_path,("fstypepermitted",))
    font.encoding = "UnicodeFull"
    font.reencode("unicode")

    # Switch to cubic curve mode. (for high-precision machining)
    font.layers[1].is_quadratic = False

    #print("Removing OpenType features...")
    #for lookup in font.gsub_lookups:
    #    font.removeLookup(lookup)
    #for lookup in font.gpos_lookups:
    #    font.removeLookup(lookup)

    print("Removing hint commands...")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.manualHints = 0
        glyph.removePosSub("*")
        glyph.dhints = ()
        glyph.hhints = ()
        glyph.vhints = ()

    #print("Unlink referencies...")
    #font.unlinkReferences()
    #font.selection.all()
    #for glyph in font.selection.byGlyphs:
    #    glyph.unlinkRef()

    print("Metrics adjustment in progress...")
    if font.em != EMSIZE:
        scale = float(EMSIZE) / font.em
        font.selection.all()
        font.transform(psMat.scale(scale))
    font.em = EMSIZE
    if ascent == None:
        ascent = font.ascent
    if descent == None:
        descent = font.descent
    font.os2_use_typo_metrics = False
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
    font.gasp = ()
    font.sfntRevision = 1.000
    font.fontname = FONTNAME
    font.fullname = FONTNAME
    font.familyname = FONTNAME
    font.uniqueid = 1
    font.version = "1.000"
    font.copyright = ""
    font.os2_vendor = "    "
    new_names = []
    for lang in ("English (US)",):
        new_names.append((lang, "Copyright", font.copyright))
        new_names.append((lang, "Family", FONTNAME))
        new_names.append((lang, "SubFamily", "Regular"))
        new_names.append((lang, "Fullname", FONTNAME))
        new_names.append((lang, "Version", f"Version {font.version}"))
        new_names.append((lang, "PostScriptName", FONTNAME))
    font.sfnt_names = tuple(new_names)

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

    if subset_chars_path != "":
        print(f"Subset creation in progress...")
        glyph_count = len(list(font.glyphs()))
        with open(subset_chars_path, 'r', encoding='utf-8') as f:
            subset_content = f.read()
        allowed_unichars = set(ord(c) for c in subset_content)
        for glyph in list(font.glyphs()):
            codes = [glyph.unicode]
            if glyph.altuni:
                codes.extend([a[0] for a in glyph.altuni])
            if any(c in allowed_unichars for c in codes if c != -1):
                continue
            font.removeGlyph(glyph)
        glyph_count = len(list(font.glyphs()))
        print(f"Current total number of glyphs: {glyph_count}")

        print("Finalizing Unicode mapping for Kanji stability...")
        for glyph in font.glyphs():
            # Force the radical area (2E80-2FDF or 3400-4DBF or F900-FAFF) to be relocated to the kanji area (4E00-9FFF).
            if 0x2E80 <= glyph.unicode <= 0x2FDF or 0x3400 <= glyph.unicode <= 0x4DBF or 0xF900 <= glyph.unicode <= 0xFAFF:
                if glyph.altuni:
                    for alt_code, alt_vid, alt_rev in glyph.altuni:
                        if 0x4E00 <= alt_code <= 0x9FFF:
                            #print(f"  Switching mapping: {glyph.glyphname} {glyph.unicode:04X} -> {alt_code:04X}")
                            glyph.unicode = alt_code
                            break

    if proc_overlap > 0:
        print(f"Removing overlapping paths...")
        font.selection.all()
        for glyph in font.selection.byGlyphs:
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.removeOverlap()
            glyph.round()

    ratio_total = round(ratio_total) / 100.0
    if ratio_total != 1.0:
        offset_y = ((1.0 - ratio_total) * EMSIZE) / 2
        print(f"Resizing ({ratio_total * 100}%) in progress...")
        mat = psMat.scale(ratio_total)
        mat = psMat.compose(mat, psMat.translate(0, offset_y))
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in PROTECTED_BLANKGLYPHS or glyph.glyphname in processed_glyphs:
                continue
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.transform(mat)
            glyph.round()
            processed_glyphs.add(glyph.glyphname)

    ratio_width = round(ratio_width) / 100.0
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
        print(f"Adjusting font weight by {weight_offset} units ...")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"{glyph.glyphname:<50}",end="\r")
            glyph.changeWeight(weight_offset,"auto",0,0,"squish")
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    if shift_height != 0:
        print(f"Shifting glyphs vertically by {shift_height} units...")
        mat = psMat.translate(0, shift_height)
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in PROTECTED_BLANKGLYPHS or glyph.glyphname in processed_glyphs:
                continue
            glyph.transform(mat)
            glyph.round()
            processed_glyphs.add(glyph.glyphname)

    print("Final optimization in progress...")
    font.selection.all()
    processed_glyphs = set()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in processed_glyphs:
                continue
        print(f"{glyph.glyphname:<50}",end="\r")
        glyph.simplify(SIMPLIFY, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        processed_glyphs.add(glyph.glyphname)
        glyph.round()

    # Disable cubic curve mode (required for TrueType output)
    print("Disable cubic curve mode...")
    font.layers[1].is_quadratic = True
    #font.selection.all()
    #for glyph in font.selection.byGlyphs:
    #    print(f"{glyph.glyphname:<50}",end="\r")
    #    glyph.correctDirection()
    #    glyph.round()

    print("Outputting optimized fonts...")
    if output_font_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_font_path) or "."
        base_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_font_path = os.path.join(directory, output_file_name+".ttf")
    font.generate(output_font_path)

    font.close()

    print("=== End of Font Optimization ===")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply various processing and optimization to the font and output it as a TTF font.")
    
    parser.add_argument("-i", "--input", required=True, help="Font file paths subject to optimization.")
    parser.add_argument("-o", "--output", default="", help="Output font file path. The file extension must be ttf.")
    parser.add_argument("-s", "--subset", default="", help="Subset character file path.")
    parser.add_argument("--ascent", type=int, default=None, help=f"Ascent value. Ensure that the total with descent is {EMSIZE}. If no value is entered, the font value will be used.")
    parser.add_argument("--descent", type=int, default=None, help=f"Descent value. Ensure that the total with ascent is {EMSIZE}. If no value is entered, the font value will be used.")
    parser.add_argument("--ratio_total", type=float, default=100.0, help=f"Size specification(%%).")
    parser.add_argument("--ratio_width", type=float, default=100.0, help=f"Width specification(%%).")
    parser.add_argument("--weight_offset", type=int, default=0, help=f"Weight adjustment value(units). Thick for positive values, thin for negative values.")
    parser.add_argument("--shift_height", type=int, default=0, help=f"Height adjustment value(units). Thick for positive values, thin for negative values.")
    parser.add_argument("--proc_overlap", type=int, default=0, help=f"Overlap removal. Unless there are issues in the overlapping areas, there is no need to enable it.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input,
        output_font_path=args.output,
        subset_chars_path=args.subset,
        ascent=args.ascent,
        descent=args.descent,
        ratio_total=args.ratio_total,
        ratio_width=args.ratio_width,
        weight_offset=args.weight_offset,
        shift_height=args.shift_height,
        proc_overlap=args.proc_overlap
    )
