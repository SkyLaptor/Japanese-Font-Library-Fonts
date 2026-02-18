import os
from pathlib import Path

from const import BUILD_DIR, ENCODE


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

        # 拡張子の決定
        # 1. 引数 ext があればそれを使う
        # 2. なければ input_path の拡張子を使う
        # 3. それでもなければ ".txt" にする
        input_p = Path(input_path)
        actual_ext = ext if ext else input_p.suffix
        if not actual_ext:
            actual_ext = ".txt"
        # ドットの調整（".txt" でも "txt" でも受け入れるように）
        if not actual_ext.startswith("."):
            actual_ext = f".{actual_ext}"

        final_output_path = Path(BUILD_DIR) / f"{input_p.stem}{suffix}{actual_ext}"
    else:
        final_output_path = Path(output_path)

    final_output_path_abs = final_output_path.resolve()
    # 途中のディレクトリが存在しなければ作成
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)

    final_output_path_abs.write_text(content, encoding=ENCODE)

    return str(final_output_path_abs)
