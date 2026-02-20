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

from utils.common.save_font_ff import save_font_ff  # noqa: E402

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"


def main():
    parser = argparse.ArgumentParser(description="フォントを開く上書き保存する")

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントのパス",
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

    action_rewrite_font_ff(**vars(args))


def action_rewrite_font_ff(input_path: str, debug: bool = False, **_):
    input_font_obj_ff = fontforge.open(input_path)
    saved_output_path = save_font_ff(
        font_obj_ff=input_font_obj_ff,
        input_path=input_path,
        output_path=input_path,
        debug=debug,
    )
    print(f"フォントを上書き保存しました: {saved_output_path}")
    input_font_obj_ff.close()


if __name__ == '__main__':
    main()
