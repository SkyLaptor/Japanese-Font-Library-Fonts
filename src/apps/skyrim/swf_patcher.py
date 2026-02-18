import subprocess
from pathlib import Path

from const import DUMMY_FONT_NAME_IN_SWF, ENCODE, FONTFILE_NAME_PREFIX, SWF_NAME_RULES


def patch_swf_internal_fontname(swf_path: Path, font_name: str) -> bool:
    """
    SWF内のフォント名を書き換える。
    一時的にXMLへデコードしてテキスト置換を行い、再度SWFへエンコードします。
    """
    xml_path = swf_path.with_suffix(".xml")
    try:
        # SWF -> XML
        subprocess.run(
            ["ffdec-cli", "-swf2xml", str(swf_path), str(xml_path)],
            check=True,
            capture_output=True,
        )

        # 置換
        xml_content = xml_path.read_text(encoding=ENCODE)
        xml_path.write_text(
            xml_content.replace(DUMMY_FONT_NAME_IN_SWF, font_name), encoding=ENCODE
        )

        # XML -> SWF
        subprocess.run(
            ["ffdec-cli", "-xml2swf", str(xml_path), str(swf_path)],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"  [ERROR] XML Patch failed: {e}")
        return False
    finally:
        if xml_path.exists():
            xml_path.unlink()


def replace_glyph_in_swf(template_path: Path, output_path: Path, ttf_path: Path):
    """
    FFDecを使用してTTFファイルをSWFファイル内のフォント定義と差し替えます。
    """
    cmd = [
        "ffdec-cli",
        "-replace",
        str(template_path),
        str(output_path),
        "1",
        str(ttf_path),
    ]
    # shell=TrueはWindows環境でのffdec-cli(バッチファイル)呼び出しに必要
    subprocess.run(cmd, check=True, capture_output=True, text=True, shell=True)


def get_swf_name(font_name: str, font_file_name: str) -> str:
    """ファイル名からスカイリムの命名規則に従ったSWF名を生成する。"""

    features_part = font_file_name.lower().replace(font_name.lower(), "")
    results = []

    # 各カテゴリごとにルールを適用
    for category in ["weight", "ui", "condense", "subset"]:
        rules = SWF_NAME_RULES.get(category, [])
        for keywords, suffix in rules:
            if any(kw in features_part for kw in keywords):
                results.append(suffix)
                break

    suffixes = "".join(results)
    return f"{FONTFILE_NAME_PREFIX}{font_name}{suffixes}.swf"
