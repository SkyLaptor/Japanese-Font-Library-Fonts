#!/usr/bin/env fontforge

# EMサイズ
#  デフォルトメトリクスの合計値と同じであること。
EMSIZE = 1024

# デフォルトメトリクス
#  合計値がEMサイズと同じであること。
#  尚且つ 日本語フォントSWFのメトリクス値と同じであること。
#  参考: Ascent:17600twips, Descent:2880twips 1px=1em=20twips
DEFAULT_METRICS = (880, 144)

# 空白で正しいグリフの名前
PROTECTED_BLANKGLYPHS = [
        "space", "uni3000", "ideographicspace", ".notdef", 
        "NULL", "nonmarkingreturn", "nbspace", "uni00A0",
        "emspace", "enspace", "thinspace", "hairspace",
        "uni2003", "uni2002", "uni2009", "uni200A",
        "zerowidthspace", "uni200B"
    ]

# 最適化レベル 0.1~1.0
#  あまり大きくするとグリフが破綻する場合あり
SIMPLIFY = 0.5

# デフォルトサブセットファイルパス
DEFAULT_SUBSET = "subset_jp_skyrim.txt"

# 最適化フォントのフォント情報
FONT_VERSION = 1.000
FONT_ID = 1
FONT_COPYRIGHT = ""
FONT_VENDOR = "    "

# フォントに含まれるグリフの縦横サイズを算出するための対象範囲
ANALYZE_RANGE = (0x4E00, 0x9FFF + 1)

# スカイリムフォント向け最適化モード
MODE_EVERY = "every"
MODE_BOOK = "book"
MODE_HANDWRITE = "handwrite"

# スカイリムの標準フォント
SKYRIM_EVERY_FONT = "skyrim_jp_every.ttf"
SKYRIM_BOOK_FONT = "skyrim_jp_book.ttf"
SKYRIM_HANDWRITE_FONT = "skyrim_jp_handwrite.ttf"
