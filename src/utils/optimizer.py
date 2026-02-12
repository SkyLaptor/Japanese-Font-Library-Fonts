from fontTools import subset
from fontTools.ttLib import TTFont

from utils import BLANK_GLYPHS, is_otf, is_ttf, reload_font
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

    elif is_otf(font_obj):
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

    return RemoveEmptyResult(reload_font(font_obj), all_glyphs, removed_glyphs)


# TODO: 必要にかられたらちゃんと作る
def clean_weird_glyphs(font_obj: TTFont, target_w=350, target_h=350) -> TTFont:
    """
    特定のサイズ(350x350)を持つ『●』っぽいゴミデータを削除する。
    ただし、句読点などの重要な文字は保護する。
    """
    glyf_table = font_obj["glyf"]
    cmap = font_obj.getBestCmap()
    # 保護リスト: 句読点、中黒、読点など（Unicodeで指定）
    protected_codes = {0x3001, 0x3002, 0x30FB, 0x002E, 0x00B7}

    # 逆引きマップ（名前からコードを特定するため）
    name_to_code = {name: code for code, name in cmap.items()}

    removed_count = 0
    for name in font_obj.getGlyphOrder():
        if name not in glyf_table:
            continue

        g = glyf_table[name]
        if hasattr(g, "xMax"):
            w = g.xMax - g.xMin
            h = g.yMax - g.yMin

            # 条件: サイズが350x350で、かつ保護リストに入っていない
            if w == target_w and h == target_h:
                code = name_to_code.get(name)
                if code not in protected_codes:
                    # グリフの中身を空にする（輪郭データを消去）
                    g.numberOfContours = 0
                    if hasattr(g, "data"):
                        del g.data
                    removed_count += 1

    if removed_count > 0:
        # print(f"Removed {removed_count} placeholder glyphs ({target_w}x{target_h}).")
        pass

    return reload_font(font_obj)


# TODO: これいる？
def remove_hinting(font_obj: TTFont) -> TTFont:
    """
    フォントからヒンティング関連のテーブルを削除し、
    スケーリングによる表示の乱れを防止する。
    """
    # 削除対象のテーブル（ヒンティング、プログラム、ガスプ等）
    hinting_tables = [
        "gasp",  # Grid-fitting and Scan-conversion Procedure
        "prep",  # Control Value Program
        "fpgm",  # Font Program
        "cvt ",  # Control Value Table
        "hdmx",  # Horizontal Device Metrics (ピクセル単位の幅データ)
        "LTSH",  # Linear Threshold table
    ]

    removed = []
    for tag in hinting_tables:
        if tag in font_obj:
            del font_obj[tag]
            removed.append(tag)

    # glyfテーブル内の各グリフの命令データ(instructions)も空にする
    if "glyf" in font_obj:
        for glyph in font_obj["glyf"].glyphs.values():
            if hasattr(glyph, "program"):
                glyph.program = None

    if removed:
        # print(f"Removed hinting tables: {', '.join(removed)}")
        pass

    # print("Glyph instructions cleared.")

    return reload_font(font_obj)
