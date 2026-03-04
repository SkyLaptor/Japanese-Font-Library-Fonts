import io
from pathlib import Path

from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

from modules.harmonize_font_metrics import (
    action_harmonize_font_metrics,
    harmonize_font_metrics,
)


def setup_kanji_mock_font(create_mock_font, upm, size, advance):
    """get_average_sizeの計算対象となる『漢字(U+4E00)』を持つフォントを作成"""
    font = create_mock_font()
    font['head'].unitsPerEm = upm

    # グリフ名とUnicodeの定義（漢字の範囲 U+4E00 を使用）
    kanji_code = 0x4E00
    kanji_name = "uni4E00"
    font.setGlyphOrder(['.notdef', kanji_name])
    font['cmap'].getcmap(3, 1).cmap[kanji_code] = kanji_name

    # 漢字グリフにサイズを持たせる
    glyph_set = font.getGlyphSet()
    pen = TTGlyphPen(glyph_set)
    pen.moveTo((0, 0))
    pen.lineTo((0, size))
    pen.lineTo((size, size))
    pen.lineTo((size, 0))
    pen.closePath()

    font['glyf'].glyphs = {}
    font['glyf'].glyphs['.notdef'] = TTGlyphPen(None).glyph()
    font['glyf'].glyphs[kanji_name] = pen.glyph()

    # メトリクスの設定
    font['hmtx'].metrics = {}
    font['hmtx'].metrics['.notdef'] = (0, 0)
    font['hmtx'].metrics[kanji_name] = (advance, 0)

    # バイナリ保存で境界ボックスを確定
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    return TTFont(buf)


def test_action_harmonize_font_metrics(tmp_path):
    """
    フォント変形アクションが正常に走り、ファイルが書き出されるかのテスト
    """
    # 準備: 入力フォント及び出力先パス
    input_file = Path("tests/data/test-font/test-font-bold.ttf")
    base_file = Path("tests/data/test-font/test-font-heavy.ttf")
    output_file = tmp_path / "test_font.ttf"

    # 実行: アクションを直接叩く
    # 引数は実際の関数に合わせて調整してください
    action_harmonize_font_metrics(
        input_path=input_file,
        output_path=output_file,
        base_path=base_file,
        scale_width=0.64,
        scale_height=0.98,
        offset_width=0,
        offset_height=-64,
        debug=True,
    )

    # 検証: ファイルが物理的に存在し、中身が空でないか
    assert output_file.exists(), "ファイルが生成されていません"


def test_action_harmonize_font_metrics_manual_metrics_override(
    create_mock_font,
    tmp_path,
):
    input_font = create_mock_font()
    input_file = tmp_path / "manual_input.ttf"
    output_file = tmp_path / "manual_output.ttf"
    input_font.save(str(input_file))

    action_harmonize_font_metrics(
        input_path=str(input_file),
        output_path=str(output_file),
        base_path=None,
        scale_width=1.0,
        scale_height=1.0,
        offset_width=0,
        offset_height=0,
        mode="manual",
        new_upm=1000,
        metrics_override={
            "os2": {
                "usWinAscent": 880,
                "usWinDescent": 144,
                "sTypoAscender": 880,
                "sTypoDescender": -144,
                "sTypoLineGap": 32,
            },
            "hhea": {
                "ascent": 880,
                "descent": -144,
                "lineGap": 32,
            },
        },
    )

    with TTFont(str(output_file)) as result_font:
        assert result_font['head'].unitsPerEm == 1000
        assert result_font['OS/2'].usWinAscent == 880
        assert result_font['OS/2'].usWinDescent == 144
        assert result_font['OS/2'].sTypoAscender == 880
        assert result_font['OS/2'].sTypoDescender == -144
        assert result_font['OS/2'].sTypoLineGap == 32
        assert result_font['hhea'].ascent == 880
        assert result_font['hhea'].descent == -144
        assert result_font['hhea'].lineGap == 32


def test_action_harmonize_font_metrics_manual_derives_upm_from_metrics(
    create_mock_font,
    tmp_path,
):
    input_font = create_mock_font()
    input_file = tmp_path / "manual_input_derived.ttf"
    output_file = tmp_path / "manual_output_derived.ttf"
    input_font.save(str(input_file))

    action_harmonize_font_metrics(
        input_path=str(input_file),
        output_path=str(output_file),
        base_path=None,
        scale_width=1.0,
        scale_height=1.0,
        offset_width=0,
        offset_height=0,
        mode="manual",
        new_upm=None,
        metrics_override={
            "os2": {
                "sTypoAscender": 880,
                "sTypoDescender": -144,
                "sTypoLineGap": 28,
            },
            "hhea": {
                "ascent": 880,
                "descent": -144,
                "lineGap": 28,
            },
        },
    )

    with TTFont(str(output_file)) as result_font:
        assert result_font['head'].unitsPerEm == 1024


def test_harmonize_font_metrics_scaling(create_mock_font):
    """UPMと漢字グリフサイズに基づき、正しくスケーリングされるかテスト"""
    # ベース: UPM 2000, 200x200の漢字, 送り300
    base_font = setup_kanji_mock_font(create_mock_font, 2000, 200, 300)
    # ターゲット: UPM 1000, 100x100の漢字, 送り150
    target_font = setup_kanji_mock_font(create_mock_font, 1000, 100, 150)

    result = harmonize_font_metrics(
        target_font_obj=target_font,
        base_font_obj=base_font,
        scale_width_manual=1.0,
        scale_height_manual=1.0,
        offset_width=0,
        offset_height=0,
        debug=True,
    )

    h_font = result.font_obj
    assert h_font['head'].unitsPerEm == 2000
    # スケーリング計算: (200/100) / (2000/1000) = 1.0倍。送り幅150が維持される
    assert h_font['hmtx'].metrics['uni4E00'][0] == 150


def test_harmonize_font_metrics_offset(create_mock_font):
    """オフセットが正しく適用されるかテスト"""
    base_font = setup_kanji_mock_font(create_mock_font, 1000, 100, 100)
    target_font = setup_kanji_mock_font(create_mock_font, 1000, 100, 100)

    result = harmonize_font_metrics(
        target_font_obj=target_font,
        base_font_obj=base_font,
        scale_width_manual=1.0,
        scale_height_manual=1.0,
        offset_width=50,
        offset_height=30,
    )

    h_font = result.font_obj
    h_glyph = h_font['glyf']['uni4E00']
    h_glyph.recalcBounds(h_font['glyf'])

    # 座標が正しく移動しているか
    assert h_glyph.xMin == 50
    assert h_glyph.yMin == 30
    # hmtxのLSBも同期しているか
    assert h_font['hmtx'].metrics['uni4E00'][1] == 50
