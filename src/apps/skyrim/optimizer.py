import argparse
import subprocess
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

# 自前モジュールのインポート
from const import (
    CONDENSE_RATIO_CONFIGS,
    EXCLUDE_CHARS,
    FONTFORGE_PATH,
    REWRITE_FONT_FF_PATH,
    SKYRIM_BASE_FONT_CONFIGS,
)
from utils.common.dprint import dprint
from utils.common.load_text import load_text
from utils.common.save_font import save_font
from utils.common.save_text import save_text
from utils.inspector.get_info import get_info
from utils.modifier.anonymize_info import anonymize_info
from utils.modifier.harmonize_font_metrics import harmonize_font_metrics
from utils.subsetter.create_subset import create_subset
from utils.subsetter.remove_empty_glyphs import remove_empty_glyphs


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
    """
    渡されたフォントをスカイリムのUI向けに最適化します。
    """
    target_path = Path(target_font_path)
    if not target_path.exists():
        raise FileNotFoundError(f"フォントファイルが見当たりません: {target_font_path}")

    # const.py からベースフォントのパスを取得
    base_font_path = SKYRIM_BASE_FONT_CONFIGS.get(base_type)
    if not base_font_path or not base_font_path.exists():
        raise FileNotFoundError(
            f"ベースフォントファイルが見つかりません: {base_font_path}"
        )

    if subset_file_path and not Path(subset_file_path).exists():
        raise FileNotFoundError(
            f"サブセットファイルが見つかりません: {subset_file_path}"
        )

    # 1. フォントの読み込み
    base_font_obj = TTFont(base_font_path)
    target_font_obj = TTFont(target_path)

    # 2. 空白グリフの消去
    print("空白グリフを消去しています...")
    # フォントによってはFontforgeによる上書きが必要である模様です。
    max_retries = 3
    for i in range(max_retries):
        try:
            target_font_obj = remove_empty_glyphs(font_obj=target_font_obj, debug=debug)
            break  # 正常に完了した場合はループを抜ける。
        except Exception as e:
            if i < max_retries - 1:
                print(e)
                print(
                    f"空白グリフの消去に失敗しました。フォントの上書きを試行します: {target_path.name}"
                )
                rewrite_cmd = [
                    str(FONTFORGE_PATH),
                    "-quiet",
                    "-script",
                    str(REWRITE_FONT_FF_PATH),
                    str(target_path.resolve()),
                    "--backup_ext",
                    ".bak",
                ]
                try:
                    print(f"上書き中...: {target_path.name}")
                    subprocess.run(
                        rewrite_cmd,
                        check=True,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                    print(
                        "上書きに成功しました。上書き後のフォントを使用して空白グリフ消去処理を再度実行します。"
                    )
                    target_font_obj = TTFont(str(target_path.resolve()))
                except subprocess.CalledProcessError as e_retry:
                    print(e_retry.stderr)
                    print("[失敗]: 上書き処理時にエラーが発生しました")
            else:
                print("[失敗]: 規定回数内に処理できませんでした。")
                return False

    # 3. グリフの変形（メトリクス調整）
    scale_width = 1.0
    if not mode_monospace:
        scale_width = CONDENSE_RATIO_CONFIGS.get(condense_type, 1.0)

    # 【修正ポイント】
    # 倍率が 1.0 かつ オフセットが 0 なら、変形処理を通す必要がない
    if scale_width == 1.0 and offset_height == 0:
        print("変形・移動の必要がないため、メトリクス調整をスキップします。")
    else:
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

    # 4. サブセット作成
    if subset_file_path:
        print(f"サブセットを作成しています...: {subset_file_path}")
        target_font_obj = create_subset(
            font_obj=target_font_obj,
            subset_text=load_text(subset_file_path, exclude_chars=EXCLUDE_CHARS),
            debug=debug,
        )

    # 5. 匿名化
    if anonymize:
        print("匿名化を実施しています...")
        target_font_obj = anonymize_info(font_obj=target_font_obj, font_name=base_type)

    # 6. 結果の出力
    suffix = f"_{base_type}_{condense_type}"
    print("フォントを出力しています...")

    save_font(
        font_obj=target_font_obj,
        input_path=str(target_path),
        output_path=output_font_path,
        suffix=suffix,
    )

    if output_font_path and output_font_info:
        # フォントと同じパスで拡張子だけ .txt に変えたものを作成
        info_output_path = Path(output_font_path).with_suffix(".txt")

        save_text(
            content=str(get_info(target_font_obj)),
            input_path=str(target_path),
            output_path=str(info_output_path),  # 保存先を明示
            suffix="",  # 既にパスに含まれているので空
        )
    else:
        # CLIから直接実行された場合などのフォールバック
        if output_font_info:
            save_text(
                content=str(get_info(target_font_obj)),
                input_path=str(target_path),
                suffix=suffix,
            )

    print("処理が完了しました！")


def main():
    """CLI用の受付窓口"""
    parser = argparse.ArgumentParser(
        description="渡されたフォントをスカイリムのUI向けに最適化します。"
    )
    parser.add_argument(
        "input", type=str, help="最適化したいフォントの入力元ファイルパス"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="", help="出力先ファイルパス"
    )
    parser.add_argument(
        "--base", choices=list(SKYRIM_BASE_FONT_CONFIGS.keys()), default="everywhere"
    )
    parser.add_argument("--subset", type=str, default="", help="サブセットファイルパス")
    parser.add_argument(
        "--condense", choices=list(CONDENSE_RATIO_CONFIGS.keys()), default="normal"
    )
    parser.add_argument("--monospace", action="store_true", help="等幅モード")
    parser.add_argument("--offset_height", type=int, default=0, help="上下位置調整")
    parser.add_argument("--anonymize", action="store_true", help="匿名化")
    parser.add_argument("--debug", action="store_true", help="デバッグモード")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    convert(
        target_font_path=args.input,
        output_font_path=args.output,
        subset_file_path=args.subset,
        base_type=args.base,
        condense_type=args.condense,
        mode_monospace=args.monospace,
        offset_height=args.offset_height,
        anonymize=args.anonymize,
        debug=args.debug,
    )


if __name__ == "__main__":
    main()
