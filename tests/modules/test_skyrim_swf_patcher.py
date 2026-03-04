from pathlib import Path

from modules.skyrim_swf_patcher import patch_swf_internal_fontname, replace_glyph_in_swf


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

    replace_glyph_in_swf(template_path, output_path, font_path)

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
            xml_path.write_text("name=REPLACE_ME_FONT_NAME_LENGTH_MAX_XXXXXXXXXXXXXXX")

    monkeypatch.setattr("modules.skyrim_swf_patcher.run_ffdec", fake_run_ffdec)

    result = patch_swf_internal_fontname(swf_path, "myfont")
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

    result = patch_swf_internal_fontname(swf_path, "myfont")
    assert result is False
