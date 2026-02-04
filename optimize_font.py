#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os

# ASCENT+DESCENTは1024にすること。
ASCENT = 880
DESCENT = 144

def process_font(input_file, subset_txt, ratio_total, ratio_width, weight_offset):
    """フォントを加工する
           input_file: 加工対象のフォントファイル
           subset_txt: サブセット対象文字列ファイル
           ratio_total: サイズ指定(%)
           ratio_width: 横幅指定(%)
           weight_offset: ウェイト調整値
           return: なし
    """

    if not os.path.exists(input_file) or not os.path.exists(subset_txt):
        print("エラー: フォントファイルが見つかりません。")
        return

    # パラメータ解析
    ratio_width_f = float(ratio_width) / 100.0
    ratio_total_f = float(ratio_total) / 100.0
    weight_offset_f = float(weight_offset) # 正の値で太く、負の値で細く

    # 処理開始
    print(f"--- 最適化開始: {input_file} ---")
    print(f"設定: サブセット{subset_txt}, サイズ{ratio_total}%, 横幅{ratio_width}%, ウェイト{weight_offset}em")
    font = fontforge.open(input_file,("fstypepermitted",))
    # 計算精度を向上させるため、前面レイヤを3次曲線モードへ移行
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
        glyph.dhints = ()
        glyph.hhints = ()
        glyph.vhints = ()

    # 参照の解除
    print("参照の解除を実施")
    font.unlinkReferences()

    # サブセット化
    print(f"{subset_txt}に従いサブセット化を開始")
    with open(subset_txt, 'r', encoding='utf-8') as f:
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
    font.em = ASCENT + DESCENT
    font.os2_use_typo_metrics = True
    font.ascent = ASCENT
    font.os2_typoascent = ASCENT
    font.os2_winascent = ASCENT
    font.hhea_ascent = ASCENT
    font.descent = DESCENT
    font.os2_typodescent = -DESCENT
    font.os2_windescent = DESCENT
    font.hhea_descent = -DESCENT
    font.os2_typolinegap = 0
    font.round()
    glyph.correctDirection()


    # グリフ内のパスの重なり除去
    print(f"グリフ内のパスの重なり除去を開始")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        print(f"グリフ内のパスの重なりを除去中:{glyph.glyphname} (U+{glyph.unicode:04X})", end="\r")
        glyph.removeOverlap()
        glyph.round()
        glyph.correctDirection()

    # サイズ変換
    if ratio_total_f != 1.0:
        print(f"グリフのサイズ変換({ratio_total}%)を開始")
        font.selection.all()
        for glyph in font.selection.byGlyphs:
            print(f"グリフのサイズを変換中:{glyph.glyphname} (U+{glyph.unicode:04X})", end="\r")
            glyph.transform(psMat.compose(psMat.scale(ratio_total_f,ratio_total_f),psMat.translate(0,0)))
            glyph.round()
            glyph.correctDirection()

    # 横幅変換
    if ratio_width_f != 1.0:
        print(f"グリフの横幅変換({ratio_width}%)を開始")
        font.selection.all()
        for glyph in font.selection.byGlyphs:
            print(f"グリフの横幅を変換中:{glyph.glyphname} (U+{glyph.unicode:04X})", end="\r")
            glyph.transform(psMat.compose(psMat.scale(ratio_width_f,1.0),psMat.translate(0,0)))
            glyph.round()
            glyph.correctDirection()

    # ウェイト調整
    if weight_offset_f != 0:
        print(f"グリフのウェイト調整({weight_offset}em)を開始")
        font.selection.all()
        for glyph in font.selection.byGlyphs:
            print(f"グリフのウェイトを調整中:{glyph.glyphname} (U+{glyph.unicode:04X})", end="\r")
            glyph.changeWeight(weight_offset_f,"auto",0,0,"squish")
            glyph.round()
            glyph.correctDirection()

    # 最適化
    print("グリフの最適化を開始")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        print(f"グリフの最適化処理中:{glyph.glyphname} (U+{glyph.unicode:04X})", end="\r")
        glyph.simplify(0.5, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        glyph.round()
        glyph.correctDirection()

    # フォントの出力
    print("最適化済フォントを出力中...")
    directory = os.path.dirname(input_file) or "."
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"{base_name}_s{ratio_total}_w{ratio_width}_b{weight_offset}"
    output_path = os.path.join(directory, output_file+".ttf")
    # フォント情報を書き換え
    font.sfnt_names = ()
    font.sfntRevision = 1.0
    font.fontname = output_file
    font.fullname = output_file
    font.familyname = output_file
    font.uniqueid = 1
    font.version = "1.000"
    font.copyright = "NONE"
    font.os2_vendor = "NONE"
    # TTF出力のため、3次曲線モードを解除
    font.layers[1].is_quadratic = True
    font.generate(output_path)
    
    # 処理終了
    print(f"--- 最適化完了: {output_path} ---")
    font.close()


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("使用法: fontforge -quiet -script build_master.py <フォント> <サブセット> <大きさ%> <横幅%> <ウェイトem>")
        print("例(小さくする): fontforge -quiet -script ... example.ttf subset.txt 50 100 0")
        print("例(長形にする): fontforge -quiet -script ... example.ttf subset.txt 100 70 0")
        print("例(細くする): fontforge -quiet -script ... example.ttf subset.txt 100 100 -15")
    else:
        process_font(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])