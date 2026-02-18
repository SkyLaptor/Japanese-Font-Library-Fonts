from pathlib import Path

from utils.subsetter.merge_text import action_merge_text, merge_text


def test_action_merge_text_output(tmp_path):
    """
    文字列結合アクションが正常に走り、ファイルが書き出されるかのテスト
    """
    # 1. 準備: 入力元、出力先
    input_dir = Path("tests/data/test-text")
    output_file = tmp_path / "test.txt"

    # 2. 実行: アクションを直接叩く
    action_merge_text(
        input_dir=input_dir,
        output_path=str(output_file),
        validnamechars_escape=True,
        debug=True,
    )

    # 3. 検証: ファイルが物理的に存在し、中身が空でないか
    assert output_file.exists(), "ファイルが生成されていません"

    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 0, "生成されたファイルが空です"

    # デバッグ用に最初の数文字を表示（pytest -s で確認可能）
    print(f"\nGenerated content preview: {content[:20]}...")


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
