import os
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont

import utils.file_io as file_io
from utils.file_io import save_font


def test_save_font_explicit_path(create_mock_font, tmp_path):
    # 出力パスを直接指定して保存できるか
    mock_font = create_mock_font()
    output_path = tmp_path / "mockfont.ttf"

    saved_output_path = save_font(mock_font, output_path=str(output_path))
    saved_mock_font = TTFont(Path(saved_output_path))

    assert Path(saved_output_path).exists()
    assert set(saved_mock_font.keys()) == set(mock_font.keys())


def test_save_font_auto_path_from_input(create_mock_font, tmp_path, monkeypatch):
    # inputパスから自動的に出力パスが生成されるか
    # BUILD_DIR がプロジェクト内の固定ディレクトリを指している場合、
    # tmp_path を指すように一時的に書き換える（monkeypatch）と安全です
    fake_build_dir = tmp_path / "build"
    monkeypatch.setattr(file_io, "BUILD_DIR", fake_build_dir)

    mock_font = create_mock_font()
    input_path = "mockfont.ttf"
    saved_output_path = save_font(mock_font, input_path=input_path, suffix="_test")
    saved_mock_font = TTFont(Path(saved_output_path))

    assert os.path.exists(saved_output_path)
    assert saved_output_path.endswith("mockfont_test.ttf")
    assert set(saved_mock_font.keys()) == set(mock_font.keys())


def test_save_font_value_error(create_mock_font):
    """引数が足りないときに適切にエラーを出すか"""
    mock_font = create_mock_font()
    with pytest.raises(ValueError, match="両方を空にすることは出来ません"):
        save_font(mock_font, input_path="", output_path="")
