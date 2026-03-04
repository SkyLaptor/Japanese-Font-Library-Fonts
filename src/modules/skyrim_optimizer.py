# Dependencies: FFDec=False, FontForge=False
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont

from const import (
    CONDENSE_RATIO_CONFIGS,
    EXCLUDE_CHARS,
    SKYRIM_BASE_FONT_CONFIGS,
)
from modules.anonymize_info import anonymize_info
from modules.create_subset import create_subset
from modules.get_info import get_info
from modules.harmonize_font_metrics import harmonize_font_metrics
from modules.remove_empty_glyphs import remove_empty_glyphs
from utils.dprint import dprint
from utils.file_io import load_text, save_font, save_text


def rewrite_font_with_fonttools(
    input_path: str | Path,
    backup_ext: str = ".bak",
) -> bool:
    target_path = Path(input_path).resolve()
    if not target_path.exists():
        return False

    if not backup_ext.startswith("."):
        backup_ext = f".{backup_ext}"

    backup_path = target_path.with_name(f"{target_path.name}{backup_ext}")
    try:
        shutil.copy2(target_path, backup_path)
        with TTFont(str(target_path)) as font_obj:
            font_obj.save(str(target_path))
        return True
    except Exception:
        return False


def convert(
    target_font_path: str,
    output_font_path: str,
    subset_file_path: str = "",
    base_type: str = "every",
    condense_type: str = "normal",
    offset_height: int = 0,
    mode_monospace: bool = False,
    anonymize: bool = False,
    output_font_info: bool = False,
    debug: bool = False,
):
    target_path = Path(target_font_path)
    if not target_path.exists():
        raise FileNotFoundError(f"フォントファイルが見当たりません: {target_font_path}")

    base_font_path = SKYRIM_BASE_FONT_CONFIGS.get(base_type)
    if not base_font_path or not base_font_path.exists():
        raise FileNotFoundError(
            f"ベースフォントファイルが見つかりません: {base_font_path}"
        )

    if subset_file_path and not Path(subset_file_path).exists():
        raise FileNotFoundError(
            f"サブセットファイルが見つかりません: {subset_file_path}"
        )

    base_font_obj = TTFont(base_font_path)
    target_font_obj = TTFont(target_path)

    print("空白グリフを消去しています...")
    max_retries = 3
    for i in range(max_retries):
        try:
            target_font_obj = remove_empty_glyphs(font_obj=target_font_obj, debug=debug)
            break
        except Exception as e:
            if i < max_retries - 1:
                print(e)
                print(
                    f"空白グリフの消去に失敗しました。フォントの上書きを試行します: {target_path.name}"
                )
                try:
                    print(f"上書き中...: {target_path.name}")
                    rewritten = rewrite_font_with_fonttools(
                        input_path=target_path,
                        backup_ext=".bak",
                    )
                    if not rewritten:
                        print("[失敗]: 上書き処理時にエラーが発生しました")
                        continue
                    print(
                        "上書きに成功しました。上書き後のフォントを使用して空白グリフ消去処理を再度実行します。"
                    )
                    target_font_obj = TTFont(str(target_path.resolve()))
                except Exception:
                    print("[失敗]: 上書き処理時にエラーが発生しました")
            else:
                print("[失敗]: 規定回数内に処理できませんでした。")
                return False

    scale_width = 1.0
    if not mode_monospace:
        scale_width = CONDENSE_RATIO_CONFIGS.get(condense_type, 1.0)

    print("グリフを変形・移動しています...")
    result = harmonize_font_metrics(
        target_font_obj=target_font_obj,
        base_font_obj=base_font_obj,
        scale_width_manual=scale_width,
        scale_height_manual=1.0,
        offset_width=0,
        offset_height=offset_height,
    )
    target_font_obj = result.font_obj
    dprint(
        f"最終的な拡大縮小率: 横:x{result.final_scale_width:.3f}, 縦:x{result.final_scale_height:.3f}",
        debug,
    )

    if subset_file_path:
        print(f"サブセットを作成しています...: {subset_file_path}")
        target_font_obj = create_subset(
            font_obj=target_font_obj,
            subset_text=load_text(subset_file_path, exclude_chars=EXCLUDE_CHARS),
            debug=debug,
        )

    if anonymize:
        print("匿名化を実施しています...")
        target_font_obj = anonymize_info(font_obj=target_font_obj, font_name=base_type)

    suffix = f"_{base_type}_{condense_type}"
    print("フォントを出力しています...")

    save_font(
        font_obj=target_font_obj,
        input_path=str(target_path),
        output_path=output_font_path,
        suffix=suffix,
    )

    if output_font_path and output_font_info:
        info_output_path = Path(output_font_path).with_suffix(".txt")

        save_text(
            content=str(get_info(target_font_obj)),
            input_path=str(target_path),
            output_path=str(info_output_path),
            suffix="",
        )
    else:
        if output_font_info:
            save_text(
                content=str(get_info(target_font_obj)),
                input_path=str(target_path),
                suffix=suffix,
            )

    print("処理が完了しました！")
