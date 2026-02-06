#!/usr/bin/env fontforge
import fontforge
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_fontc_path,output_dir_path=""):
    """Extract fonts from the font collection.
           
           Args:
               input_fontc_path (str): Path to the font collection file to be extracted.
               output_dir_path (str, optional): Extraction destination directory. Default: ''
           
           Returns:
               str: List of extracted font file paths.
    """
    print("=== Start of Extract fonts ===")

    if not os.path.exists(input_fontc_path):
        msg = f"No such file: {input_fontc_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    if output_dir_path != "" and not os.path.exists(output_dir_path):
        msg = f"No such file: {output_dir_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    print("Extracting...")
    extracted_font_paths = []
    if output_dir_path == "" or not output_dir_path:
        print("INFO:Since the output destination is unspecified, output to the same location as the font collection.")
        output_dir_path = os.path.dirname(os.path.abspath(input_fontc_path))
    ext = os.path.splitext(input_fontc_path)[1].lower()
    default_out_ext = ".ttf" if ext == ".ttc" else ".otf"
    font_names = fontforge.fontsInFile(input_fontc_path)
    for name in font_names:
        font = fontforge.open(f"{input_fontc_path}({name})")
        safe_name = name.replace(" ", "_").replace("/", "-")
        output_filename = f"{safe_name}{default_out_ext}"
        full_path = os.path.join(output_dir_path, output_filename)
        font.generate(full_path)
        font.close()
        extracted_font_paths.append(full_path)

    print("Extract completed.")
    for path in extracted_font_paths:
        print(f"{path}")

    print("=== End of Extract fonts ===")
    return extracted_font_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract fonts from the font collection.")
    
    parser.add_argument("-i", "--input", required=True, help="Path to the font collection file to be extracted.")
    parser.add_argument("-o", "--output", default="", help="Extraction destination directory.")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_fontc_path=args.input,
        output_dir_path=args.output
    )
