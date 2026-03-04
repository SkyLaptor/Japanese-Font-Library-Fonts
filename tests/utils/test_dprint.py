from utils.dprint import dprint


def test_dprint_enabled(capsys):
    """debug=True のときに正しく表示されるか"""
    dprint("テストメッセージ", debug=True)

    # capsys.readouterr() で標準出力をキャプチャ
    captured = capsys.readouterr()

    # デフォルトのプレフィックスとメッセージが含まれているか
    assert "テストメッセージ" in captured.out
    assert "[DEBUG]: " in captured.out


def test_dprint_disabled(capsys):
    """debug=False のときに何も表示されないか"""
    dprint("隠密メッセージ", debug=False)

    captured = capsys.readouterr()

    # 何も表示されていないことを確認
    assert captured.out == ""


def test_dprint_custom_prefix(capsys):
    """カスタムプレフィックスが機能するか"""
    dprint("カスタム", debug=True, prefix="[INFO]: ")

    captured = capsys.readouterr()
    assert "[INFO]: カスタム" in captured.out.strip()
