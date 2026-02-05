#!/usr/bin/env fontforge
import fontforge
import sys
import os

import constants

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_path):
    """フォントの縦横サイズの平均値を出力する
           input_path: フォントファイルパス
           return: 解析データのタプル(Ascent値(em),Descent値(em),横幅の平均値(em),縦幅の平均値(em),解析対象のグリフ数,EMサイズ)
    """

    # ファイルが存在しない場合
    if not os.path.exists(input_path):
        print(f"エラー: {input_path}が存在しないため処理を終了。")
        return

    # 処理開始
    print(f"--- 解析開始: {input_path} ---")
    font = fontforge.open(input_path,("fstypepermitted",))

    # OpenType機能の削除
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    # フォントのEMサイズを設定
    font.em = constants.EMSIZE

    total_width = 0
    total_height = 0
    glyph_count = 0
    ascent = font.ascent
    descent = font.descent

    # グリフの縦横平均値を算出する
    for i in range(*constants.ANALYZE_RANGE):
        if i in font:
            glyph = font[i]
            if glyph.isWorthOutputting():
                bbox = glyph.boundingBox()
                
                # 幅と高さの計算
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                # 実体のあるグリフのみをカウント
                if width > 0 and height > 0:
                    total_width += width
                    total_height += height
                    glyph_count += 1
    
    if glyph_count == 0:
        print("エラー: 解析対象のグリフが存在しないため処理を終了。")
        font.close()
        return ascent, descent, 0, 0, glyph_count, constants.EMSIZE

    avg_x = round(total_width / glyph_count)
    avg_y = round(total_height / glyph_count)

    # 処理終了
    print("--- 解析完了 ---")
    print(f"Ascent:{ascent}em,Descent:{descent}em,横幅の平均値:{avg_x}em,縦幅の平均値:{avg_y}em,解析対象のグリフ数:{glyph_count},EMサイズ:{constants.EMSIZE}")
    font.close()

    return ascent, descent, avg_x, avg_y, glyph_count, constants.EMSIZE

if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)