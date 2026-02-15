#!/usr/bin/env fontforge
import argparse
import os
import sys
from pathlib import Path

import fontforge

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

# FontForge環境でのパス問題を避けるため、プロジェクト固有のimportは避ける
BUILD_DIR = "build"


def main():
    parser = argparse.ArgumentParser(
        description="FontForgeを使用してフォントを結合するスクリプト。FontForgeからのみ使用できます。"
    )
    parser.add_argument("base", help="ベースフォントのファイルパス")
    parser.add_argument("--sub", default="", help="補間フォントのファイルパス")
    parser.add_argument("--out", default="", help="出力ファイル名")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    font = fontforge.open(args.base)

    print("ベースフォントにマージ: %s" % args.sub)
    font.mergeFonts(args.sub)

    save_font(font=font, input=args.base, output=args.out)
    font.close()


def save_font(
    font,  # fontforgeのフォントタイプ。正しい型名が分からないのでAny
    input: str = "",
    output: str = "",
):
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        output = Path(BUILD_DIR) / f"{Path(input).stem}_merged{Path(input).suffix}"
    else:
        output = Path(output)
    font.generate(str(output), flags=("winkern",))
    print(f"フォントファイルを保存しました。: {output}")


if __name__ == '__main__':
    main()
