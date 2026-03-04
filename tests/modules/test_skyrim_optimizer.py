from pathlib import Path

from fontTools.ttLib import TTFont

from modules.skyrim_optimizer import rewrite_font_with_fonttools


def test_rewrite_font_with_fonttools_creates_backup_and_keeps_font_readable(tmp_path):
    src_font = Path("tests/data/test-font/test-font-medium.ttf")
    target_font = tmp_path / "test-font-medium.ttf"
    target_font.write_bytes(src_font.read_bytes())

    result = rewrite_font_with_fonttools(target_font)

    assert result is True
    assert target_font.exists()
    assert target_font.with_name(f"{target_font.name}.bak").exists()

    with TTFont(str(target_font)) as rewritten_font:
        assert len(rewritten_font.getGlyphOrder()) > 0


def test_rewrite_font_with_fonttools_returns_false_when_missing_file(tmp_path):
    missing = tmp_path / "not_found.ttf"
    result = rewrite_font_with_fonttools(missing)
    assert result is False
