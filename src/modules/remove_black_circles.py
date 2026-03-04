# Dependencies: FFDec=False, FontForge=False

from fontTools.ttLib import TTFont

from core.font_processor import reopen_font
from utils.file_io import save_font

REMOVE_TARGET_SIZE = 90
REMOVE_TARGED_SIZE = REMOVE_TARGET_SIZE


def action_remove_black_circles(
    input_path: str, output_path: str, target_size: int, debug: bool = False, **_
):
    with TTFont(input_path) as input_font_obj:
        removed_font_obj = remove_black_circles(input_font_obj, target_size, debug)
        if output_path is not None:
            saved_output_path = save_font(
                removed_font_obj,
                input_path,
                output_path,
                suffix="_black_circles_removed",
            )
            print(f"フォントを保存しました: {saved_output_path}")


def remove_black_circles(
    font_obj: TTFont, target_size: int = REMOVE_TARGET_SIZE, debug: bool = False
) -> TTFont:
    """
    フォントから不正な黒丸（●）と思われるグリフを検出し削除する

    誤消去防止のため漢字範囲のみに絞っています。
    出力後、fontforgeなどで個別に目視確認を行ってください。
    ほぼ「[Lore-friendly fonts - font_jp_skyrim」MODから取り出したフォントのための機能です。

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param output_path: 出力ファイルパス
    :type output_path: str
    :param target_size: 削除対象とするグリフサイズ
    :type target_size: int
    :param debug: デバッグモード
    :type debug: bool
    :return: クリーニング済みフォントオブジェクト
    :rtype: TTFont
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

        # 黒丸判定
        if glyph.numberOfContours == 1:
            xMin, yMin, xMax, yMax = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
            width = xMax - xMin
            height = yMax - yMin

            aspect_ratio = width / height if height != 0 else 0
            if 0.8 < aspect_ratio < 1.2 and width > target_size:
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

    return reopen_font(font_obj)
