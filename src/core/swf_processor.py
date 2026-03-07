from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Mapping

from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf

from const import TEMPLATE_FONTSWF_PATH
from core.font_loader import reopen_font
from core.font_processor import is_otf_path
from modules.skyrim_swf_patcher import (
    patch_swf_internal_fontname,
    patch_swf_internal_fontnames,
    replace_glyph_in_swf,
    replace_glyphs_in_swf,
)

def process_swf(params: Mapping[str, Any]) -> None:
    """Individual SWF embedding process separated from GUI.
    
    Expected params:
    - output_swf_path: str
    - items: list of dicts with:
        - font_path: str
        - internal_name: str (optional)
    - debug: bool (optional)
    """
    debug = bool(params.get("debug", False))
    output_swf = params.get("output_swf_path")
    if not output_swf:
        raise ValueError("output_swf_path is required")
    
    items = params.get("items")
    if not items or not isinstance(items, list):
        raise ValueError("items (list of fonts to embed) is required")

    target_swf = TEMPLATE_FONTSWF_PATH
    output_swf_path = Path(output_swf).resolve()
    if not Path(target_swf).exists():
        raise FileNotFoundError(f"Template SWF not found: {target_swf}")

    output_swf_path.parent.mkdir(parents=True, exist_ok=True)

    prepared_items: list[tuple[Path, str]] = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        
        total_items = len(items)
        for index, item in enumerate(items, start=1):
            f_path_str = item.get("font_path")
            if not f_path_str:
                continue
            font_path = Path(f_path_str).resolve()
            internal_name = item.get("internal_name") or font_path.stem
            
            print(f"[{index}/{total_items}] {font_path.name}")
            
            if not font_path.exists():
                raise FileNotFoundError(f"Font file not found: {font_path}")
            
            if is_otf_path(font_path):
                if debug:
                    print(f"Converting OTF to TTF for embedding: {font_path.name}")
                # We reuse the logic from main_window.py but here in core
                with TTFont(str(font_path)) as source_font_obj:
                    loaded_font_obj = reopen_font(source_font_obj)
                    # otf_to_ttf expects a TTFont object with CFF table
                    otf_to_ttf(loaded_font_obj)
                    temp_ttf_path = temp_root / f"embed_{index:02d}_{font_path.stem}.ttf"
                    loaded_font_obj.save(str(temp_ttf_path))
                    prepared_items.append((temp_ttf_path, internal_name))
            else:
                prepared_items.append((font_path, internal_name))

        if not prepared_items:
            raise ValueError("No valid fonts to embed")

        if len(prepared_items) == 1:
            ttf_path, internal_name = prepared_items[0]
            if debug:
                print(f"Embedding single font: {internal_name} ({ttf_path.name})")
            replace_glyph_in_swf(Path(target_swf), output_swf_path, ttf_path)
            patch_swf_internal_fontname(output_swf_path, internal_name)
        else:
            ttf_paths = [p for p, _ in prepared_items]
            internal_names_by_id = {
                idx: name for idx, (_, name) in enumerate(prepared_items, start=1)
            }
            if debug:
                print(f"Embedding multiple fonts: {len(prepared_items)} fonts")
            replace_glyphs_in_swf(Path(target_swf), output_swf_path, ttf_paths)
            patch_swf_internal_fontnames(output_swf_path, internal_names_by_id)

    print(f"SWF embedding completed: {output_swf_path}")
