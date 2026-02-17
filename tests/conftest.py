import time  # UNIX時間が必要なためdatetime.timeではなくこちらを使用

import pytest
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.ttLib.tables._g_l_y_f import Glyph
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.ttLib.tables.O_S_2f_2 import Panose


@pytest.fixture
def create_mock_font():
    """
    テスト用の疑似TTFontを生成・カスタマイズするためのファクトリフィクスチャ
    """

    ascent = 880
    descent = -144
    upm = ascent + abs(descent)
    linegap = 90

    def _create(mapping=None):
        font = TTFont()
        font.setGlyphOrder([".notdef"])
        # --- head: 基本情報とタイムスタンプ ---
        font['head'] = newTable('head')
        head = font['head']
        head.tableVersion = 1.0
        head.fontRevision = 1.0
        head.checkSumAdjustment = 0
        head.magicNumber = 0x5F0F3CF5
        head.flags = 0
        head.unitsPerEm = upm
        head.created = int(time.time())
        head.modified = int(time.time())
        head.xMin, head.yMin = 0, 0
        head.xMax, head.yMax = ascent, ascent
        head.macStyle = 0
        head.lowestRecPPEM = 3
        head.fontDirectionHint = 2
        head.indexToLocFormat = 0
        head.glyphDataFormat = 0

        # --- OS/2: ベンダーIDや詳細なメトリクス ---
        font['OS/2'] = newTable('OS/2')
        os2 = font['OS/2']
        os2.version = 3
        os2.achVendID = "TEST"
        os2.usWinAscent = ascent
        os2.usWinDescent = abs(descent)
        os2.sTypoAscender = ascent
        os2.sTypoDescender = descent
        os2.sTypoLineGap = linegap
        os2.fsSelection = 0b10000000
        os2.xAvgCharWidth = 500
        os2.usWeightClass = 400
        os2.usWidthClass = 5
        os2.fsType = 0
        os2.usFirstCharIndex = 0x0020  # Space
        os2.usLastCharIndex = 0xFFFF
        os2.sCapHeight = 700
        os2.sxHeight = 500
        os2.usBreakChar = 32
        os2.usMaxContext = 0
        os2.usDefaultChar = 0
        os2.ySubscriptXSize = 0
        os2.ySubscriptYSize = 0
        os2.ySubscriptXOffset = 0
        os2.ySubscriptYOffset = 0
        os2.ySuperscriptXSize = 0
        os2.ySuperscriptYSize = 0
        os2.ySuperscriptXOffset = 0
        os2.ySuperscriptYOffset = 0
        os2.yStrikeoutSize = 0
        os2.yStrikeoutPosition = 0
        os2.sFamilyClass = 0
        os2.panose = Panose()
        os2.panose.bFamilyType = 0
        os2.panose.bSerifStyle = 0
        os2.panose.bWeight = 0
        os2.panose.bProportion = 0
        os2.panose.bContrast = 0
        os2.panose.bStrokeVariation = 0
        os2.panose.bArmStyle = 0
        os2.panose.bLetterForm = 0
        os2.panose.bMidline = 0
        os2.panose.bXHeight = 0
        os2.ulUnicodeRange1 = 0
        os2.ulUnicodeRange2 = 0
        os2.ulUnicodeRange3 = 0
        os2.ulUnicodeRange4 = 0
        os2.ulCodePageRange1 = 0
        os2.ulCodePageRange2 = 0

        # --- hhea: 縦方向のメトリクス ---
        font['hhea'] = newTable('hhea')
        hhea = font['hhea']
        hhea.tableVersion = 0x00010000  # 1.0の固定小数点形式
        hhea.ascent = ascent
        hhea.descent = descent
        hhea.lineGap = linegap
        hhea.advanceWidthMax = upm
        hhea.minLeftSideBearing = 0
        hhea.minRightSideBearing = 0
        hhea.xMaxExtent = ascent
        hhea.caretSlopeRise = 1
        hhea.caretSlopeRun = 0
        hhea.caretOffset = 0
        hhea.reserved0 = 0
        hhea.reserved1 = 0
        hhea.reserved2 = 0
        hhea.reserved3 = 0
        hhea.metricDataFormat = 0
        hhea.numberOfHMetrics = 1  # .notdef分

        # --- name テーブルを追加 ---
        font['name'] = newTable('name')
        name = font['name']
        nr = NameRecord()
        nr.nameID = 1  # Family Name
        nr.platformID = 3
        nr.platEncID = 1
        nr.langID = 0x409
        nr.string = "TestFont".encode("utf-16-be")
        name.names = [nr]

        # --- glyf テーブルを追加(CFF/CFF2でも必要) ---
        font['glyf'] = newTable('glyf')
        glyf = font['glyf']
        notdef_glyph = Glyph()
        notdef_glyph.numberOfContours = 0
        notdef_glyph.data = b""
        glyf.glyphs = {".notdef": notdef_glyph}

        # --- cmap テーブルを追加 ---
        font['cmap'] = newTable('cmap')
        cmap = font['cmap']
        cmap.tableVersion = 0
        subtable = cmap_format_4(4)
        subtable.platformID = 3
        subtable.platEncID = 1
        subtable.language = 0
        subtable.cmap = mapping if mapping is not None else {}
        cmap.tables = [subtable]

        return font

    return _create
