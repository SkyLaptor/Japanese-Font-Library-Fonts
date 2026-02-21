from pathlib import Path

from const import BUILD_DIR
from utils.common.dprint import dprint


def save_font_ff(
    font_obj_ff,  # fontforgeのフォントタイプオブジェクト。正しい型名が分からないのでAny
    input_path: str = "",
    output_path: str = "",
    suffix: str = "",
    ext: str = "",
    debug: bool = False,
):
    # 1. 基準となるパスを決定
    base_path = Path(output_path) if output_path else Path(input_path)
    if not base_path or str(base_path) == ".":
        raise ValueError("パスを特定できません。")

    # 2. 拡張子の決定
    # 引数 ext が優先、なければ base_path のもの、それもなければ .ttf
    actual_ext = ext if ext else base_path.suffix
    if not actual_ext:
        actual_ext = ".ttf"
    if not actual_ext.startswith("."):
        actual_ext = f".{actual_ext}"

    # 3. 最終的な出力パスの組み立て
    # output_path が指定されていて、かつ suffix も ext も指定されていない時だけ
    # そのままのパスを使い、それ以外は加工する
    if output_path and not suffix and not ext:
        final_output_path = Path(output_path)
    else:
        # output_path があっても suffix があれば、そのディレクトリを維持してファイル名を変える
        final_output_path = base_path.with_stem(
            f"{base_path.stem}{suffix}"
        ).with_suffix(actual_ext)

    # 4. (オプション) output_path がない場合のデフォルトディレクトリ指定
    if not output_path and 'BUILD_DIR' in globals():
        final_output_path = Path(BUILD_DIR) / final_output_path.name

    final_output_path_abs = final_output_path.resolve()
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)

    dprint(f"final_output_path_abs: {final_output_path_abs}", debug)
    font_obj_ff.generate(str(final_output_path_abs), flags=("winkern",))

    return str(final_output_path_abs)
