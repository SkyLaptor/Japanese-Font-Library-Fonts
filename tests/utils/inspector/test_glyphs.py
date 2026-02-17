from utils.inspector.get_glyphs import get_glyphs


def test_get_glyphs_null(create_mock_font):
    # テスト用に文字が存在しないTTFを用意
    mock_font = create_mock_font()

    result = get_glyphs(mock_font)

    # 存在しない文字を取得したりしていないか
    assert result == ""


def test_get_glyphs_abc(create_mock_font):
    # テスト用に基本的な文字のみ設定したTTFを用意
    mock_font = create_mock_font({0x0041: "A", 0x0042: "B", 0x0043: "C"})

    result = get_glyphs(mock_font)

    # 存在するはずの文字を取得できているか
    assert result == "ABC"


def test_get_glyphs_aiu(create_mock_font):
    # テスト用に日本語で基本的な文字のみ設定したTTFを用意
    mock_font = create_mock_font({0x3042: "あ", 0x3044: "い", 0x3046: "う"})

    result = get_glyphs(mock_font)

    # 存在するはずの文字を取得できているか
    assert result == "あいう"


def test_get_glyphs_abc_sort(create_mock_font):
    # テスト用に基本的な文字のみ設定したTTFを用意（順番はバラバラ）
    mock_font = create_mock_font({0x0043: "C", 0x0042: "B", 0x0041: "A"})

    result = get_glyphs(mock_font)

    # 順番がソートされているか
    assert result == "ABC"


def test_get_glyphs_aiu_sort(create_mock_font):
    # テスト用に日本語で基本的な文字のみ設定したTTFを用意（順番はバラバラ）
    mock_font = create_mock_font({0x3046: "う", 0x3044: "い", 0x3042: "あ"})

    result = get_glyphs(mock_font)

    # 順番がソートされているか
    assert result == "あいう"
