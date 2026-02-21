#!/usr/bin/env fontforge
import argparse
import os
import shutil
import sys
from pathlib import Path

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
from utils.common.dprint import dprint  # noqa: E402
from utils.common.save_font_ff import save_font_ff  # noqa: E402

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

BACKUP_SUFFIX = "_backup"
BACKUP_EXT = ".bak"


def main():
    parser = argparse.ArgumentParser(description="フォントを開く上書き保存する")

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントのパス",
    )
    parser.add_argument(
        "--backup_suffix",
        type=str,
        default=BACKUP_SUFFIX,
        help=f"元フォントのバックアップ接尾詞 デフォルト:{BACKUP_SUFFIX}",
    )
    parser.add_argument(
        "--backup_ext",
        type=str,
        default=BACKUP_EXT,
        help=f"元フォントのバックアップ拡張子 デフォルト:{BACKUP_EXT}",
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


def action_rewrite_font_ff(
    input_path: str, backup_suffix: str, backup_ext: str, debug: bool = False, **_
):
    rewrite_font_ff(
        input_path=input_path,
        backup_suffix=backup_suffix,
        backup_ext=backup_ext,
        debug=debug,
    )


def rewrite_font_ff(
    input_path: str,
    backup_ext: str = BACKUP_EXT,
    debug: bool = False,
    **_,
):
    input_path = Path(input_path).resolve()  # 絶対パス化
    dprint(
        f"input_path: {str(input_path)}, backup_ext: {backup_ext}",
        debug,
    )
    # バックアップを作成
    if not backup_ext:
        backup_ext = BACKUP_EXT  # デフォルトを .bak に設定

    if not backup_ext.startswith("."):
        backup_ext = f".{backup_ext}"

    # input_path.name が "font1.ttf" の場合、 "font1.ttf.bak" にする。
    backup_path = input_path.with_name(f"{input_path.name}{backup_ext}")
    try:
        shutil.copy2(input_path, backup_path)
        print(f"バックアップを作成しました: {str(backup_path.resolve())}")
    except Exception as e:
        print(f"{e}")
        print("バックアップ作成に失敗したため上書きを行いません。")
        return

    # 上書き実行
    input_font_obj_ff = fontforge.open(
        str(input_path)
    )  # fontforge.open は 'with' 文に対応していない場合があるため。
    try:
        saved_output_path = save_font_ff(
            font_obj_ff=input_font_obj_ff,
            output_path=str(input_path),
            debug=debug,
        )
        print(f"フォントを上書きしました: {saved_output_path}")
    finally:
        input_font_obj_ff.close()


if __name__ == '__main__':
    main()
