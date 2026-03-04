from fontTools.ttLib import newTable

from modules.get_info import get_info


def test_get_info_ttf_format(create_mock_font):
    # テスト用のTTFを用意
    mock_font = create_mock_font()
    # mock_ttf['glyf'] = newTable('glyf') # glyfは必須テーブルのためモック側で設定済

    result = get_info(mock_font)

    # アウトライン判定が正しいかどうか
    assert result.is_ttf


def test_get_info_cff_format(create_mock_font):
    # テスト用のCFFを用意
    mock_font = create_mock_font()
    mock_font['CFF '] = newTable('CFF ')

    result = get_info(mock_font)

    # アウトライン判定が正しいかどうか
    assert result.is_cff


def test_get_info_cff2_format(create_mock_font):
    # テスト用のCFF2を用意
    mock_font = create_mock_font()
    mock_font['CFF2'] = newTable('CFF2')

    result = get_info(mock_font)

    # アウトライン判定が正しいかどうか
    assert result.is_cff2


def test_get_info_weird_timestamp(create_mock_font):
    # 作成日や更新日が0のフォントを用意
    mock_font = create_mock_font()
    mock_font['head'].created = 0  # 1904/01/01
    mock_font['head'].modified = 0

    result = get_info(mock_font)

    # 変換に失敗してエラーにならず、特定の文字列を返すかチェック
    assert "1904" in result.created_time
    assert "1904" in result.modified_time
