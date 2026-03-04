from pathlib import Path

from fontTools.ttLib import TTFont

from gui.main_window import MainWindow

OTF_FIXTURE_PATH = Path("tests/data/otf-test/logotypegothic.otf")


def test_load_font_for_processing_converts_otf_to_ttf_and_logs() -> None:
    otf_path = OTF_FIXTURE_PATH
    assert otf_path.exists(), f"OTF fixture not found: {otf_path}"

    window = MainWindow.__new__(MainWindow)
    logs: list[str] = []

    font_obj = window._load_font_for_processing(
        otf_path,
        "入力元",
        log=logs.append,
    )

    try:
        assert font_obj.sfntVersion == "\x00\x01\x00\x00"
        assert "CFF " not in font_obj
        assert "glyf" in font_obj
        assert any("OTFをオンメモリでフォント変換" in message for message in logs)
    finally:
        font_obj.close()


def test_convert_otf_to_temporary_ttf_creates_valid_ttf_file(tmp_path: Path) -> None:
    otf_path = OTF_FIXTURE_PATH
    assert otf_path.exists(), f"OTF fixture not found: {otf_path}"

    window = MainWindow.__new__(MainWindow)
    logs: list[str] = []

    converted_path = window._convert_otf_to_temporary_ttf(
        otf_path,
        tmp_path,
        index=1,
        label="埋め込みフォント[1]",
        log=logs.append,
    )

    assert converted_path.exists()
    assert converted_path.suffix.lower() == ".ttf"
    assert any("変換済みフォントを一時生成" in message for message in logs)

    with TTFont(str(converted_path)) as converted_font_obj:
        assert converted_font_obj.sfntVersion == "\x00\x01\x00\x00"
        assert "CFF " not in converted_font_obj
