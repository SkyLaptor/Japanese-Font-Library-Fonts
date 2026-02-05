#!/usr/bin/env fontforge
import fontforge
import sys
import os

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def convert_otf2ttf(input_path):
    """OTFをTTFに変換する
           input_path: OTFファイルパス
           return: TTFファイルパス
    """

    # フォントファイルが存在しない場合
    if not os.path.exists(input_path):
        print(f"エラー: {input_path}が存在しないため処理を終了。")
        return

    # 処理開始
    print(f"--- 変換開始: {input_path} ---")
    font = fontforge.open(input_path,("fstypepermitted",))
    # TTF出力を行うため、前面レイヤを2次曲線モードへ設定
    font.layers[1].is_quadratic = True

    # CID単一化
    print("CID単一化を実施")
    font.cidFlatten()

    # OpenType機能の削除
    print("OpenType機能の削除を実施")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    # CID単一化による未マップグリフ削除
    print("CID単一化による未マップグリフ削除を開始")
    unmapped_glyphs = []
    for glyph in font.glyphs():
        if glyph.unicode == -1 and glyph.glyphname != ".notdef":
            unmapped_glyphs.append(glyph.glyphname)
    for name in unmapped_glyphs:
        print(f"CID単一化による未マップグリフを削除中:{name:<50}", end="\r")
        font.removeGlyph(name)

    # フォントの出力
    print("TTFフォントを出力中...")
    directory = os.path.dirname(input_path) or "."
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_file = f"{base_name}"
    output_path = os.path.join(directory, output_file+".ttf")
    font.generate(output_path)

    # 処理終了
    print(f"--- 変換完了: {output_path} ---")
    print("変換には時間がかかるため、以後は変換済TTFファイルの利用を推奨。")
    font.close()

    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: fontforge -quiet -script convert_otf2ttf.py <OTFフォント>")
        print("例: fontforge -quiet -script convert_otf2ttf.py example.otf")
    else :
        convert_otf2ttf(sys.argv[1])