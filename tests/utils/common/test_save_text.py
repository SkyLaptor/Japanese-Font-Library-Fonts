from pathlib import Path

import pytest

from utils.common.save_text import save_text


def test_save_text_explicit_path(tmp_path):
    # 出力パスを直接指定して保存できるか
    content = "Test content"
    output_path = tmp_path / "result.txt"

    returned_path = save_text(content=content, output_path=str(output_path))

    assert Path(returned_path).exists()
    assert Path(returned_path).read_text(encoding="utf-8") == content


def test_save_text_auto_path_from_input(tmp_path, monkeypatch):
    # inputパスから自動的に出力パスが生成されるか
    # BUILD_DIR がプロジェクト内の固定ディレクトリを指している場合、
    # tmp_path を指すように一時的に書き換える（monkeypatch）と安全です
    fake_build_dir = tmp_path / "build"
    monkeypatch.setattr("utils.common.BUILD_DIR", str(fake_build_dir))

    content = "Auto Path Test"
    input_file = "myfont.ttf"

    returned_path = save_text(content=content, input_path=input_file, suffix="_test")

    assert returned_path.name == "myfont_test.txt"
    assert returned_path.exists()
    assert returned_path.read_text(encoding="utf-8") == content


def test_save_text_value_error():
    """引数が足りないときに適切にエラーを出すか"""
    with pytest.raises(ValueError, match="両方を空にすることは出来ません"):
        save_text(content="error", input_path="", output_path="")
