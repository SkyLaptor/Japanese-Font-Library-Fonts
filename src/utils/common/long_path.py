from pathlib import Path


def long_path(path: Path) -> str:
    """
    Windowsの260文字制限を回避するためのロングパスプレフィックスを付与
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
