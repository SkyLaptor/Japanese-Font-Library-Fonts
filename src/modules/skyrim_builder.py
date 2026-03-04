# Dependencies: FFDec=True, FontForge=False
import csv
import re
import shutil
import time
from pathlib import Path

from fontTools.ttLib import TTFont

from const import (
    BASE_LINE_TARGET,
    MERGE_CONF_PATH,
    SKYRIM_BASE_KEYNAME,
    SKYRIM_EXPORT_MATRIX,
    TEMPLATE_FONTSWF_PATH,
)
from modules.get_offset_to_align_bottom import get_offset_to_align_bottom
from modules.merge_font import action_merge_font
from modules.skyrim_optimizer import convert
from modules.skyrim_swf_patcher import (
    get_swf_name,
    patch_swf_internal_fontname,
    replace_glyph_in_swf,
)
from utils.dprint import dprint


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def action_premerge_export(
    work_dir: str,
    base_line: int,
    anonymize: bool,
    output_font_info: bool,
    debug: bool = False,
    **_,
) -> None:
    premerge_export(
        work_dir=work_dir,
        base_line=base_line,
        anonymize=anonymize,
        output_font_info=output_font_info,
        debug=debug,
    )


def premerge_export(
    work_dir: str,
    base_line: int = BASE_LINE_TARGET,
    anonymize: bool = False,
    output_font_info: bool = False,
    debug: bool = False,
) -> None:
    suffix = "_premerge"
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_files = [f for f in font_dir.glob("*.ttf") if suffix not in f.name]
        if not font_files:
            continue

        print(f"\n[事前調整フォント出力]: {font_dir.name}")

        for font_path in font_files:
            base = "every"
            offset_height = 0
            try:
                with TTFont(str(font_path)) as tmp_font:
                    offset_height = get_offset_to_align_bottom(
                        tmp_font, base_line, debug
                    )
                print(
                    f"  [オフセット計算]: ベースライン値: {base_line}, このフォントのオフセット値: {offset_height}"
                )
            except Exception as e:
                print(
                    f"  [警告]: 自動計算に失敗しました。オフセット0で進めます。詳細: {e}"
                )
                offset_height = 0

            stem_lower = font_path.stem.lower()
            clean_stem = re.sub(
                r'-(bold|medium|thin|light|regular|black|heavy|semibold|extrabold|extralight)',
                r'_\1',
                stem_lower,
            )

            output_path = font_dir / f"{clean_stem}{suffix}.ttf"

            try:
                convert(
                    target_font_path=str(font_path),
                    output_font_path=str(output_path),
                    base_type=base,
                    offset_height=offset_height,
                    anonymize=anonymize,
                    output_font_info=output_font_info,
                )
                print(f"  [出力成功]: {output_path.name}")
            except Exception as e:
                print(f"  [エラー]: {font_path.name} 詳細: {e}")

    print("\n--- 全ての対象フォントの事前調整が完了しました ---")


def action_variant_export(
    work_dir: str, anonymize: bool, output_font_info: bool, debug: bool = False, **_
) -> None:
    variant_export(
        work_dir=work_dir, anonymize=anonymize, output_font_info=output_font_info
    )


def variant_export(
    work_dir: str,
    anonymize: bool = False,
    output_font_info: bool = False,
    debug: bool = False,
) -> None:
    search_root = Path(work_dir).resolve()
    target_pattern = "*_merged.ttf"

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        merged_fonts = list(font_dir.glob(target_pattern))
        if not merged_fonts:
            continue

        print(f"\n[バリアントフォント出力]: {font_dir.name}")

        for target_font in merged_fonts:
            dprint(f"元の名前: {target_font}", debug)
            clean_base_name = target_font.stem.replace("_merged", "")
            dprint(f"_mergedを取り除いた名前: {clean_base_name}", debug)

            for item in SKYRIM_EXPORT_MATRIX:
                base = item["base"]
                condense = item["condense"]
                label = item["label"]
                subset_path = item["path"]

                dprint(f"マトリクス: {item}", debug)

                temp_name = clean_base_name
                temp_name = re.sub(r'[-_]medium', '', temp_name, flags=re.IGNORECASE)
                temp_name = re.sub(
                    r'[-_]regular', '_regular', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(r'[-_]thin', '_thin', temp_name, flags=re.IGNORECASE)
                temp_name = re.sub(
                    r'[-_]extralight', '_extralight', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]light', '_light', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]semibold', '_semibold', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(r'[-_]bold', '_bold', temp_name, flags=re.IGNORECASE)
                temp_name = re.sub(
                    r'[-_]extrabold', '_extrabold', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]heavy', '_heavy', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]black', '_black', temp_name, flags=re.IGNORECASE
                )

                base_parts = [p for p in temp_name.split("_") if p]
                parts = base_parts
                if base:
                    parts.append(base)
                if condense not in ["normal"]:
                    parts.append(condense)
                if label not in ["full"]:
                    parts.append(label)

                out_name_base = "_".join(parts)
                dprint(f"最終的な名前: {out_name_base}", debug)
                out_name = f"{out_name_base}.ttf"

                out_path = font_dir / out_name

                try:
                    convert(
                        target_font_path=str(target_font),
                        output_font_path=str(out_path),
                        subset_file_path=str(subset_path),
                        base_type=base,
                        condense_type=condense,
                        offset_height=0,
                        anonymize=anonymize,
                        output_font_info=output_font_info,
                    )
                    print(f"  -> [生成完了]: {out_name}")
                except Exception as e:
                    print(f"  [エラー]: {out_name} 詳細: {e}")

    print("\n--- 全ての対象フォントのバリアント化が完了しました ---")


def action_swf_export(work_dir: str, debug: bool = False, **_) -> None:
    swf_export(work_dir=work_dir)


def swf_export(work_dir: str, debug: bool = False) -> None:
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_name = font_dir.name
        dprint(f"フォント名(ディレクトリ名から取得): {font_name}")

        variant_fonts = [
            f
            for f in font_dir.glob("*.ttf")
            if any(k in f.name for k in SKYRIM_BASE_KEYNAME)
            and "_merged" not in f.name
            and "_premerge" not in f.name
        ]

        if not variant_fonts:
            continue

        print(f"\n[フォントSWF出力]: {font_name}")
        for ttf_path in variant_fonts:
            stem_name = ttf_path.stem

            swf_filename = get_swf_name(font_name, stem_name)
            output_swf_path = font_dir / swf_filename

            internal_font_name = swf_filename.replace("fonts_", "").replace(".swf", "")
            print(f"  -> 変換元: {ttf_path.name}")
            print(f"  -> 処理後: {swf_filename} (内部フォント名: {internal_font_name})")

            max_retries = 3
            for i in range(max_retries):
                try:
                    replace_glyph_in_swf(
                        TEMPLATE_FONTSWF_PATH, output_swf_path, ttf_path
                    )
                    time.sleep(0.5)
                    patched = patch_swf_internal_fontname(
                        output_swf_path, internal_font_name
                    )
                    if not patched:
                        raise RuntimeError("SWF内部フォント名パッチに失敗しました")
                    print(f"  [成功]: {swf_filename}")
                    break
                except Exception as e:
                    if i < max_retries - 1:
                        print(
                            f"  [再試行]: {swf_filename} 処理失敗（{e}）。{i+1}度目の再試行中..."
                        )
                        time.sleep(1.0)
                    else:
                        print(
                            f"  [失敗]: {swf_filename} が規定回数内に処理できませんでした。"
                        )

    print("\n--- 全ての対象フォントのSWF化が完了しました ---")


def action_merge_fonts(
    work_dir: str, merge_conf: str = MERGE_CONF_PATH, debug: bool = False, **_
):
    merge_font(work_dir=work_dir, merge_conf=merge_conf, debug=debug)


def merge_font(work_dir: str, merge_conf: str = MERGE_CONF_PATH, debug: bool = False):
    if not Path(merge_conf).exists():
        print(f"[エラー] CSVファイルが見つかりません: {merge_conf}")
        return

    print(f"\n[マージ一括処理開始]: {merge_conf}")

    with open(merge_conf, "r", encoding="utf_8_sig") as f:
        reader = csv.reader(f)

        try:
            header = next(reader)
            dprint(f"ヘッダー '{header}' をスキップしました", debug)
        except StopIteration:
            return

        for row in reader:
            if not row or row[0].startswith("#") or len(row) < 3:
                continue

            vals = [s.strip() for s in row[:3]]
            base, sub, out = vals
            if not base or not out:
                continue

            is_copy_only = not sub

            base_path = (Path(work_dir) / base.lstrip("/\\")).resolve()
            sub_path = None
            if not is_copy_only:
                sub_path = (Path(work_dir) / sub.lstrip("/\\")).resolve()
            out_path = (Path(work_dir) / out.lstrip("/\\")).resolve()

            if is_copy_only:
                try:
                    print(f"\nコピー処理中: {base_path.name}")
                    shutil.copy2(str(base_path), str(out_path))
                    print(f">>  コピー先: {out_path.name}")
                    print("   [成功]")
                    continue
                except Exception as e:
                    print(f"   [失敗] {e}")
                    continue

            print(f"\nマージ処理中: {base_path.name} <- {sub_path.name}")
            print(f">>  出力先: {out_path.name}")

            try:
                action_merge_font(
                    base_path=str(base_path),
                    interpolation_path=str(sub_path),
                    output_path=str(out_path),
                    debug=debug,
                )
                print("   [成功]")
            except Exception as e:
                print(f"   [失敗] {e}")

    print("\n--- 全てのマージ処理が完了しました ---")


ACTION_MAP = {
    "premerge_export": action_premerge_export,
    "variant_export": action_variant_export,
    "swf_export": action_swf_export,
    "merge_font": action_merge_fonts,
}
