#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging
import secrets
import string

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

FONTNAME = "Unknown"

def main(font, fontname=FONTNAME):
    """フォント情報を匿名化する
           
           Args:
               font (fontforge.font): 匿名化対象のフォント
               fontname (str, Optional): フォント名 空白や記号は使用できません。
           
           Returns:
               fontforge.font: 匿名化後のフォント
    """

    #print("=== 現在のフォント情報")
    #print(f"フォント名: {font.fontname}")
    #print(f"フォントフル名: {font.fullname}")
    #print(f"フォントファミリー名: {font.familyname}")
    #print(f"ユニークID: {font.uniqueid}")
    #print(f"バージョン: {font.version}")
    #print(f"著作権: {font.copyright}")
    #print(f"OS2ベンダー: {font.os2_vendor}")
    #for sfnt_name in font.sfnt_names:
    #    print(f"SFNTエントリ: {sfnt_name}")
    
    font.fontname = fontname
    font.fullname = fontname
    font.familyname = fontname
    font.uniqueid = 1
    font.version = "1.000"
    font.copyright = ""
    font.os2_vendor = "    "
    new_names = []
    for lang in ("English (US)",):
        new_names.append((lang, "Copyright", font.copyright))
        new_names.append((lang, "Family", FONTNAME))
        new_names.append((lang, "SubFamily", "Regular"))
        new_names.append((lang, "UniqueID", "Unknown"))
        new_names.append((lang, "Fullname", FONTNAME))
        new_names.append((lang, "Version", f"Version {font.version}"))
        new_names.append((lang, "PostScriptName", FONTNAME))
    font.sfnt_names = tuple(new_names)

    #print("=== 匿名化後のフォント情報")
    #print(f"フォント名: {font.fontname}")
    #print(f"フォントフル名: {font.fullname}")
    #print(f"フォントファミリー名: {font.familyname}")
    #print(f"ユニークID: {font.uniqueid}")
    #print(f"バージョン: {font.version}")
    #print(f"著作権: {font.copyright}")
    #print(f"OS2ベンダー: {font.os2_vendor}")
    #for sfnt_name in font.sfnt_names:
    #    print(f"SFNTエントリ: {sfnt_name}")

    return font


if __name__ == "__main__":
    print("フォントオブジェクトが必要です。")
