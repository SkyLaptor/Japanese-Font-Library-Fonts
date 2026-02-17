import os
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont

from const import BUILD_DIR
from utils.common.dprint import dprint
from utils.common.save_text import save_text

# 基準となるメトリクス
ASCENT = 880
DESCENT = -144
UPM = ASCENT + abs(DESCENT)
# アウトラインフォーマット
FORMAT_TTF = 'glyh'
FORMAT_CFF = 'CFF '  # 空白は抜いてはなりません。
FORMAT_CFF2 = 'CFF2'
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

BASE_UNDER = 0


def save_font(
    font_obj: TTFont,
    input_path: str = "",
    output_path: str = "",
    suffix: str = "",
    ext: str = ".ttf",
) -> str:
    """
    フォントファイルに内容を書き出す

    :param font_obj: フォント
    :type font_obj: TTFont
    :param input: 入力ファイルパス
    :type input: str
    :param output: 出力ファイルパス
    :type output: str
    :param suffix: 接尾詞
    :type suffix: str
    :return: 出力ファイルパス
    :rtype: str
    """

    if not input_path and not output_path:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )

    final_output_path = ""
    if not output_path:
        os.makedirs(BUILD_DIR, exist_ok=True)
        # もし input_path が ".otf" なら、デフォルトでも ".otf" を維持するようにする
        # input_path の拡張子をそのまま使う（または引数 ext を尊重する）
        actual_ext = ext if ext else Path(input_path).suffix
        final_output_path = (
            Path(BUILD_DIR) / f"{Path(input_path).stem}{suffix}{actual_ext}"
        )
    else:
        final_output_path = Path(output_path)

    final_output_path_abs = final_output_path.resolve()
    # 途中のディレクトリが存在しなければ作成
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)

    font_obj.save(final_output_path_abs)

    return final_output_path_abs


def reload_font(font_obj: TTFont) -> TTFont:
    """
    フォントの再読み込みを行う

    フォントオブジェクトのまま加工を続けていくとフォントが破損する場合があります。
    そこで、一度メモリ上に書き出して読み直しさせることで回避します。
    再読み込みしたデータは全く別物扱いのため、必ず戻り値で受け取る必要があります。

    :param font_obj: 再読み込みさせるフォントオブジェクト
    :type font_obj: TTFont
    :return: 再読み込みを行ったフォントオブジェクト
    :rtype: TTFont
    """
    buffer = BytesIO()
    font_obj.save(buffer)
    buffer.seek(0)
    font_obj = TTFont(buffer)
    return font_obj


def action_generate_subset_jp_full(output_text_file: str, debug: bool = False, **_):
    subset = generate_subset_jp_full(debug=debug)
    dprint(subset, debug)
    if output_text_file == "" or not output_text_file:
        output_text_file = f"{BUILD_DIR}/subset_jp_full.txt"
    output_text_file = save_text(content=subset, output_path=output_text_file)
    print(f"生成したサブセットを出力しました。: {output_text_file}")


def generate_subset_jp_full(debug: bool = False) -> str:
    """
    日本語圏向けフルサブセットテキストを生成する

    :return: 日本語圏向けフルサブセットテキスト
    :rtype: str
    """
    # 重複を防ぐため set を使用
    target_chars = set()

    # --- ASCII (0x20 - 0x7E) ---
    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    # --- JIS X 0213 (第1, 2, 3, 4水準) を網羅的に収集 ---
    # 面1 (1面): 第1, 2, 3水準の一部
    # 面2 (2面): 第4水準
    for plane in [1, 2]:
        for ku in range(1, 95):
            for ten in range(1, 95):
                try:
                    # EUC-JIS-2004 のバイト順序に変換
                    # 1面は 0xA1-0xFE, 2面は 0x8F + 0xA1-0xFE
                    if plane == 1:
                        b_data = bytes([ku + 0xA0, ten + 0xA0])
                    else:
                        b_data = bytes([0x8F, ku + 0xA0, ten + 0xA0])

                    char = b_data.decode("euc_jis_2004")

                    if char.isprintable():
                        target_chars.add(char)
                except UnicodeDecodeError:
                    continue

    # --- 追加文字（Unicode直接指定） ---
    extra_unicodes = [
        0x2026,  # … (三点リーダー)
        0x2014,  # — (エムダッシュ)
        0x32FF,  # ㋿ (令和合字)
        0xFF01,
        0xFF03,
        0xFF04,
        0xFF05,
        0xFF06,  # などの全角記号 (念のため)
    ]
    # NEC/IBM拡張文字などの範囲 (CP932でよく使われる範囲)
    # 0x2460 - 0x24FF (囲み英数字)
    for i in range(0x2460, 0x2500):
        extra_unicodes.append(i)

    for code in extra_unicodes:
        target_chars.add(chr(code))

    # 生成された文字列をソートして返す
    result = "".join(sorted(target_chars))

    if debug:
        print(f"Total characters: {len(result)}")

    return result


def action_generate_subset_jp_jisx0208(output_text_file: str, debug: bool = False, **_):
    subset = generate_subset_jp_jisx0208(debug=debug)
    subset = escape_for_fontconfig(subset)
    dprint(subset, debug)
    if output_text_file == "" or not output_text_file:
        output_text_file = f"{BUILD_DIR}/subset_jp_jisx0208.txt"
    output_text_file = save_text(content=subset, output_path=output_text_file)
    print(f"生成したサブセットを出力しました。: {output_text_file}")


def escape_for_fontconfig(text: str) -> str:
    """
    全文字の前にバックスラッシュを付与する
    (fontconfigのvalidNameChars形式用)
    """
    return text.replace('"', '\\"')


def generate_subset_jp_jisx0208(debug: bool = False) -> str:
    """
    JIS第二基準(JISX0208)サブセットテキストを生成する

    fontconfigのvalidNameCharsで使用する想定。
    なお、validNameCharsは生成後に'\'でエスケープするのを忘れずに。

    :return: JIS第二基準(JISX0208)サブセットテキスト
    :rtype: str
    """
    target_chars = set()

    # --- ASCII (0x20 - 0x7E) ---
    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    # --- JIS X 0208 (第1水準, 第2水準, 非漢字) ---
    # EUC-JPの漢字範囲（0xA1-0xFE）を利用すると、
    # 拡張文字を含まない純粋なJIS X 0208だけを抽出できます。
    for ku in range(1, 95):
        for ten in range(1, 95):
            try:
                # EUC-JPの区点番号へのマッピング
                # 第1・第2水準は 0xA1〜0xFE の範囲に収まります
                b_data = bytes([ku + 0xA0, ten + 0xA0])

                # 'euc_jp' は純粋な JIS X 0208 範囲（+補助漢字など）を扱います
                char = b_data.decode("euc_jp", errors="strict")

                if char.isprintable():
                    target_chars.add(char)
            except UnicodeDecodeError:
                continue

    # --- 追加文字（Unicode直接指定） ---
    extra_unicodes = [
        # 0x2026,  # … (三点リーダー)
    ]
    for code in extra_unicodes:
        target_chars.add(chr(code))

    # 生成された文字列をソートして返す
    result = "".join(sorted(target_chars))

    if debug:
        print(f"Total characters: {len(result)}")

    return result
