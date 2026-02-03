#!/usr/bin/env fontforge
import fontforge
import psMat
import sys
import os

def process_font(input_file, subset_txt, ratio_h, ratio_total, weight_offset):
    if not os.path.exists(input_file) or not os.path.exists(subset_txt):
        print("エラー: 必要なファイルが見つかりません。")
        return

    # パラメータ解析
    scale_h = float(ratio_h) / 100.0
    scale_total = float(ratio_total) / 100.0
    w_offset = float(weight_offset) # 正の値で太く、負の値で細く

    print(f"--- 最適化開始: {input_file} ---")
    print(f"設定: 長体{ratio_h}%, 拡大{ratio_total}%, ウェイト調整{weight_offset}")
    
    font = fontforge.open(input_file)
    font.em = 1024

    # サブセット化
    print(f"サブセット適用中: {subset_txt}")
    with open(subset_txt, 'r', encoding='utf-8') as f:
        subset_content = f.read()
    
    # 必要なUnicodeの集合を作成
    allowed_unichars = set(ord(c) for c in subset_content)
    
    # フォント内の全グリフをスキャンして削除
    print("不要なグリフを物理的に削除中...")
    for glyph in list(font.glyphs()): # リスト化してループ回すのが安全
        if glyph.unicode not in allowed_unichars:
            # 物理削除。これが最も確実です。
            font.removeGlyph(glyph)

    # 変形前の事前洗浄
    print("変形前のパス最適化を実行中...")
    font.selection.all()
    for glyph in font.selection.byGlyphs:
        # 変形前に細かい点を取り除き、計算の矛盾を防ぐ
        glyph.simplify(1.0)
        glyph.removeOverlap()
        glyph.correctDirection()

    # ウェイト調整 (太らせ / 細らせ)
    if w_offset != 0:
        print(f"ウェイト調整中 ({weight_offset})...")
        font.selection.all()
        # 引数をシンプルに w_offset だけ、あるいは標準的な引数構成に変更します
        try:
            # 最新の安定した呼び出し方に修正
            font.changeWeight(w_offset) 
        except TypeError:
            # 万が一上記で失敗する場合の予備
            font.changeWeight(w_offset, "custom")
            
        font.removeOverlap()
        font.correctDirection()

    # サイズと長体の変換
    final_scale_x = scale_total * scale_h
    final_scale_y = scale_total

    if final_scale_x != 1.0 or final_scale_y != 1.0:
        print(f"スケール変換中: X={final_scale_x:.2f}, Y={final_scale_y:.2f}")
        font.selection.all()
        matrix = psMat.scale(final_scale_x, final_scale_y)
        font.transform(matrix)

    # メトリクス固定
    font.ascent = 880
    font.descent = 144

    # センター配置
    print("文字の位置を中央に調整中...")
    for glyph in font.glyphs():
        # 現在の「送り幅(width)」を取得
        current_width = glyph.width
        # 現在の「左余白(lb)」と「右余白(rb)」を取得
        lb = glyph.left_side_bearing
        rb = glyph.right_side_bearing
        
        # 左右の余白を足して2で割り、均等に分配する
        # これにより、全体の幅を変えずに文字を中央に寄せます
        average_bearing = (lb + rb) / 2
        glyph.left_side_bearing = int(average_bearing)
        glyph.right_side_bearing = int(average_bearing)
        
        # 最後に送り幅を元の数値に戻して固定（変形による意図しない拡大を防止）
        glyph.width = current_width

    # 上下位置の調整（ベースラインへの接地）
    print("文字の上下位置を調整中...")
    for glyph in font.glyphs():
        # グリフの境界（上下左右の端）を取得
        # (x_min, y_min, x_max, y_max)
        bbox = glyph.boundingBox()
        y_min = bbox[1]
        
        # y_min（文字の底）が 0 になるように垂直移動させる
        # これにより、縮小しても文字が基準線に乗るようになります
        if y_min != 0:
            matrix = psMat.translate(0, -y_min)
            glyph.transform(matrix)


    # 最終最適化
    print("構造の最終再構築を実行中...")
    for glyph in font.selection.byGlyphs:
        # パスの重なりを物理的に一度リセット
        glyph.removeOverlap()
        glyph.correctDirection()
        
        # 構造のクリーンアップ（最新版の機能を安全に呼び出し）
        try:
            glyph.canonicalStart()
            glyph.canonicalContours()
        except:
            pass

        # 冗長な点を削除（フラグを使わず、数値のみで実行）
        # 引数を 1.0 にすることで、最新エンジンのデフォルト最適化を適用
        glyph.simplify(1.0)
        
        # 最終的な重なり除去（白抜け防止）
        glyph.removeOverlap()
        glyph.correctDirection()
        
        # 座標の整数化
        glyph.round()

    # 出力パスの生成
    # input_file からディレクトリとファイル名を取り出します
    directory = os.path.dirname(input_file)
    # もしディレクトリが空（カレントディレクトリ）なら '.' を補完
    if not directory:
        directory = "."
        
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    
    # 命名規則: 元の名前_W{幅}.ttf
    output_file = f"{base_name}_W{ratio_h}.ttf"
    output_path = os.path.join(directory, output_file)

    # 保存
    print(f"--- 最適化完了: {output_path} ---")
    font.generate(output_path)
    font.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("使用法: fontforge -script build_master.py <font> <subset> <長体%> <大きさ%> <ウェイト値>")
        print("例(細くする): fontforge -script ... font.otf subset.txt 100 100 -10")
    else:
        process_font(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])