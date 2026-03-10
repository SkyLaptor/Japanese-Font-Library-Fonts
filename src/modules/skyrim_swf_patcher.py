# Dependencies: FFDec=True, FontForge=False
import copy
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from const import ENCODE
from core.ffdec_wrapper import ffdec_replace, run_ffdec

FONT_TAG_TYPES = {"DefineFont2Tag", "DefineFont3Tag", "DefineFont4Tag"}


def _get_font_items(root: ET.Element) -> list[ET.Element]:
    return [
        item
        for item in root.findall("./tags/item")
        if item.attrib.get("type") in FONT_TAG_TYPES and "fontID" in item.attrib
    ]


def _expand_font_slots_in_xml(xml_content: str, slot_count: int) -> str:
    if slot_count < 1:
        raise ValueError("slot_count は1以上である必要があります")

    root = ET.fromstring(xml_content)
    tags_element = root.find("./tags")
    if tags_element is None:
        raise ValueError("SWF XMLに tags 要素が見つかりません")

    font_items = _get_font_items(root)
    if not font_items:
        raise ValueError("SWF XMLにフォント定義タグが見つかりません")

    template_item = font_items[0]
    base_font_id = int(template_item.attrib["fontID"])

    while len(font_items) < slot_count:
        cloned = copy.deepcopy(template_item)
        tags_element.append(cloned)
        font_items.append(cloned)

    for index, item in enumerate(font_items[:slot_count]):
        item.attrib["fontID"] = str(base_font_id + index)

    return ET.tostring(root, encoding=ENCODE, xml_declaration=True).decode(ENCODE)


def _get_base_font_id_from_xml(xml_content: str) -> int:
    root = ET.fromstring(xml_content)
    font_items = _get_font_items(root)
    if not font_items:
        raise ValueError("SWF XMLにフォント定義タグが見つかりません")
    return int(font_items[0].attrib["fontID"])


def _patch_font_names_in_xml(xml_content: str, font_names_by_id: dict[int, str]) -> str:
    root = ET.fromstring(xml_content)
    font_items = _get_font_items(root)
    id_to_item = {int(item.attrib["fontID"]): item for item in font_items}

    for font_id, font_name in font_names_by_id.items():
        item = id_to_item.get(font_id)
        if item is None:
            raise ValueError(f"fontID={font_id} のフォント定義が見つかりません")
        item.attrib["fontName"] = font_name

    return ET.tostring(root, encoding=ENCODE, xml_declaration=True).decode(ENCODE)


def patch_swf_internal_fontname(swf_path: Path, font_name: str) -> bool:
    return patch_swf_internal_fontnames(swf_path, {1: font_name})


def patch_swf_internal_fontnames(
    swf_path: Path, font_names_by_id: dict[int, str]
) -> bool:
    xml_path = swf_path.with_suffix(".xml")
    try:
        print("SWF内部名を更新中: XMLエクスポート...")
        # 事前に旧XMLが残っていれば削除（上書き衝突を避ける）
        if xml_path.exists():
            try:
                xml_path.unlink()
            except Exception:
                pass
        run_ffdec(["-swf2xml", str(swf_path), str(xml_path)])

        print("SWF内部名を更新中: XMLパッチ適用...")
        xml_content = xml_path.read_text(encoding=ENCODE)

        # 渡されたキーが1..Nの連番（スロット順）である場合に対応するため、
        # 実際のfontIDへマッピングし直す。
        try:
            root = ET.fromstring(xml_content)
            font_items = _get_font_items(root)
            # 位置（1-based）→実fontID
            pos_to_id: dict[int, int] = {
                i + 1: int(item.attrib["fontID"]) for i, item in enumerate(font_items)
            }
            effective_names_by_id: dict[int, str] = {}
            for k, v in font_names_by_id.items():
                actual_id = pos_to_id.get(int(k), None)
                if actual_id is None:
                    # k自体をfontIDとみなしてそのまま使う（後方互換）
                    actual_id = int(k)
                effective_names_by_id[actual_id] = v
        except Exception:
            # パースに失敗した場合はそのままのマップで適用を試みる
            effective_names_by_id = {int(k): v for k, v in font_names_by_id.items()}

        patched = _patch_font_names_in_xml(xml_content, effective_names_by_id)
        xml_path.write_text(patched, encoding=ENCODE)

        print("SWF内部名を更新中: XMLインポート...")
        run_ffdec(["-xml2swf", str(xml_path), str(swf_path)])
        return True
    except subprocess.CalledProcessError as e:
        detail = e.stderr or e.stdout or "(no output)"
        print(
            "  [エラー] XML パッチPatch failed: FFDec execution failed with non-zero exit.\n"
            f"    Command: {' '.join(e.cmd) if hasattr(e, 'cmd') else '(unknown)'}\n"
            f"    Output: {detail}"
        )
        return False
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


def replace_glyphs_in_swf(
    template_path: Path,
    output_path: Path,
    ttf_paths: list[Path],
    font_names_by_position: dict[int, str] | None = None,
) -> None:
    if not ttf_paths:
        raise ValueError("埋め込み対象TTFが未指定です")

    if len(ttf_paths) == 1:
        replace_glyph_in_swf(template_path, output_path, ttf_paths[0])
        return

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        template_xml_path = temp_root / "template.xml"
        expanded_xml_path = temp_root / "template_expanded.xml"
        expanded_swf_path = temp_root / "template_expanded.swf"

        # テンプレートのfontID起点を取得
        run_ffdec(["-swf2xml", str(template_path), str(template_xml_path)])
        template_xml_text = template_xml_path.read_text(encoding=ENCODE)
        base_font_id = _get_base_font_id_from_xml(template_xml_text)

        # スロットを必要数へ拡張
        expanded_xml = _expand_font_slots_in_xml(template_xml_text, len(ttf_paths))
        # 可能であれば、この段階で内部フォント名を付与しておく（後段の巨大SWFに対するswf2xmlを回避）
        if font_names_by_position:
            try:
                # 位置(1..N)→実fontIDへの変換
                id_map: dict[int, str] = {
                    base_font_id + (int(pos) - 1): name
                    for pos, name in font_names_by_position.items()
                }
                expanded_xml = _patch_font_names_in_xml(expanded_xml, id_map)
            except Exception:
                # 名前付与は最終段にフォールバック（ただし本関数では最終段パッチは行わない）
                pass
        expanded_xml_path.write_text(expanded_xml, encoding=ENCODE)
        run_ffdec(["-xml2swf", str(expanded_xml_path), str(expanded_swf_path)])

        current_input = expanded_swf_path
        total = len(ttf_paths)
        for index, ttf_path in enumerate(ttf_paths, start=1):
            print(f"[{index}/{total}] 埋め込み中: {ttf_path.name}")
            next_output = (
                output_path if index == total else temp_root / f"step_{index}.swf"
            )
            ffdec_replace(
                input_swf_path=str(current_input),
                output_swf_path=str(next_output),
                # fontIDはテンプレートの起点から連番で付与しているため
                # 実際のcharacter_idは base_font_id + (index - 1)
                character_id=base_font_id + (index - 1),
                input_font_path=str(ttf_path),
            )
            current_input = next_output
