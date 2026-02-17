from pathlib import Path


def long_path(path: Path, debug: bool = False) -> str:
    """
    Windowsの260文字制限を回避するためのロングパスプレフィックスを付与

    :param path: テキストファイルパス
    :type path: Path
    :param debug: デバッグモード
    :type debug: bool
    :return: ロングパスプレフィックスを付与したパス
    :rtype: str
    """
    abs_path = str(path.resolve())

    # 既にプレフィックスがついている場合はそのまま
    if abs_path.startswith("\\\\?\\"):
        return abs_path

    # ネットワークパス(UNC)の場合の処理
    if abs_path.startswith("\\\\"):
        return f"\\\\?\\UNC\\{abs_path[2:]}"

    # 通常のローカルパス
    return f"\\\\?\\{abs_path}"
