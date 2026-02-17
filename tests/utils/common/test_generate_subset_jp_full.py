# def test_generate_subset_jp_full_samples():
#     result = generate_subset_jp_full()

#     # 1. 最低限含まれているべき文字
#     assert "A" in result  # ASCII
#     assert "あ" in result  # 第1水準
#     assert "熙" in result  # 第2水準
#     assert "①" in result  # 囲み英数字 (EXTRA)

#     # 2. 文字数が明らかに異常でないか (JIS第1-4水準+αなら1万文字前後はあるはず)
#     assert len(result) > 10000

#     # 3. ソートされているか
#     assert result == "".join(sorted(result))
