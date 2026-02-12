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
    ".notdef",  # 未定義文字の代替（必須）
    "space",  # 半角スペース
    "uni0020",  # 半角スペース(Unicode)
    "ideographicspace",  # 全角スペース
    "uni3000",  # 全角スペース(Unicode)
    "nbspace",  # 改行しないスペース
    "nonbreakingspace",  # 改行しないスペース(別名)
    "uni00A0",  # 改行しないスペース(Unicode)
    "uni2002",  # En Space
    "uni2003",  # Em Space
    "uni2007",  # Figure Space
    "uni2008",  # Punctuation Space
    "uni2009",  # Thin Space
    "uni200A",  # Hair Space
    "uni000D",  # CR
    "uni000A",  # LF
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


def is_otf(font_obj: TTFont) -> bool:
    """
    # ヘッダーを確認して、本当にOTFなのか確認する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :return: 検査結果
    :rtype: bool
    """
    if "CFF " in font_obj or "CFF2" in font_obj:
        return True
    return False


def is_ttf(font_obj: TTFont) -> bool:
    """
    # ヘッダーを確認して、本当にTTFなのか確認する

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
):
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        ext = Path(input).suffix
        if is_otf(font_obj) and otf2ttf:
            ext = ".ttf"
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}{ext}"
    else:
        output = Path(output)
    # 特に指定が無い場合はOTFであればTTFに変換する。
    if is_otf(font_obj) and otf2ttf:
        # 破壊的変更のため、font_objectには代入しないこと。
        print("OTFからTTFへの変換を行います。")
        print(
            "注: 出力ファイルパスで.otfを指定したとしても中身はTTFとなります。変換したくない場合は --no_otf2ttf フラグを有効にして下さい。"
        )
        otf_to_ttf(font_obj)
    font_obj.save(output)
    print(f"フォントファイルを保存しました。: {output}")
