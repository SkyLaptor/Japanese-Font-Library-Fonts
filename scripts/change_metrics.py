#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os
import logging

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(font, ascent, descent):
    """フォントのメトリクスを変更する
           
           Args:
               font (fontforge.font): 変更対象のフォント
               ascent (int): Ascentの値
               descent (int): Descentの値
           
           Returns:
               fontforge.font: 変更後のフォント
    """

    emsize = ascent + descent

    if emsize % 8 != 0:
        logging.error("ascentとdescentの値の合計は8の倍数にしてください。例:880,144")
        raise ValueError()

    #print("=== 現在のメトリクス")
    #print(f"EMサイズ: {font.em}")

    print(f"メトリクスを変更します: Ascent:{ascent}, Descent:{descent}, EMサイズ:{emsize}")
    if font.em != emsize:
        scale = float(emsize) / font.em
        font.selection.all()
        font.transform(psMat.scale(scale))
        font.em = emsize
    font.ascent = ascent
    font.descent = descent
    font.upos = -100
    font.uwidth = 50
    font.hasvmetrics = False
    font.os2_winascent = ascent
    font.os2_windescent = descent
    font.os2_typoascent = ascent
    font.os2_typodescent = -descent
    font.os2_use_typo_metrics = False
    font.os2_typolinegap = 0
    font.os2_subxsize = int(font.em * 0.635)
    font.os2_subysize = int(font.em * 0.6)
    font.os2_subxoff = 0
    font.os2_subyoff = int(font.em * 0.075)
    font.os2_supxsize = int(font.em * 0.635)
    font.os2_supysize = int(font.em * 0.6)
    font.os2_supxoff = 0
    font.os2_supyoff = int(font.em * 0.34)
    font.os2_strikeysize = int(font.em * 0.050)
    font.os2_strikeypos = int(font.em * 0.03)
    font.hhea_ascent = ascent
    font.hhea_descent = -descent

    #print("=== 変更後のメトリクス")
    #print(f"EMサイズ: {font.em}")

    return font


if __name__ == "__main__":
    print("フォントオブジェクトが必要です。")
