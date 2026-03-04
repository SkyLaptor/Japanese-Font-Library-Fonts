# Dependencies: FFDec=True, FontForge=False
from pathlib import Path

from const import (
    DUMMY_FONT_NAME_IN_SWF,
    ENCODE,
    FONTFILE_NAME_PREFIX,
    SWF_NAME_RULES,
)
from core.ffdec_wrapper import ffdec_replace, run_ffdec


def patch_swf_internal_fontname(swf_path: Path, font_name: str) -> bool:
    xml_path = swf_path.with_suffix(".xml")
    try:
        run_ffdec(["-swf2xml", str(swf_path), str(xml_path)])

        xml_content = xml_path.read_text(encoding=ENCODE)
        xml_path.write_text(
            xml_content.replace(DUMMY_FONT_NAME_IN_SWF, font_name), encoding=ENCODE
        )

        run_ffdec(["-xml2swf", str(xml_path), str(swf_path)])
        return True
    except Exception as e:
        print(f"  [エラー] XML パッチPatch failed: {e}")
        return False
    finally:
        if xml_path.exists():
            xml_path.unlink()


def replace_glyph_in_swf(template_path: Path, output_path: Path, ttf_path: Path):
    ffdec_replace(
        input_swf_path=str(template_path),
        output_swf_path=str(output_path),
        character_id=1,
        input_font_path=str(ttf_path),
    )


def get_swf_name(font_name: str, font_file_name: str) -> str:
    features_part = font_file_name.lower().replace(font_name.lower(), "")
    feature_parts_list = features_part.split("_")

    results = []
    for category in ["weight", "ui", "condense", "subset"]:
        rules = SWF_NAME_RULES.get(category, [])
        for keywords, suffix in rules:
            if any(kw in feature_parts_list for kw in keywords):
                results.append(suffix)
                break

    suffixes = "".join(results)
    return f"{FONTFILE_NAME_PREFIX}{font_name}{suffixes}.swf"
