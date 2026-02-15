import argparse
import os
import sys
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf

# ビルド物の配置場所(コミット対象外)
BUILD_DIR = "build"
# 出力テキストファイルのエンコード
ENCODE = "utf-8"
# 基準となるメトリクス
ASCENT = 880
DESCENT = -144
UPM = ASCENT + abs(DESCENT)
# 各種固定メッセージ
MSG_FONTTYPE_UNIDENT = "フォントの形式が判別出来ません。"
# 空白であることが正しいグリフ
BLANK_GLYPHS = {
    # 未定義文字の代替（絶対に消してはならない）
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


def main():
    parser = argparse.ArgumentParser(
        description="フォントの検査を行うためのツールボックス"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
    )
    parser.add_argument(
        "--input_text_dir",
        type=str,
        help="テキストファイルのディレクトリ",
    )
    parser.add_argument(
        "-o",
        "--output_text_file",
        type=str,
        help="テキストの書き出し先",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ表示の有効化",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    dispatch_action(**vars(args))


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def long_path(path: Path) -> str:
    """
    Windowsの260文字制限を回避するためのロングパスプレフィックスを付与
    """
    abs_path = str(path.resolve())
    if abs_path.startswith("\\\\?\\"):
        return abs_path
    return f"\\\\?\\{abs_path}"


def dprint(message: str, debug: bool = False, prefix: str = "[DEBUG]: "):
    """
    デバッグモードが有効の時だけ表示する

    :param message: メッセージ
    :type message: str
    :param debug: デバッグモード
    :type debug: bool
    :param prefix: 接詞詞
    :type prefix: str
    """
    if debug:
        print(prefix, message)


def is_ttf(font_obj: TTFont) -> bool:
    """
    テーブルを確認してアウトラインフォーマットがTrueTypeなのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "glyf" in font_obj:
        return True
    return False


def is_cff(font_obj: TTFont) -> bool:
    """
    テーブルを確認してアウトラインフォーマットがCFF(PostScript (CFF))なのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "CFF " in font_obj:
        return True
    return False


def is_cff2(font_obj: TTFont) -> bool:
    """
    テーブルを確認してアウトラインフォーマットがCFF2(PostScript (CFF2 / Variable))なのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "CFF " in font_obj:
        return True
    return False


def load_text(text_path: str) -> str:
    """
    指定されたパスからテキストファイルを読み込む

    改行などの制御コードと重複している文字は排除されます。

    :param text_path: テキストファイルパス
    :type text_path: str
    :return: 読み込んだ文字列
    :rtype: str
    """
    path = Path(text_path)
    if not path.exists():
        raise FileNotFoundError(f"テキストファイルが見つかりません: {text_path}")
    content = path.read_text(encoding=ENCODE)

    # 改行やタブなどの制御文字を除去し、重複を排除（setを使用）
    # 基本的には含めておいたほうが安全です。
    char_set = set(content.replace("\n", "").replace("\r", "").replace("\t", ""))

    # ソートして文字列に戻す（デバッグ時に中身を確認しやすくするため）
    return "".join(sorted(char_set))


def action_merge_text(input_text_dir, output_text_file, debug: bool = False):
    unique_sorted_chars = merge_text(input_text_dir=input_text_dir)
    output_text_file = save_text(
        text=unique_sorted_chars, input="", output=output_text_file
    )
    print(f"マージ済みテキストを出力しました。{output_text_file}")


def merge_text(input_text_dir: str | Path) -> str:
    """
    指定ディレクトリ内の全txtファイルを読み込み、重複なし・ソート済みの1ファイルにまとめます。
    """
    input_text_dir = Path(input_text_dir)
    all_text = ""

    # 1. ディレクトリ内の全 .txt ファイルをループ
    for txt_file in input_text_dir.glob("*.txt"):
        print(f"[DEBUG]: 読み込み中... {txt_file.name}")
        all_text += txt_file.read_text(encoding="utf-8")

    # 2. 改行・空白・タブを削除
    # スカイリムのサブセットには不要な制御文字をここで一掃します
    table = str.maketrans("", "", "\n\r\t ")
    clean_text = all_text.translate(table)

    # 3. 重複排除 & ソート
    unique_sorted_chars = "".join(sorted(set(clean_text)))

    return unique_sorted_chars


def save_text(
    text: str, input: str = "", output: str = "", suffix: str = "", ext: str = ".txt"
) -> str:
    """
    テキストファイルに内容を書き出す

    :param text: 内容
    :type text: str
    :param input: 入力ファイルパス
    :type input: str
    :param output: 出力ファイルパス
    :type output: str
    :param suffix: 接尾詞
    :type suffix: str
    :return: 出力ファイルパス
    :rtype: str
    """
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}{ext}"
    else:
        output = Path(output)
    output.write_text(text, encoding=ENCODE)
    return output


def save_font(
    font_obj: TTFont,
    input: str = "",
    output: str = "",
    suffix: str = "",
    otf2ttf: bool = True,
) -> str:
    """
    フォントファイルに内容を書き出す

    与えられた拡張子のアウトラインフォーマットに自動で変換はされません。
    フォントオブジェクトの中身には留意して下さい。

    :param font_obj: フォント
    :type font_obj: TTFont
    :param input: 入力ファイルパス
    :type input: str
    :param output: 出力ファイルパス
    :type output: str
    :param suffix: 接尾詞
    :type suffix: str
    :param otf2ttf: TTF変換を有効
    :type otf2ttf: bool
    :return: 出力ファイルパス
    :rtype: str
    """
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        ext = Path(input).suffix
        if is_cff(font_obj) or is_cff2(font_obj) and otf2ttf:
            ext = ".ttf"
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}{ext}"
    else:
        output = Path(output)
    # 特に指定が無い場合はOTFであればTTFに変換する。
    if is_cff(font_obj) or is_cff2(font_obj) and otf2ttf:
        # 破壊的変更のため、font_objectには代入しないこと。
        print("OTFからTTFへの変換を行います。")
        print(
            "注: 出力ファイルパスで.otfを指定したとしても中身はTTFとなります。変換したくない場合は --no_otf2ttf フラグを有効にして下さい。"
        )
        otf_to_ttf(font_obj)
    font_obj.save(output)
    return output


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


def convert_timestamp(timestamp: int, format: str = "%Y/%m/%d %H:%M:%S (UTC)") -> str:
    """
    タイムスタンプ秒数を任意のフォーマットの文字列表記に変換する

    :param timestamp: UNIXタイムスタンプ
    :type timestamp: int
    :param format: フォーマット
    :type format: str
    :return: フォーマット済みタイムスタンプ
    :rtype: str
    """
    return (datetime(1904, 1, 1) + timedelta(seconds=timestamp)).strftime(format)


def action_generate_subset_jp_full(output_text_file: str, debug: bool = False, **_):
    subset = generate_subset_jp_full(debug=debug)
    dprint(subset, debug)
    if output_text_file == "" or not output_text_file:
        output_text_file = f"{BUILD_DIR}/subset_jp_full.txt"
    output_text_file = save_text(text=subset, output=output_text_file)
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
    output_text_file = save_text(text=subset, output=output_text_file)
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


ACTION_MAP = {
    "generate_subset_jp_full": action_generate_subset_jp_full,
    "generate_subset_jp_jisx0208": action_generate_subset_jp_jisx0208,
    "merge_text": action_merge_text,
}


if __name__ == "__main__":
    main()
