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
