from pathlib import Path

# 出力テキストファイルのエンコード
ENCODE = "utf-8"
# メインウィンドウタイトル
MAIN_WINDOW_TITLE = "TESVFontForge"
# プレビューウィンドウタイトル
PREVIEW_WINDOW_TITLE = "プレビュー"
# 各種ディレクトリ
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
BUILD_DIR = BASE_DIR / "build"
SUBSETS_DIR = DATA_DIR / "subsets"
LANG_DIR = DATA_DIR / "lang"

# デフォルト言語設定
DEFAULT_LANG_CODE = "ja-jp"
DEFAULT_LANG_FILE = LANG_DIR / f"{DEFAULT_LANG_CODE}.yml"
# アプリケーションアイコン
APP_ICON_PATH = ASSETS_DIR / "images" / "icon.png"
# FFDecとJavaの自動ダウンロード用URL
FFDEC_ARCHIVE_URL = "https://github.com/jindrapetrik/jpexs-decompiler/releases/download/version25.1.3/ffdec_25.1.3.zip"
JAVA_ARCHIVE_URL = "https://corretto.aws/downloads/resources/25.0.2.10.1/amazon-corretto-25.0.2.10.1-windows-x64-jdk.zip"
FONTFORGE_ARCHIVE_URL = "https://portableapps.com/downloading/?a=FontForgePortable&s=s&p=&d=pa&n=FontForge%20Portable&f=FontForgePortable_2025-10-09.paf.exe"
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
TEMPLATE_FONTSWF_PATH = DATA_DIR / "template.swf"
# グリフの位置を調整する際の基準値
BASE_LINE_TARGET = 0
# フォント処理で基準とするUPM
NORMALIZED_UPM = 1024

# プレビュー描画設定
# サンプル文字列を描画するフォントサイズ（px）
PREVIEW_FONT_SIZE = 120
# プレビュー画像の四辺余白（px）
PREVIEW_PADDING = 28
# プレビュー画像の最小サイズ（px）
PREVIEW_MIN_WIDTH = 520
PREVIEW_MIN_HEIGHT = 180

# Baseline補助線の色（RGBA）
PREVIEW_BASELINE_COLOR = (80, 170, 255, 220)
# Ascender/Descender/LineGap補助線の色（RGBA）
PREVIEW_METRIC_COLOR = (255, 220, 120, 200)
# Underline補助線の色（RGBA）
PREVIEW_UNDERLINE_COLOR = (255, 120, 120, 220)

# Baseline補助線の太さ（px）
PREVIEW_BASELINE_WIDTH = 1
# Ascender/Descender/LineGap補助線の太さ（px）
PREVIEW_METRIC_WIDTH = 1
# 破線の1セグメント長（px）
PREVIEW_DASH_LENGTH = 8
# 破線のセグメント間隔（px）
PREVIEW_DASH_GAP = 6

# 凡例描画設定
# 凡例ボックスの背景色（RGBA）
PREVIEW_LEGEND_BACKGROUND_COLOR = (0, 0, 0, 170)
# 凡例テキストの色（RGBA）
PREVIEW_LEGEND_TEXT_COLOR = (255, 255, 255, 230)
# 凡例のX座標（左端からのオフセット、px）
PREVIEW_LEGEND_MARGIN_X = 8
# 凡例の下端余白（下端からのオフセット、px）
PREVIEW_LEGEND_MARGIN_Y = 4
# 凡例ボックス内部余白（px）
PREVIEW_LEGEND_PADDING = 6
# 凡例の行間（px）
PREVIEW_LEGEND_ROW_GAP = 4
# 凡例表示領域として画像下部に確保する高さ（px）
PREVIEW_LEGEND_RESERVED_HEIGHT = 56

# 凡例用フォント候補（上から優先）
PREVIEW_LEGEND_FONT_CANDIDATES = (
    ASSETS_DIR / "fonts" / "system.otf",
    Path("C:/Windows/Fonts/msgothic.ttc"),
    Path("C:/Windows/Fonts/meiryo.ttc"),
)
# 凡例フォントサイズ
PREVIEW_LEGEND_FONT_SIZE = 12
