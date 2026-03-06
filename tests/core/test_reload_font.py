from core.font_loader import reopen_font


def test_reload_font_is_different_object(create_mock_font):
    """再読み込み後、オブジェクトが別物になっているか"""
    # create_mock_fontフィクスチャからパスをもらって読み込み
    original_font = create_mock_font()

    reloaded_font = reopen_font(original_font)

    # Pythonの id() が異なる = メモリ上の別オブジェクトであること
    print(reloaded_font)
    print(original_font)
    assert reloaded_font is not original_font

    # 閉じ忘れないように
    original_font.close()
    reloaded_font.close()


def test_reload_font_preserves_data(create_mock_font):
    """再読み込みしても中身（テーブルなど）が維持されているか"""
    original_font = create_mock_font()
    original_tables = set(original_font.keys())

    reloaded_font = reopen_font(original_font)
    reloaded_tables = set(reloaded_font.keys())

    # 存在するテーブルの種類が一致しているか
    assert original_tables == reloaded_tables

    original_font.close()
    reloaded_font.close()
