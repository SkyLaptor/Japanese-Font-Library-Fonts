#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os

import constants
import convert_otf2ttf

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_path, subset_path=constants.DEFAULT_SUBSET, ratio_total=100, ratio_width=100, weight_offset=0, metrics=constants.DEFAULT_METRICS, prefix="", suffix=""):
    """フォントを最適化されたTTFフォントにする
           input_path: フォントファイルパス
           subset_path: サブセットファイルパス
           ratio_total: サイズ指定(%)
           ratio_width: 横幅指定(%)
           weight_offset: ウェイト調整値(em)
           metrics: Ascent値,Descent値のカンマ区切り文字列もしくはタプルまたはリスト
           prefix: 最適化済みフォントファイル名の先頭に付与する文字
           suffix: 最適化済みフォントファイル名の末尾に付与する文字
           return: 最適化済みフォントファイルパス
    """

    # フォントファイルが存在しない場合
    if not os.path.exists(input_path):
        print(f"エラー: フォントファイル {input_path} が存在しないため処理を終了。")
        return

    # サブセットファイルが存在しない場合
    if not os.path.exists(subset_path):
        print(f"エラー: サブセットファイル {subset_path} が存在しないため処理を終了。")
        return

    # OTFの場合はTTFに変換する
    ext = os.path.splitext(input_path)[1].lower()
    if ext == ".otf":
        input_path = convert_otf2ttf.main(input_path)
        # フォントファイルが存在しない場合
        if not os.path.exists(input_path):
            print(f"エラー: フォントファイル {input_path} が存在しないため処理を終了。")
            return

    # パラメータ解析
    ratio_width_f = float(ratio_width) / 100.0
    ratio_total_f = float(ratio_total) / 100.0
    weight_offset_f = float(weight_offset) # 正の値で太く、負の値で細く

    # 処理開始
    print(f"--- 最適化開始: {input_path} ---")
    print(f"設定: サブセットファイル{subset_path}, サイズ指定{ratio_total}%, 横幅指定{ratio_width}%, ウェイト調整値{weight_offset}em, メトリクス{metrics}")
    if metrics is None:
        print("注: メトリクス値(Ascent,Descent)が渡されていないためフォント設定が使用される。")
    font = fontforge.open(input_path,("fstypepermitted",))
    
    # 3次曲線モードへ移行
    font.layers[1].is_quadratic = False

    # OpenType機能の削除
    print("OpenType機能の削除を実施")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    # ヒント命令の削除
    print("ヒント命令の削除を実施")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.manualHints = 0
        glyph.removePosSub("*")
        glyph.dhints = ()
        glyph.hhints = ()
        glyph.vhints = ()

    # 参照の解除
    print("参照の解除を実施")
    font.unlinkReferences()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.unlinkRef()

    # サブセット化
    print(f"{subset_path}に従いサブセット化を開始")
    with open(subset_path, 'r', encoding='utf-8') as f:
        subset_content = f.read()
    allowed_unichars = set(ord(c) for c in subset_content)
    for glyph in list(font.glyphs()):
        if glyph.unicode not in allowed_unichars:
            font.removeGlyph(glyph)

    # 意図しない空白グリフの削除
    print(f"意図しない空白グリフを削除")
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
        # パスが1つも無ければ空白とみなす
        if len(glyph.layers[1]) == 0:
            target_names.add(glyph.glyphname)
    for name in target_names:
        try:
            font.removeGlyph(name)
        except:
            continue

    # EM及びメトリクス調整
    print("EMサイズおよびメトリクス調整を開始")
    font.em = constants.EMSIZE
    if metrics is None:
        ascent, descent = font.ascent, font.descent
    elif isinstance(metrics, str):
        try:
            a_str, d_str = metrics.split(',')
            ascent, descent = int(a_str), int(d_str)
        except ValueError:
            ascent, descent = font.ascent, font.descent
    elif isinstance(metrics, (tuple, list)):
        ascent, descent = metrics
    else:
        ascent, descent = font.ascent, font.descent
    font.os2_use_typo_metrics = True
    font.ascent = ascent
    font.os2_typoascent = ascent
    font.os2_winascent = ascent
    font.hhea_ascent = ascent
    font.descent = descent
    font.os2_typodescent = -descent
    font.os2_windescent = descent
    font.hhea_descent = -descent
    font.os2_typolinegap = 0
    font.os2_subxsize = int(constants.EMSIZE * 0.635)
    font.os2_subysize = int(constants.EMSIZE * 0.6)
    font.os2_subxoff = 0
    font.os2_subyoff = int(constants.EMSIZE * 0.075)
    font.os2_supxsize = int(constants.EMSIZE * 0.635)
    font.os2_supysize = int(constants.EMSIZE * 0.6)
    font.os2_supxoff = 0
    font.os2_supyoff = int(constants.EMSIZE * 0.34)
    font.os2_strikeysize = int(constants.EMSIZE * 0.050)
    font.os2_strikeypos = int(constants.EMSIZE * 0.03)
    font.hasvmetrics = False
    font.upos = -100
    font.uwidth = 50
    font.round()

    # グリフ内のパスの重なり除去
    print(f"グリフ内のパスの重なり除去を開始")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        print(f"グリフ内のパスの重なりを除去中:{glyph.glyphname:<50}",end="\r")
        glyph.removeOverlap()
        glyph.round()

    # サイズ変換
    if ratio_total_f != 1.0:
        print(f"グリフのサイズ変換({ratio_total}%)を開始")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"グリフのサイズ変換中:{glyph.glyphname:<50}",end="\r")
            glyph.transform(psMat.scale(ratio_total_f,),)
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    # 横幅変換
    if ratio_width_f != 1.0:
        print(f"グリフの横幅変換({ratio_width}%)を開始")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"グリフの横幅変換中:{glyph.glyphname:<50}",end="\r")
            glyph.transform(psMat.scale(ratio_width_f,1.0),)
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    # ウェイト調整
    if weight_offset_f != 0:
        print(f"グリフのウェイト調整({weight_offset}em)を開始")
        font.selection.all()
        processed_glyphs = set()
        for glyph in font.selection.byGlyphs:
            if glyph.glyphname in processed_glyphs:
                continue
            print(f"グリフのウェイト調整中:{glyph.glyphname:<50}",end="\r")
            glyph.changeWeight(weight_offset_f,"auto",0,0,"squish")
            processed_glyphs.add(glyph.glyphname)
            glyph.round()

    # 最適化
    print("グリフの最適化を開始")
    font.selection.all()
    processed_glyphs = set()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in processed_glyphs:
                continue
        print(f"グリフの最適化処理中:{glyph.glyphname:<50}",end="\r")
        glyph.simplify(constants.SIMPLIFY, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        processed_glyphs.add(glyph.glyphname)
        glyph.round()

    # 3次曲線モードを解除
    font.layers[1].is_quadratic = True

    # フォントの出力
    print("最適化済フォントを出力中...")
    directory = os.path.dirname(input_path) or "."
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_file = f"{prefix}{base_name}_s{ratio_total}_w{ratio_width}_b{weight_offset}{suffix}"
    output_path = os.path.join(directory, output_file+".ttf")
    # 匿名化処理
    font.sfnt_names = ()
    font.gasp = ()
    font.sfntRevision = constants.FONT_VERSION
    font.fontname = output_file
    font.fullname = output_file
    font.familyname = output_file
    font.uniqueid = constants.FONT_ID
    font.version = f"{constants.FONT_VERSION}"
    font.copyright = constants.FONT_COPYRIGHT
    font.os2_vendor = constants.FONT_VENDOR
    font.generate(output_path)
    
    # 処理終了
    print(f"--- 最適化完了: {output_path} ---")
    font.close()

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: fontforge -quiet -script optimize_font.py <フォント> [サブセット=subset_jp_skyrim.txt] [サイズ指定%=100] [横幅指定%=100] [ウェイト調整em=0] [メトリクス=None]")
        print("例(小さくする): fontforge -quiet -script optimize_font.py example.ttf subset_jp_skyrim.txt 50")
        print("例(長形にする): fontforge -quiet -script optimize_font.py example.ttf subset_jp_skyrim.txt 100 70")
        print("例(細くする): fontforge -quiet -script optimize_font.py example.ttf subset_jp_skyrim.txt 100 100 -15")
        print("例(メトリクス値を変更): fontforge -quiet -script optimize_font.py example.ttf subset_jp_skyrim.txt 100 100 0 880,150")
    else:
        args = sys.argv[1:]
        main(*args)