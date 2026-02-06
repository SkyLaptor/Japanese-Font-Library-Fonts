#!/usr/bin/env python3
import sys
import os
import logging
import argparse

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

DEFAULT_OUTPUTNAME_SUFFIX = "_dedup"

def main(input_chars_path, output_chars_path=""):
    """Output a string file with duplicate strings removed.
           
           Args:
               input_chars_path (str): Chars file for which you want to perform deduplication.
               output_chars_path (str, optional): Output chars file path. The file extension must be txt. Default: ''
           
           Returns:
               str: Output chars file path.
    """
    print("=== Start of Duplicate strings removed from file ===")

    if not os.path.exists(input_chars_path):
        msg = f"No such file: {input_chars_path}"
        logging.error(msg)
        raise FileNotFoundError(msg)

    with open(input_chars_path, "r", encoding="utf-8") as f:
        content = f.read()

    unique_chars = sorted(list(set(content)))
    unique_chars = [c for c in unique_chars if not c.isspace()]
    result = "".join(unique_chars)

    print(f"Original length: {len(content)}")
    print(f"Unique length: {len(result)}")

    print("Outputting contained chars...")
    if output_chars_path == "":
        print("INFO:Since the output destination is unspecified, output to the same location as the base font.")
        directory = os.path.dirname(input_chars_path) or "."
        base_name = os.path.splitext(os.path.basename(input_chars_path))[0]
        output_file_name = f"{base_name + DEFAULT_OUTPUTNAME_SUFFIX}"
        output_chars_path = os.path.join(directory, output_file_name+".txt")
    with open(output_chars_path, "w", encoding="utf-8") as f:
        f.write("".join(result))

    print("=== End of Duplicate strings removed from file ===")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Output a string file with duplicate strings removed.")

    parser.add_argument("-i", "--input", required=True, help="Chars file for which you want to perform deduplication.")
    parser.add_argument("-o", "--output", default="", help="Output chars file path. The file extension must be txt.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    main(
        input_chars_path=args.input,
        output_chars_path=args.output
    )
