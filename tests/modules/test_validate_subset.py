from pathlib import Path

from modules.validate_subset import action_validate_subset


def test_action_validate_subset_output(tmp_path):
    # 準備: 入力フォントと出力場所を準備
    input_path = Path("tests/data/test-font/test-font-medium.ttf")
    output_path = tmp_path / "test.txt"
    subset_path = Path("data/subsets/subset_jp_full.txt")
    action_validate_subset(
        input_path=input_path,
        output_path=output_path,
        subset_path=subset_path,
        debug=True,
    )

    # 3. 検証: ファイルが物理的に存在し、中身が空でないか
    assert output_path.exists(), "ファイルが生成されていません"

    # フルサブセットと比較しているため、基本的に空はありえない。
    content = output_path.read_text(encoding="utf-8")
    assert len(content) > 0, "生成されたファイルが空です"
