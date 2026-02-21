#!/usr/bin/env fontforge
import argparse
import os
import sys

# プロジェクトのルートを特定
current_dir = os.path.dirname(os.path.abspath(__file__))
# merge_font_ff.py は src/utils/modifier にあるので、3つ上の階層がリポジトリルート
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_dir = os.path.join(repo_root, "src")

# 1. 仮想環境（.venv）のライブラリパスを追加
# Windowsの場合、通常は .venv/Lib/site-packages にあります
venv_site_packages = os.path.join(repo_root, ".venv", "Lib", "site-packages")

if venv_site_packages not in sys.path and os.path.exists(venv_site_packages):
    sys.path.append(venv_site_packages)

# 2. プロジェクトのソースパスを追加
if src_dir not in sys.path:
    sys.path.append(src_dir)

import fontforge  # type: ignore # noqa: E402

# fontforege内包モジュール以外はこれ以降でimportすること。
from utils.common.save_font_ff import save_font_ff  # noqa: E402

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"


def main():
    parser = argparse.ArgumentParser(description="2つのフォントを結合する")

    parser.add_argument(
        "base_path",
        type=str,
        help="ベースとなるフォントのパス",
    )
    parser.add_argument(
        "interpolation_path",
        type=str,
        help="補間を行うフォントのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="結合済みフォントの書き出し先",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ表示の有効化",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    action_merge_font_ff(**vars(args))


def action_merge_font_ff(
    base_path: str, interpolation_path: str, output_path: str, debug: bool = False, **_
):
    base_font_obj_ff = fontforge.open(base_path)
    merged_font_obj_ff = merge_font_ff(base_font_obj_ff, interpolation_path, debug)
    if output_path is not None:
        saved_output_path = save_font_ff(
            font_obj_ff=merged_font_obj_ff,
            input_path=base_path,
            output_path=output_path,
            debug=debug,
        )
        print(f"フォントを保存しました: {saved_output_path}")
    merged_font_obj_ff.close()


def merge_font_ff(base_font_obj_ff, interpolation_path: str, debug: bool = False):
    """
    2つのフォントを結合する

    :param base_font_obj_ff: fontforge型フォントオブジェクト
    :param interpolation_path: 補間フォントのファイルパス
    :type interpolation_path: str
    :param debug: デバッグモード
    :type debug: bool
    """
    base_font_obj_ff.mergeFonts(interpolation_path)
    return base_font_obj_ff


if __name__ == '__main__':
    main()
