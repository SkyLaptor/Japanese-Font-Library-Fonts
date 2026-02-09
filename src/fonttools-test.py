from fontTools.ttLib import TTFont


def identify_empty_glyphs(font_path):
    font = TTFont(font_path)
    empty_glyphs = []

    # TTFの場合（'glyf'テーブルを確認）
    if "glyf" in font:
        glyf_table = font["glyf"]
        for name in font.getGlyphOrder():
            # グリフに輪郭(numberOfContours)がない、かつコンポーネントでもない場合
            if not glyf_table[name].numberOfContours == 0:
                continue

            # スペース(uni0020)などは除外したい場合、ここでフィルタリング
            if name in [".notdef", "space", "uni0020", "nbspace"]:
                continue

            empty_glyphs.append(name)

    # OTFの場合（'CFF 'テーブルを確認）
    elif "CFF " in font:
        cff = font["CFF "].cff.topDictIndex[0]
        charstrings = cff.CharStrings
        for name in font.getGlyphOrder():
            if name in charstrings:
                # パスデータがほぼ空（リターンのみなど）のものを判定
                if len(charstrings[name].bytecode) <= 1:
                    if name in [".notdef", "space", "uni0020", "nbspace"]:
                        continue
                    empty_glyphs.append(name)

    return empty_glyphs


# 実行テスト
font_file = "your_font.ttf"  # ここを実際のファイル名に書き換えてください
empties = identify_empty_glyphs(font_file)

print(f"見つかった空のグリフ（計 {len(empties)} 個）:")
print(empties[:100])  # 最初の100個だけ表示

# 日本語の代表的な文字が「空リスト」に入ってしまっていないか確認
check_list = ["uni3042", "uni4E9C", "a", "A"]  # あ, 亜, a, A
for char in check_list:
    if char in empties:
        print(f"⚠️ 警告: '{char}' も空だと判定されています！")
