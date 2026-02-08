#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging
import argparse

import change_metrics
import anonymize_font

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

DEFAULT_OUTPUTNAME_SUFFIX = "_tested"

def main(input_font_path, output_font_path=""):
    """スクリプトをテストする
           
           Args:
               input_font_path (str): テストしたいフォントパス
               output_font_path (str, Optional): テスト後のフォント出力先パス
           
           Returns:
               str: テスト後のフォント出力先パス
    """

    if not os.path.exists(input_font_path):
        logging.error(f"フォントファイルが見つかりません。: {input_font_path}")
        raise FileNotFoundError()

    print("フォントを開きます。")
    font = fontforge.open(input_font_path,("fstypepermitted",))

    # ここにテストしたい関数を記述
    font = change_metrics.main(font, 881, 144)
    #font = anonymize_font.main(font)

    print("フォントを出力します。")
    if output_font_path == "":
        print("フォント出力先パスが設定されていないため、テストしたフォントと同じ場所に出力します。")
        output_dir = os.path.dirname(input_font_path) or "."
        input_font_name = os.path.splitext(os.path.basename(input_font_path))[0]
        output_font_path = os.path.join(output_dir, input_font_name + DEFAULT_OUTPUTNAME_SUFFIX + ".ttf")
    font.generate(output_font_path, flags=("winkern",))
    font.close()
    print(f"出力が完了しました。出力先:{output_font_path}")

    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="スクリプトをテストする")
    
    parser.add_argument("input_font", help="テストしたいフォントパス")
    parser.add_argument("output_font", nargs='?', default="", help="テスト後のフォント出力先パス")
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    main(
        input_font_path=args.input_font,
        output_font_path=args.output_font
    )
