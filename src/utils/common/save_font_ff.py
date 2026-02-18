import os
from pathlib import Path

from const import BUILD_DIR


def save_font_ff(
    font_obj_ff,  # fontforgeのフォントタイプオブジェクト。正しい型名が分からないのでAny
    input_path: str = "",
    output_path: str = "",
    suffix: str = "",
    ext: str = "",
    debug: bool = False,
):
    if not input_path and not output_path:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )

    final_output_path = ""
    if not output_path:
        os.makedirs(BUILD_DIR, exist_ok=True)
        # 拡張子の決定
        # 1. 引数 ext があればそれを使う
        # 2. なければ input_path の拡張子を使う
        # 3. それでもなければ ".ttf" にする
        input_p = Path(input_path)
        actual_ext = ext if ext else input_p.suffix
        if not actual_ext:
            actual_ext = ".ttf"
        # ドットの調整（".ttf" でも "ttf" でも受け入れるように）
        if not actual_ext.startswith("."):
            actual_ext = f".{actual_ext}"
        final_output_path = Path(BUILD_DIR) / f"{input_p.stem}{suffix}{actual_ext}"
    else:
        final_output_path = Path(output_path)

    final_output_path_abs = final_output_path.resolve()
    # 途中のディレクトリが存在しなければ作成
    final_output_path_abs.parent.mkdir(parents=True, exist_ok=True)

    font_obj_ff.generate(str(final_output_path_abs), flags=("winkern",))

    return str(final_output_path_abs)
