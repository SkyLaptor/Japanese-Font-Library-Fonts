from pathlib import Path

import pytest

from modules import skyrim_swf_patcher as patcher

SIMPLE_SWF_XML = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<swf>
    <tags>
        <item type=\"DefineFont3Tag\" fontID=\"1\" fontName=\"DUMMY\" />
        <item type=\"ShowFrameTag\" />
    </tags>
</swf>
"""


def _get_font_entries(xml_text: str) -> list[tuple[int, str]]:
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_text)
    items = root.findall("./tags/item")
    return [
        (int(item.attrib["fontID"]), item.attrib.get("fontName", ""))
        for item in items
        if item.attrib.get("type") in patcher.FONT_TAG_TYPES and "fontID" in item.attrib
    ]


def test_replace_glyph_in_swf_uses_ffdec_wrapper(monkeypatch, tmp_path):
    called = {}

    def fake_ffdec_replace(
        input_swf_path, output_swf_path, character_id, input_font_path
    ):
        called["input_swf_path"] = input_swf_path
        called["output_swf_path"] = output_swf_path
        called["character_id"] = character_id
        called["input_font_path"] = input_font_path

    monkeypatch.setattr("modules.skyrim_swf_patcher.ffdec_replace", fake_ffdec_replace)

    template_path = tmp_path / "template.swf"
    output_path = tmp_path / "output.swf"
    font_path = tmp_path / "font.ttf"

    patcher.replace_glyph_in_swf(template_path, output_path, font_path)

    assert called["input_swf_path"] == str(template_path)
    assert called["output_swf_path"] == str(output_path)
    assert called["character_id"] == 1
    assert called["input_font_path"] == str(font_path)


def test_patch_swf_internal_fontname_rewrites_xml_and_cleanup(monkeypatch, tmp_path):
    swf_path = tmp_path / "test.swf"
    swf_path.write_bytes(b"dummy")

    run_calls = []

    def fake_run_ffdec(args):
        run_calls.append(args)
        if args[0] == "-swf2xml":
            xml_path = Path(args[2])
            xml_path.write_text(SIMPLE_SWF_XML, encoding="utf-8")

    monkeypatch.setattr("modules.skyrim_swf_patcher.run_ffdec", fake_run_ffdec)

    result = patcher.patch_swf_internal_fontname(swf_path, "myfont")
    assert result is True

    assert run_calls[0][0] == "-swf2xml"
    assert run_calls[1][0] == "-xml2swf"
    assert not swf_path.with_suffix(".xml").exists()


def test_patch_swf_internal_fontname_returns_false_when_ffdec_fails(
    monkeypatch, tmp_path
):
    swf_path = tmp_path / "test.swf"
    swf_path.write_bytes(b"dummy")

    def fake_run_ffdec(_):
        raise RuntimeError("ffdec failed")

    monkeypatch.setattr("modules.skyrim_swf_patcher.run_ffdec", fake_run_ffdec)

    result = patcher.patch_swf_internal_fontname(swf_path, "myfont")
    assert result is False


def test_expand_font_slots_in_xml():
    expanded = patcher._expand_font_slots_in_xml(SIMPLE_SWF_XML, 3)
    entries = _get_font_entries(expanded)

    assert [font_id for font_id, _ in entries] == [1, 2, 3]


def test_patch_font_names_in_xml():
    expanded = patcher._expand_font_slots_in_xml(SIMPLE_SWF_XML, 2)
    patched = patcher._patch_font_names_in_xml(
        expanded, {1: "FontEvery", 2: "FontBook"}
    )
    entries = _get_font_entries(patched)

    assert entries == [(1, "FontEvery"), (2, "FontBook")]


def test_patch_font_names_in_xml_missing_font_id():
    with pytest.raises(ValueError, match="fontID=2"):
        patcher._patch_font_names_in_xml(SIMPLE_SWF_XML, {2: "Missing"})


def test_replace_glyphs_in_swf_replaces_all_character_ids(monkeypatch, tmp_path: Path):
    calls: list[int] = []

    def fake_run_ffdec(args: list[str]):
        if args[0] == "-swf2xml":
            xml_output = Path(args[2])
            xml_output.write_text(SIMPLE_SWF_XML, encoding="utf-8")
            return
        if args[0] == "-xml2swf":
            swf_output = Path(args[2])
            swf_output.write_bytes(b"FWS")
            return
        raise AssertionError(f"unexpected ffdec args: {args}")

    def fake_ffdec_replace(
        *,
        input_swf_path: str,
        output_swf_path: str,
        character_id: int,
        input_font_path: str,
    ):
        calls.append(character_id)
        output_path = Path(output_swf_path)
        output_path.write_bytes(Path(input_swf_path).read_bytes())

    monkeypatch.setattr(patcher, "run_ffdec", fake_run_ffdec)
    monkeypatch.setattr(patcher, "ffdec_replace", fake_ffdec_replace)

    template_swf = tmp_path / "template.swf"
    template_swf.write_bytes(b"FWS")
    output_swf = tmp_path / "out.swf"

    fonts = []
    for index in range(3):
        ttf_path = tmp_path / f"font_{index + 1}.ttf"
        ttf_path.write_bytes(b"ttf")
        fonts.append(ttf_path)

    patcher.replace_glyphs_in_swf(template_swf, output_swf, fonts)

    assert calls == [1, 2, 3]
    assert output_swf.exists()
