# 出力テキストファイルのエンコード
ENCODE = "utf-8"
# ビルド物の配置場所(コミット対象外)
BUILD_DIR = "build"
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
