from pathlib import Path

import pytest

from modules.inspect_swf_tags import inspect_swf_tags


def test_inspect_swf_tags_template():
    swf_path = Path("data/template.swf")
    result = inspect_swf_tags(swf_path)

    assert result.signature == "FWS"
    assert result.swf_version == 10
    assert result.has_definefont3
    assert not result.has_definefont4


def test_inspect_swf_tags_core():
    swf_path = Path("data/template.swf")
    result = inspect_swf_tags(swf_path)

    assert result.signature == "FWS"
    assert result.has_definefont3
    assert not result.has_definefont4
    assert result.tag_counts.get(75, 0) >= 1


def test_inspect_swf_tags_not_found():
    with pytest.raises(FileNotFoundError):
        inspect_swf_tags(Path("data/font_swfs/not_found.swf"))
