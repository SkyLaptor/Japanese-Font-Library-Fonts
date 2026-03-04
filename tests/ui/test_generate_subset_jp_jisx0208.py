from ui.cui.generate_subset_jp_jisx0208 import action_generate_subset_jp_jisx0208


def test_action_generate_subset_jp_jisx0208_output(tmp_path):
    """
    サブセット生成アクションが正常に走り、ファイルが書き出されるかのテスト
    """
    # 1. 準備: 出力先のパスを決める
    output_file = tmp_path / "test_subset.txt"

    # 2. 実行: アクションを直接叩く
    # 引数は実際の関数に合わせて調整してください
    action_generate_subset_jp_jisx0208(
        output_path=str(output_file), validnamechars_escape=True, debug=True
    )

    # 3. 検証: ファイルが物理的に存在し、中身が空でないか
    assert output_file.exists(), "ファイルが生成されていません"

    content = output_file.read_text(encoding="utf-8")
    assert len(content) > 0, "生成されたファイルが空です"

    # デバッグ用に最初の数文字を表示（pytest -s で確認可能）
    print(f"\nGenerated content preview: {content[:20]}...")


# def test_generate_subset_jp_jisx0208():
#     result = generate_subset_jp_jisx0208()

#     # 1. 最低限含まれているべき文字
#     assert "A" in result  # ASCII
#     assert "あ" in result  # 第1水準
#     assert "熙" in result  # 第2水準

#     # 2. 文字数が明らかに異常でないか (JIS第1-2水準なら5000文字前後はあるはず)
#     assert len(result) > 5000

#     # 3. ソートされているか
#     assert result == "".join(sorted(result))
