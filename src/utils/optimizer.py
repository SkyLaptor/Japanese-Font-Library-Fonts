from fontTools import subset
from fontTools.ttLib import TTFont

from utils import BLANK_GLYPHS, is_ttf, reload_font
from utils.models import RemoveEmptyResult


def remove_empty_glyphs(font_obj: TTFont) -> RemoveEmptyResult:
    """
    # フォントから空白グリフを消去する。

    消してはならない空白グリフ(.notdefやスペースなど)は保護消去されません。
    グリフID(順序)が変更されます。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 空白グリフ消去結果
    :rtype: RemoveEmptyResult
    """
    all_glyphs = font_obj.getGlyphOrder()
    removed_glyphs = []

    # 削除対象の特定
    if is_ttf(font_obj):
        # TTFの場合
        glyf_table = font_obj['glyf']
        for name in all_glyphs:
            # 空白が正しいグリフはスルーします
            if name in BLANK_GLYPHS:
                continue

            # 輪郭(contours)が0個、かつコンポーネント(参照)も持っていないものを抽出
            glyph = glyf_table[name]
            if glyph.numberOfContours == 0 and not hasattr(glyph, "components"):
                removed_glyphs.append(name)

    elif is_ttf(font_obj):
        # OTFの場合
        charstrings = font_obj['CFF '].cff.topDictIndex[0].CharStrings
        for name in all_glyphs:
            # 空白が正しいグリフはスルーします
            if name in BLANK_GLYPHS:
                continue
            if len(charstrings[name].bytecode) <= 1:  # ほぼデータなし
                removed_glyphs.append(name)

    # サブセット機能を使って削除を実行
    # 残すべきグリフ = (全てのグリフ) - (削除対象)
    keep_glyphs = [g for g in all_glyphs if g not in removed_glyphs]

    # サブセッタの設定と実行
    options = subset.Options()
    options.layout_features = ["*"]  # OpenType機能（合字、カーニング等）を維持
    options.name_IDs = ["*"]  # フォント名や著作権情報をすべて維持
    options.notdef_outline = True  # .notdef（豆腐）の形を維持
    options.glyph_names = True  # グリフ名を維持（デバッグしやすくなる）
    options.legacy_kern = True  # 古い形式のカーニングも維持
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=keep_glyphs)
    subsetter.subset(font_obj)

    return RemoveEmptyResult(
        font_obj=reload_font(font_obj),
        all_glyphs=all_glyphs,
        removed_glyphs=removed_glyphs,
    )


def remove_black_circles(font_obj):
    """
    フォントから黒丸（●）と思われるグリフを検出し、削除する。
    ただし、. や , などの基本文字は除外する。
    """
    glyf_table = font_obj['glyf']
    cmap = font_obj.getBestCmap()

    # 1. 漢字（CJK Unified Ideographs）の範囲を定義
    # 一般的な漢字の範囲: U+4E00 - U+9FFF
    # (必要に応じて拡張 A: 3400-4DBF も含めることがありますが、まずは基本の 4E00-9FFF を「判定対象」にします)
    kanji_range = range(0x4E00, 0x9FFF + 1)

    # 2. ホワイトリスト（保護対象）を作成
    keep_glyphs = set()
    keep_glyphs.add('.notdef')

    for code, name in cmap.items():
        # 「漢字の範囲」に入っていない文字はすべて保護！
        if code not in kanji_range:
            keep_glyphs.add(name)

    removed_count = 0
    glyphs_to_remove = []

    # 3. 判定ループ（漢字エリアにあるグリフだけをチェック）
    for glyph_name in font_obj.getGlyphOrder():
        if glyph_name in keep_glyphs:
            continue

        if glyph_name not in glyf_table:
            continue

        glyph = glyf_table[glyph_name]

        # 黒丸判定（サイズを 90 まで下げて、小さなゴミも逃さない）
        if glyph.numberOfContours == 1:
            xMin, yMin, xMax, yMax = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
            width = xMax - xMin
            height = yMax - yMin

            aspect_ratio = width / height if height != 0 else 0
            if 0.8 < aspect_ratio < 1.2 and width > 90:
                glyphs_to_remove.append(glyph_name)

    # 4. 実行（物理削除せず、中身を空にする）
    from fontTools.ttLib.tables._g_l_y_f import Glyph

    for g_name in glyphs_to_remove:
        # cmapからも消す（検索に引っかからないようにする）
        for code in [k for k, v in cmap.items() if v == g_name]:
            del cmap[code]
        # 中身を空にする
        glyf_table[g_name] = Glyph()
        removed_count += 1

    return reload_font(font_obj)
