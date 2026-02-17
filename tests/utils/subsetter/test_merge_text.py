from utils.subsetter.merge_text import merge_text


def test_merge_text_basic(tmp_path):
    # 1. テスト用のテキストファイルを作成
    file1 = tmp_path / "test1.txt"
    file1.write_text("あいう", encoding="utf-8")

    file2 = tmp_path / "test2.txt"
    file2.write_text("うえお", encoding="utf-8")

    # 2. 実行
    result = merge_text(str(tmp_path))

    # 3. 検証
    # 「あいう」+「うえお」 -> 重複排除＆ソート -> 「あいうえお」
    assert result == "あいうえお"


def test_merge_text_with_exclude_chars(tmp_path):
    # EXCLUDE_CHARS (\r, \n, \t) や重複が含まれる場合
    content = "A\nB\rC\tA B"  # 改行、タブ、スペース、重複
    file = tmp_path / "exclude.txt"
    file.write_text(content, encoding="utf-8")

    result = merge_text(str(tmp_path))

    # \n \r \t が消えているか（スペースは残す仕様）
    # ソート順: " " -> "A" -> "B" -> "C"
    assert "\n" not in result
    assert "\r" not in result
    assert "\t" not in result
    assert result == " ABC"


def test_merge_text_no_txt_files(tmp_path):
    # .txt ファイルが存在しない場合
    (tmp_path / "image.png").write_text("fake", encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert result == ""


def test_merge_text_empty_file(tmp_path):
    # 空のファイルがある場合
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")

    result = merge_text(str(tmp_path))

    assert result == ""
