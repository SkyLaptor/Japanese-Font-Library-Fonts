import os
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


def reload_font(font_obj: TTFont) -> TTFont:
    """
    # フォントの再読み込みを行う

    フォントオブジェクトのまま加工を続けていくとフォントが破損する場合があります。
    そこで、一度メモリ上に書き出してすぐに読み直しさせることで回避します。
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


def is_cff2(font_obj: TTFont) -> bool:
    """
    テーブルを確認して本当にOTF(CFF2)なのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "CFF " in font_obj:
        return True
    return False


def is_cff(font_obj: TTFont) -> bool:
    """
    テーブルを確認して本当にOTF(CFF)なのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "CFF " in font_obj:
        return True
    return False


def is_ttf(font_obj: TTFont) -> bool:
    """
    テーブルを確認して本当にTTFなのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "glyf" in font_obj:
        return True
    return False


def load_text(text_path: str) -> str:
    """
    # 指定されたパスからテキストファイルを読み込み1行の文字列として返す

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


def convert_timestamp(timestamp: int) -> str:
    """
    タイムスタンプ秒数を文字列表記に直す

    :param timestamp:
    """
    return (datetime(1904, 1, 1) + timedelta(seconds=timestamp)).strftime(
        "%Y/%m/%d %H:%M:%S (UTC)"
    )


def save_text(text: str, input: str = "", output: str = "", suffix: str = ""):
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}.txt"
    else:
        output = Path(output)
    output.write_text(text, encoding=ENCODE)
    print(f"テキストファイルを保存しました。: {output}")


def save_font(
    font_obj: TTFont,
    input: str = "",
    output: str = "",
    suffix: str = "",
    otf2ttf: bool = True,
) -> str:
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        ext = Path(input).suffix
        if is_cff(font_obj) and otf2ttf:
            ext = ".ttf"
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}{ext}"
    else:
        output = Path(output)
    # 特に指定が無い場合はOTFであればTTFに変換する。
    if is_cff(font_obj) and otf2ttf:
        # 破壊的変更のため、font_objectには代入しないこと。
        print("OTFからTTFへの変換を行います。")
        print(
            "注: 出力ファイルパスで.otfを指定したとしても中身はTTFとなります。変換したくない場合は --no_otf2ttf フラグを有効にして下さい。"
        )
        otf_to_ttf(font_obj)
    font_obj.save(output)
    # print(f"フォントファイルを保存しました。: {output}")
    return output


def merge_text_files(input_dir: str, output_file: str):
    """
    指定したディレクトリ内の全.txtファイルを読み込み、
    重複を除去して1つのファイルに保存する。
    """
    input_path = Path(input_dir)
    all_chars = set()

    # ディレクトリ内の全ての .txt ファイルを対象にする
    txt_files = list(input_path.glob("*.txt"))

    if not txt_files:
        print(f"警告: {input_dir} 内に .txt ファイルが見つかりませんでした。")
        return

    print(f"{len(txt_files)} 個のファイルを読み込み中...")

    for file_path in txt_files:
        try:
            # UTF-8で読み込み、改行や空白も一旦含めてセットに放り込む
            content = file_path.read_text(encoding="utf-8")
            all_chars.update(content)
        except Exception as e:
            print(f"エラー: {file_path.name} の読み込みに失敗しました: {e}")

    # 改行文字やスペースなどは除外したい場合が多いのでフィルタリング
    # 必要に応じて '\n', '\r', ' ' などを残すか決めてください
    ignored_chars = {'\n', '\r', '\t'}
    unique_chars = [c for c in all_chars if c not in ignored_chars]

    # 文字コード順に並び替えておくと、後で差分が見やすくなります
    unique_chars.sort()

    # 結果を保存
    output_path = Path(output_file)
    output_path.write_text("".join(unique_chars), encoding="utf-8")

    print(f"完了！: {output_path} (総文字数: {len(unique_chars)}文字)")


def generate_subset_jp_full() -> str:
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

    return "".join(target_chars)


def generate_jisx0208(output: str):
    """
    # JIS X 0208(非漢字+第1・第2水準漢字)を抽出し、指定したファイルに保存する。
    """
    all_chars = []

    # 1. 一般的な半角英数記号 (ASCII: 0x21 - 0x7E) を追加
    for i in range(0x21, 0x7F):
        all_chars.append(chr(i))

    # 半角スペースも一応追加
    all_chars.append(" ")

    # 2. JIS X 0208 (全角・漢字) を追加
    for ku in range(1, 85):
        if 9 <= ku <= 15:
            continue
        for ten in range(1, 95):
            if ku == 47 and ten > 51:
                continue
            if ku == 84 and ten > 6:
                continue
            try:
                b1 = ku + 0xA0
                b2 = ten + 0xA0
                char = bytes([b1, b2]).decode("euc-jp")
                if char.isprintable():
                    all_chars.append(char)
            except UnicodeDecodeError:
                continue

    # 書き出し
    from pathlib import Path

    Path(output).write_text("".join(all_chars), encoding="utf-8")
    print(f"Done: {output} (ASCII + JIS X 0208)")
