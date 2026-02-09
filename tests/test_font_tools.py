import pytest
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._g_l_y_f import Glyph
from src.utils.font_tools import clean_empty_glyphs, CleanupResult


@pytest.fixture
def mock_font():
    """テスト用の最小構成TTFフォントをメモリ上に作成"""
    font = TTFont()
    glyph_names = [".notdef", "space", "uni3042", "empty_junk"]
    font.setGlyphOrder(glyph_names)

    # --- 1. glyfテーブル（描画データ）の設定 ---
    font["glyf"] = newTable("glyf")
    # ↓ この一行を追加：テーブル側にも順番を教えてあげる
    font["glyf"].glyphOrder = glyph_names

    # 「uni3042（あ）」だけに輪郭を1つ作り、他は空にする
    glyph_with_contour = Glyph()
    glyph_with_contour.numberOfContours = 1

    font["glyf"].glyphs = {
        ".notdef": Glyph(),
        "space": Glyph(),
        "uni3042": glyph_with_contour,
        "empty_junk": Glyph(),
    }

    # --- 2. 必須テーブルの最小設定 ---
    # head, loca, maxp, hmtx, cmap を作成
    font["head"] = newTable("head")
    font["loca"] = newTable("loca")
    font["maxp"] = newTable("maxp")
    font["hmtx"] = newTable("hmtx")
    font["cmap"] = newTable("cmap")

    # 最低限必要な属性をセット
    font["maxp"].numGlyphs = len(glyph_names)
    font["hmtx"].metrics = {n: (500, 0) for n in glyph_names}

    # 実際はダミーのcmap（Unicode対応表）も作っておくとsubsetが安定します
    from fontTools.ttLib.tables._c_m_a_p import cmap_format_4

    cmap4 = cmap_format_4(4)
    cmap4.platformID = 3
    cmap4.platEncID = 1
    cmap4.language = 0
    cmap4.cmap = {0x0020: "space", 0x3042: "uni3042"}
    font["cmap"].tables = [cmap4]

    return font


@pytest.mark.parametrize(
    "glyph_name, should_remain",
    [
        ("uni3042", True),  # 実体がある（残るべき）
        ("space", True),  # 実体はないが保護リスト（残るべき）
        ("empty_junk", False),  # 実体もなく保護もされない（消えるべき）
    ],
)
def test_glyph_retention(mock_font, glyph_name, should_remain):
    """特定のグリフが期待通りに残るか、あるいは消えるかをテスト"""
    # 実行
    result = clean_empty_glyphs(mock_font)

    # 1. 戻り値が正しいデータクラスか
    assert isinstance(result, CleanupResult)

    # 2. 実際にフォントから消去（または維持）されているか
    remaining_glyphs = result.font_obj.getGlyphOrder()

    if should_remain:
        assert glyph_name in remaining_glyphs
        assert glyph_name not in result.removed_glyphs
    else:
        assert glyph_name not in remaining_glyphs
        assert glyph_name in result.removed_glyphs


def test_result_contains_all_info(mock_font):
    """戻り値のデータクラスに必要な情報が揃っているか"""
    result = clean_empty_glyphs(mock_font)

    # 削除前の全リストが保持されているか
    assert "uni3042" in result.all_glyphs
    assert "empty_junk" in result.all_glyphs
    # 削除されたリストに正しく入っているか
    assert "empty_junk" in result.removed_glyphs
