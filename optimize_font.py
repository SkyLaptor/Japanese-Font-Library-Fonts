#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os


def process_font(input_file, subset_txt, ratio_total, ratio_width, weight_offset):
    """フォントを加工する
           input_file: 加工対象のフォントファイル
           subset_txt: サブセット対象文字列ファイル
           ratio_total: サイズ指定(%)
           ratio_width: 横幅指定(%)
           weight_offset: ウェイト調整値 正の値で太く、負の値で細く
           return: なし
    """

    if not os.path.exists(input_file) or not os.path.exists(subset_txt):
        print("エラー: フォントファイルが見つかりません。")
        return

    # パラメータ解析
    ratio_width_f = float(ratio_width) / 100.0
    ratio_total_f = float(ratio_total) / 100.0
    weight_offset_f = float(weight_offset)

    # 処理開始
    print(f"--- 最適化開始: {input_file} ---")
    print(f"設定: サブセット{subset_txt}, サイズ{ratio_total}%, 横幅{ratio_width}%, ウェイト{weight_offset}em")
    font = fontforge.open(input_file,("fstypepermitted",))
    # 計算精度を向上させるため、前面レイヤを3次曲線モードへ移行
    font.layers[1].is_quadratic = False

    # OpenType機能の削除
    print("OpenType機能の削除中...")
    for lookup in font.gsub_lookups:
        font.removeLookup(lookup)
    for lookup in font.gpos_lookups:
        font.removeLookup(lookup)

    # ヒント命令の削除
    print("ヒント命令の削除中...")
    font.selection.none()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        glyph.manualHints = 0
        glyph.dhints = ()
        glyph.hhints = ()
        glyph.vhints = ()

    # 参照の解除
    print("参照の解除中...")
    font.unlinkReferences()

    # サブセット化
    print(f"サブセット化を実行中...: {subset_txt}")
    with open(subset_txt, 'r', encoding='utf-8') as f:
        subset_content = f.read()
    allowed_unichars = set(ord(c) for c in subset_content)
    for glyph in list(font.glyphs()):
        if glyph.unicode not in allowed_unichars:
            font.removeGlyph(glyph)

    # 意図しない空白グリフの削除
    print(f"意図しない空白グリフを削除中...")
    protected_glyphs = [
        "space", "uni3000", "ideographicspace", ".notdef", 
        "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
        "emspace", "enspace", "thinspace", "hairspace",
        "uni2003", "uni2002", "uni2009", "uni200A",
        "zerowidthspace", "uni200B"
    ]
    target_names = set()
    font.selection.none()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        if glyph.glyphname in protected_glyphs:
            continue
        if len(glyph.layers[1]) == 0:
            target_names.add(glyph.glyphname)
    for name in target_names:
        try:
            font.removeGlyph(name)
        except:
            continue

    # EM及びメトリクス調整
    print("EMサイズおよびメトリクス調整を実行中...")
    font.em = 1024
    font.ascent = 880
    font.descent = 144
    font.round()

    # サイズ変換
    if ratio_total_f != 1.0:
        print(f"グリフのサイズを変換中...: {ratio_total_f:.2f}")
        font.selection.none()
        font.selection.all()
        for glyph in font.glyphs():
            glyph.psMat.scale(ratio_total_f,ratio_total_f)

    # 横幅変換
    if ratio_width_f != 1.0:
        print(f"グリフの横幅を変換中...: {ratio_width_f:.2f}")
        font.selection.all()
        matrix_width = psMat.scale(ratio_width_f, 1.0)
        font.transform(matrix_width)
        for glyph in font.glyphs():
            # 左右の余白を均等に分配する
            current_width = glyph.width
            lb = glyph.left_side_bearing
            rb = glyph.right_side_bearing
            average_bearing = (lb + rb) / 2
            glyph.left_side_bearing = int(average_bearing)
            glyph.right_side_bearing = int(average_bearing)
            # 送り幅を元の数値に戻して固定し、変形による意図しない拡大を防止する
            glyph.width = current_width

    # ウェイト調整
    if weight_offset_f != 0:
        print(f"グリフのウェイトを調整中...: {weight_offset}")
        font.selection.none()
        font.selection.all()
        for glyph in font.selection.byGlyphs:
            glyph.changeWeight(weight_offset_f,"auto",0,0,"squish")

    # 最適化
    print("グリフの最適化を実行中...")
    # TTF出力のため、3次曲線モードを解除
    font.layers[1].is_quadratic = True
    font.selection.none()
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        # パスを簡略化
        glyph.simplify(0.5, ("choosehv", "mergelines", "nearlyhvlines", "removesingletonpoints"), 0.02, 0.1, 0)
        # 座標を整数丸め
        glyph.round()

    # フォントの出力
    print("最適化済フォントを出力中...")
    directory = os.path.dirname(input_file) or "."
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"mod_{base_name}_s{ratio_total}_w{ratio_width}_b{weight_offset}.ttf"
    output_path = os.path.join(directory, output_file)
    font.generate(output_path)
    
    # 処理終了
    print(f"--- 最適化完了: {output_path} ---")
    font.close()


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("使用法: fontforge -script build_master.py <フォント> <サブセット> <大きさ%> <横幅%> <ウェイトem>")
        print("例(小さくする): fontforge -script ... example.ttf subset.txt 50 100 0")
        print("例(長形にする): fontforge -script ... example.ttf subset.txt 100 70 0")
        print("例(細くする): fontforge -script ... example.ttf subset.txt 100 100 -15")
    else:
        process_font(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])