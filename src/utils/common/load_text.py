from pathlib import Path

from const import ENCODE


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

    # 集合を使って一気に重複排除と除外を行う
    unique_chars = set(content) - set(exclude_chars)

    # テキストから重複を除去してソートする。
    sorted_unique_chars = "".join(sorted(unique_chars))

    return sorted_unique_chars
