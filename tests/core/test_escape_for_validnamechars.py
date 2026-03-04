from core.text_processor import escape_for_validnamechars


def test_escape_basic():
    """ダブルクォートが正しくエスケープされるか"""
    input_str = 'Name with "quote"'
    expected = r'Name with \"quote\"'
    assert escape_for_validnamechars(input_str) == expected


def test_escape_no_quotes():
    """クォートがない場合はそのままか"""
    input_str = 'SimpleName'
    assert escape_for_validnamechars(input_str) == 'SimpleName'


def test_escape_multiple_quotes():
    """複数のクォートがあっても全てエスケープされるか"""
    input_str = '"Start" and "End"'
    expected = r'\"Start\" and \"End\"'
    assert escape_for_validnamechars(input_str) == expected


def test_escape_empty():
    """空文字でエラーにならないか"""
    assert escape_for_validnamechars("") == ""
