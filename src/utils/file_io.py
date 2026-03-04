import os
from pathlib import Path

from fontTools.ttLib import TTFont

from const import BUILD_DIR, ENCODE


def to_windows_long_path(path: Path, debug: bool = False) -> str:
    """
    Windowsの260文字制限を回避するためのロングパスプレフィックスを付与

    :param path: パス
    :type path: Path
    :param debug: デバッグモード
    :type debug: bool
    :return: ロングパスプレフィックスを付与したパス
    :rtype: str
    """
    abs_path = str(path.resolve())

    if abs_path.startswith("\\\\?\\"):
        return abs_path

    if abs_path.startswith("\\\\"):
        return f"\\\\?\\UNC\\{abs_path[2:]}"

    return f"\\\\?\\{abs_path}"


def load_text(input_path: str, exclude_chars: str, debug: bool = False) -> str:
    """
    指定されたパスからテキストファイルを読み込む

    除外する文字にバックスラッシュを含める場合は2つ並べて入力して下さい。

    :param input_path: テキストファイルパス
    :type input_path: str
    :param exclude_chars: 除外する文字
    :type exclude_chars: str
    :param debug: デバッグモード
    :type debug: bool
    :return: 読み込んだ文字列
    :rtype: str
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"テキストファイルが見つかりません: {input_path}")

    content = path.read_text(encoding=ENCODE)
    unique_chars = set(content) - set(exclude_chars)
    sorted_unique_chars = "".join(sorted(unique_chars))

    return sorted_unique_chars


def save_text(
    content: str,
    input_path: str = "",
    output_path: str = "",
    suffix: str = "",
    ext: str = "",
    debug: bool = False,
) -> str:
    """
    テキストファイルに内容を書き出す

    接尾詞は拡張子の前に付きます。

    :param content: 内容
    :type content: str
    :param input_path: 入力ファイルパス
    :type input_path: str
    :param output_path: 出力ファイルパス
    :type output_path: str
    :param suffix: 接尾詞
    :type suffix: str
    :param debug: デバッグモード
    :type debug: bool
    :return: 出力ファイルパス（絶対パス）
    :rtype: str
    """
    if not input_path and not output_path:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    final_output_path = ""
    if not output_path:
        os.makedirs(BUILD_DIR, exist_ok=True)

        input_p = Path(input_path)
        actual_ext = ext if ext else input_p.suffix
        if not actual_ext:
            actual_ext = ".txt"
        if not actual_ext.startswith("."):
            actual_ext = f".{actual_ext}"

        final_output_path = Path(BUILD_DIR) / f"{input_p.stem}{suffix}{actual_ext}"
    else:
        final_output_path = Path(output_path)

    final_output_path_abs = final_output_path.resolve()
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)
    final_output_path_abs.write_text(content, encoding=ENCODE)

    return str(final_output_path_abs)


def save_font(
    font_obj: TTFont,
    input_path: str = "",
    output_path: str = "",
    suffix: str = "",
    ext: str = "",
    debug: bool = False,
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
    :param debug: デバッグモード
    :type debug: bool
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

        input_p = Path(input_path)
        actual_ext = ext if ext else input_p.suffix
        if not actual_ext:
            actual_ext = ".ttf"
        if not actual_ext.startswith("."):
            actual_ext = f".{actual_ext}"

        final_output_path = Path(BUILD_DIR) / f"{input_p.stem}{suffix}{actual_ext}"
    else:
        final_output_path = Path(output_path)

    final_output_path_abs = final_output_path.resolve()
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)

    font_obj.save(final_output_path_abs)

    return str(final_output_path_abs)
