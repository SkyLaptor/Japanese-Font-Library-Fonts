import time  # UNIX時間が必要なためdatetime.timeではなくこちらを使用

import pytest
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4

from tests.utilstest import MockGlyph


@pytest.fixture
def create_mock_font():
    """
    テスト用の疑似TTFontを生成・カスタマイズするためのファクトリフィクスチャ
    """

    def _create(mapping=None):
        font = TTFont()
        font.setGlyphOrder([".notdef"])
        # --- head: 基本情報とタイムスタンプ ---
        font['head'] = newTable('head')
        font['head'].unitsPerEm = 1024
        font['head'].created = int(time.time())
        font['head'].modified = int(time.time())
        font['head'].xMin, font['head'].yMin = 0, 0
        font['head'].xMax, font['head'].yMax = 800, 800
        font['head'].flags = 0
        font['head'].indexToLocFormat = 0
        font['head'].glyphDataFormat = 0

        # --- OS/2: ベンダーIDや詳細なメトリクス ---
        font['OS/2'] = newTable('OS/2')
        font['OS/2'].version = 3
        font['OS/2'].achVendID = "TEST"
        font['OS/2'].usWinAscent = 800
        font['OS/2'].usWinDescent = 200
        font['OS/2'].sTypoAscender = 800
        font['OS/2'].sTypoDescender = -200
        font['OS/2'].sTypoLineGap = 90
        font['OS/2'].fsSelection = 0b10000000
        font['OS/2'].xAvgCharWidth = 500
        font['OS/2'].usWeightClass = 400
        font['OS/2'].usWidthClass = 5
        font['OS/2'].fsType = 0
        font['OS/2'].ySubscriptXSize = 0
        font['OS/2'].ySubscriptYSize = 0
        font['OS/2'].ySubscriptXOffset = 0
        font['OS/2'].ySubscriptYOffset = 0
        font['OS/2'].ySuperscriptXSize = 0
        font['OS/2'].ySuperscriptYSize = 0
        font['OS/2'].ySuperscriptXOffset = 0
        font['OS/2'].ySuperscriptYOffset = 0
        font['OS/2'].yStrikeoutSize = 0
        font['OS/2'].yStrikeoutPosition = 0
        font['OS/2'].sFamilyClass = 0
        font['OS/2'].panose = None
        font['OS/2'].ulUnicodeRange1 = 0
        font['OS/2'].ulUnicodeRange2 = 0
        font['OS/2'].ulUnicodeRange3 = 0
        font['OS/2'].ulUnicodeRange4 = 0
        font['OS/2'].ulCodePageRange1 = 0
        font['OS/2'].ulCodePageRange2 = 0

        # --- hhea: 縦方向のメトリクス ---
        font['hhea'] = newTable('hhea')
        font['hhea'].ascent = 800
        font['hhea'].descent = -200
        font['hhea'].lineGap = 90
        font['hhea'].numberOfHMetrics = 0

        # --- name テーブルを追加 ---
        font['name'] = newTable('name')
        font['name'].names = []

        # --- glyf テーブルを追加(CFF/CFF2でも必要) ---
        font['glyf'] = newTable('glyf')
        font['glyf'].glyphs = {
            ".notdef": MockGlyph(0, 0, 0, 0)
        }  # .notdefが無いとTTFとして不正となるため

        # --- cmap テーブルを追加 ---
        font['cmap'] = newTable('cmap')
        subtable = cmap_format_4(4)
        subtable.platformID = 3
        subtable.platEncID = 1
        subtable.language = 0
        subtable.cmap = mapping if mapping is not None else {}
        font['cmap'].tables = [subtable]

        return font

    return _create
