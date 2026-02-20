# 出力テキストファイルのエンコード
from pathlib import Path

ENCODE = "utf-8"
# 各種ディレクトリ
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
BUILD_DIR = BASE_DIR / "build"
SUBSETS_DIR = DATA_DIR / "subsets"
# === キー名は不整合が起きないように注意 ===
# Skyrim用ベースキー名
SKYRIM_BASE_KEYNAME = ["every", "book", "handwrite"]
# Skyrim用ベースフォントマップ
SKYRIM_BASE_FONT_DIR = DATA_DIR / "base_fonts" / "skyrim"
SKYRIM_BASE_FONT_CONFIGS = {
    "every": SKYRIM_BASE_FONT_DIR / "every.ttf",
    "book": SKYRIM_BASE_FONT_DIR / "book.ttf",
    "handwrite": SKYRIM_BASE_FONT_DIR / "handwrite.ttf",
}
# Skyrim用のベースフォント毎の長体バリエーション
SKYRIM_MODE_VARIANTS = {
    "every": ["normal", "condensed", "skinny"],
    "book": ["normal"],
    "handwrite": ["normal"],
}
# Skyrim用サブセットバリエーション
SKYRIM_SUBSET_DIR = DATA_DIR / "subsets" / "skyrim"
SKYRIM_SUBSET_CONFIGS = {
    "full": "subset_jp_full.txt",
    "lightweight": "subset_jp_lightweight.txt",
}
SKYRIM_EXPORT_MATRIX = [
    {
        "base": base,
        "condense": condense,
        "label": label,
        "path": SKYRIM_SUBSET_DIR / filename,
    }
    for base, condenses in SKYRIM_MODE_VARIANTS.items()
    for condense in condenses
    for label, filename in SKYRIM_SUBSET_CONFIGS.items()
]
# 長体別倍率マップ
CONDENSE_RATIO_CONFIGS = {
    "normal": 1.0,
    "condensed": 0.64,
    "skinny": 0.48,
}
# 追加文字（Unicode直接指定）
EXTRA_UNICODES = [
    0x2026,  # … (三点リーダー)
    0x2014,  # — (エムダッシュ)
    0x32FF,  # ㋿ (令和合字)
]
# 検証を行わない文字(改行コードなど特殊なもの)
EXCLUDE_CHARS = "\r\n\t"
# 空白であることが正しいグリフ
BLANK_GLYPHS = {
    # 未定義文字の代替（絶対に消してはなりません）
    ".notdef",
    # 半角スペース
    "space",
    "uni0020",
    0x0020,
    # 全角スペース
    "ideographicspace",
    "uni3000",
    0x3000,
    # 改行しないスペース
    "nbspace",
    "nonbreakingspace",
    "uni00A0",
    0x00A0,
    # En Space
    "uni2002",
    0x2002,
    # Em Space
    "uni2003",
    0x2003,
    # Figure Space
    "uni2007",
    0x2007,
    # Punctuation Space
    "uni2008",
    0x2008,
    # Thin Space
    "uni2009",
    0x2009,
    # Hair Space
    "uni200A",
    0x200A,
    # CR
    "uni000D",
    0x000D,
    # LF
    "uni000A",
    0x000A,
}
# テンプレートSWFパス
TEMPLATE_FONTSWF_PATH = DATA_DIR / "font_swfs" / "fonts_template.swf"
# テンプレートSWF内のリプレース文字列
DUMMY_FONT_NAME_IN_SWF = "REPLACE_ME_FONT_NAME_LENGTH_MAX_XXXXXXXXXXXXXXX"
# フォントSWFのファイル名の頭に付ける文字列（慣例的につけてるだけ）
FONTFILE_NAME_PREFIX = "fonts_"
# SWF名判定ルール
SWF_NAME_RULES = {
    "weight": [
        (["bold"], "_bold"),
        (["light"], "_light"),
        (["heavy", "extrabold"], "_heavy"),
    ],
    "ui": [
        (["everywhere", "every"], "_every"),
        (["book"], "_book"),
        (["handwritten", "handwrite", "hand"], "_handwrite"),
    ],
    "condense": [
        (["condensed", "condense", "cond"], "_condensed"),
        (["skinny", "skin"], "_skinny"),
    ],
    "subset": [
        (["skyrim", "lightweight"], "_lightweight"),
    ],
}
# グリフの位置を調整する際の基準値
BASE_LINE_TARGET = 0
