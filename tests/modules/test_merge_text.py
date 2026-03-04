from pathlib import Path

from modules.merge_text import action_merge_text, merge_text


def test_action_merge_text_output(tmp_path):
    input_dir = Path("tests/data/test-text")
    output_file = tmp_path / "test.txt"

    action_merge_text(
        input_dir=input_dir,
        output_path=str(output_file),
        validnamechars_escape=True,
        debug=True,
    )

    assert output_file.exists(), "ファイルが生成されていません"

    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 0, "生成されたファイルが空です"


def test_merge_text_basic(tmp_path):
    file1 = tmp_path / "test1.txt"
    file1.write_text("あいう", encoding="utf-8")

    file2 = tmp_path / "test2.txt"
    file2.write_text("うえお", encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert result == "あいうえお"


def test_merge_text_with_exclude_chars(tmp_path):
    content = "A\nB\rC\tA B"
    file = tmp_path / "exclude.txt"
    file.write_text(content, encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert "\n" not in result
    assert "\r" not in result
    assert "\t" not in result
    assert result == " ABC"


def test_merge_text_no_txt_files(tmp_path):
    (tmp_path / "image.png").write_text("fake", encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert result == ""


def test_merge_text_empty_file(tmp_path):
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert result == ""
