from pathlib import Path

from utils.common.long_path import long_path


def test_long_path_local(tmp_path):
    # 通常のパス
    p = tmp_path / "test.txt"
    result = long_path(p)
    assert result.startswith("\\\\?\\")
    assert "test.txt" in result


def test_long_path_already_prefixed():
    # 1. すでにプレフィックスが付いている「文字列」を用意
    prefixed_str = "\\\\?\\C:\\test.txt"

    # 2. それを Path オブジェクトにする
    p = Path(prefixed_str)

    # 3. 関数に p を渡し、結果が元の prefixed_str と一致するか確認
    # (内部で resolve() されても、プレフィックスが維持または再付与されるか)
    result = long_path(p)

    assert result == prefixed_str
