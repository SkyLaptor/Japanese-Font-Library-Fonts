import pytest

from utils.common.load_text import load_text


def test_load_text_basic(tmp_path):
    """基本：読み込み、重複排除、ソートが正しく行われるか"""
    # 「あいうえお」をバラバラかつ重複させて保存
    p = tmp_path / "test.txt"
    p.write_text("うえおあいうえお", encoding="utf-8")

    # 除外なし
    result = load_text(str(p), exclude_chars="")
    assert result == "あいうえお"


def test_load_text_exclude(tmp_path):
    """除外：指定した文字が消えているか"""
    p = tmp_path / "test.txt"
    p.write_text("ABCDEFG", encoding="utf-8")

    # BとDとFを除外
    result = load_text(str(p), exclude_chars="BDF")
    assert result == "ACEG"


def test_load_text_exclude_newline(tmp_path):
    """改行や空白の扱い：これらも一文字として扱われる"""
    p = tmp_path / "test.txt"
    p.write_text("A\nB\nC", encoding="utf-8")

    # 改行を除外文字に入れれば、純粋な文字だけ残る
    result = load_text(str(p), exclude_chars="\n")
    assert result == "ABC"


def test_load_text_not_found():
    """例外：ファイルが存在しないときに正しくエラーが出るか"""
    with pytest.raises(FileNotFoundError, match="テキストファイルが見つかりません"):
        load_text("non_existent_file.txt", exclude_chars="")


def test_load_text_backslash_exclude(tmp_path):
    """バックスラッシュの除外テスト"""
    p = tmp_path / "test.txt"
    p.write_text("A\\B\\C", encoding="utf-8")

    # バックスラッシュを除外
    result = load_text(str(p), exclude_chars="\\")
    assert result == "ABC"
