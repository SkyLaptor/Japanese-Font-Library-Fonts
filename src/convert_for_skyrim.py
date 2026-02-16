import argparse
import os
import sys

from fontTools.ttLib import TTFont

from utils.common import dprint, load_text, save_font, save_text
from utils.inspector import get_average_size, get_glyphs, get_info
from utils.modifier import anonymize_info, harmonize_font_metrics
from utils.optimizer import create_subset, remove_empty_glyphs

BASE_FONT_CONFIGS = {
    "everywhere": "data/basefonts/everywhere.ttf",
    "book": "data/basefonts/book.ttf",
    "handwrite": "data/basefonts/handwrite.ttf",
}

CONDENSE_RATIO_CONFIGS = {
    "normal": 1.0,  # 標準
    "condense": 0.64,  # バニラのFutura Condensed相当
    "skinny": 0.48,  # 視認性の限界
}


def main():
    parser = argparse.ArgumentParser(
        description="渡されたフォントをスカイリムのUI向けに最適化します。"
    )

    parser.add_argument(
        "input",
        type=str,
        help="最適化したいフォントの入力元ファイルパス指定です。",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="最適化したフォントの出力先ファイルパス指定です。渡さなかった場合はbuildディレクトリに出力します。",
    )
    parser.add_argument(
        "--base",
        choices=list(BASE_FONT_CONFIGS.keys()),
        type=str,
        default="everywhere",
        help="基準とするバニラフォントを選択します。対応モード: "
        + ", ".join(BASE_FONT_CONFIGS.keys())
        + " デフォルト: everywhere",
    )
    parser.add_argument(
        "--subset",
        type=str,
        default="",
        help="サブセット文字ファイルへのファイルパスです。渡さなかった場合はサブセットを行いません。文字コードはUTF-8にして下さい。",
    )
    parser.add_argument(
        "--condense",
        choices=list(CONDENSE_RATIO_CONFIGS.keys()),
        type=str,
        default="normal",
        help="長体タイプを選択します。対応モード: "
        + ", ".join(CONDENSE_RATIO_CONFIGS.keys())
        + " デフォルト: normal",
    )
    parser.add_argument(
        "--monospace",
        action="store_true",
        help="等幅フォントなど、幅を変えたくない場合に有効化して下さい。有効の場合、長体タイプ設定は無視されます。",
    )
    parser.add_argument(
        "--offset_height",
        type=int,
        default=0,
        help="上下の位置調整の値です。正の値で上方向へ、負の値で下方向へ移動します。 デフォルト: 0",
    )
    parser.add_argument(
        "--anonymize",
        action="store_true",
        help="匿名化を行いたい場合に有効化して下さい。",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモード",
    )

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


def convert(
    target_font_path: str,
    output_font_path: str,
    subset_file_path: str,
    base_type: str,
    condense_type: str,
    offset_height: int,
    mode_monospace: bool = False,
    anonymize: bool = False,
    debug: bool = False,
):
    # TODO: doc
    if not target_font_path or not os.path.exists(target_font_path):
        raise FileNotFoundError(
            f"フォントファイルが見当たりません。: {target_font_path}"
        )

    base_font_path = BASE_FONT_CONFIGS.get(base_type)

    if not base_font_path or not os.path.exists(base_font_path):
        raise FileNotFoundError(
            f"ベースフォントファイルが見つかりません。: {base_font_path}"
        )

    if subset_file_path != "" and not os.path.exists(subset_file_path):
        raise FileNotFoundError(
            f"サブセットファイルが見つかりません。: {subset_file_path}"
        )

    # 基準用のフォントと処理対象のフォントを開く
    base_font_obj = TTFont(base_font_path)
    target_font_obj = TTFont(target_font_path)
    # dprint("ベースフォント情報", debug)
    # dprint(get_info(font_obj=base_font_obj, debug=debug))
    # dprint("処理対象フォント情報", debug)
    # dprint(get_info(font_obj=target_font_obj, debug=debug))

    # 空白グリフ（正規の空白は除く）を消去
    print("空白グリフを消去しています...")
    dprint(
        f"消去前のグリフ数(Unicode割当済): {len(get_glyphs(font_obj=target_font_obj, debug=debug))}",
        debug,
    )
    target_font_obj = remove_empty_glyphs(font_obj=target_font_obj, debug=debug)
    dprint(
        f"消去後のグリフ数(Unicode割当済): {len(get_glyphs(font_obj=target_font_obj, debug=debug))}",
        debug,
    )

    # グリフを変形する
    # 可能な限りサブセット前に行う（負荷は上がるが、サブセット後だと平均値算出に使用可能な文字が減り、精度が下がるため。）
    # 横幅倍率の決定
    scale_width = 1.0
    if not mode_monospace:
        scale_width = CONDENSE_RATIO_CONFIGS.get(condense_type)
        dprint(f"カスタム横幅拡大率: x{scale_width} 長体モード: {condense_type}", debug)
    else:
        dprint("等幅モードのため横幅拡大率は無効", debug)
    print("グリフを変形しています...")
    dprint("ベースフォント", debug)
    dprint(get_average_size(font_obj=base_font_obj), debug)
    dprint("変更前の処理対象フォント", debug)
    dprint(get_average_size(font_obj=target_font_obj), debug)
    result = harmonize_font_metrics(
        src_font_obj=target_font_obj,
        base_font_obj=base_font_obj,
        scale_width_manual=scale_width,
        scale_height_manual=1.0,
        offset_width=0,
        offset_height=offset_height,
    )
    target_font_obj = result.font_obj
    dprint(f"UPMを変更したか: {result.is_upm_change}", debug)
    dprint(
        f"最終的な拡大縮小率: 横:x{result.final_scale_width:.3f}, 縦:x{result.final_scale_height:.3f}",
        debug,
    )
    dprint("変更後の処理対象フォント", debug)
    dprint(get_average_size(font_obj=target_font_obj), debug)

    # サブセットファイルが渡された場合にサブセットを作成
    if subset_file_path != "":
        print(
            f"サブセットを作成しています...: 使用サブセットテキスト: {subset_file_path}"
        )
        dprint(f"サブセットテキストの文字数: {len(load_text(subset_file_path))}", debug)
        dprint(
            f"サブセット前のグリフ数(Unicode割当済): {len(get_glyphs(font_obj=target_font_obj))}",
            debug,
        )
        target_font_obj = create_subset(
            font_obj=target_font_obj,
            subset_text=load_text(subset_file_path),
            debug=debug,
        )
        dprint(
            f"サブセット後のグリフ数(Unicode割当済): {len(get_glyphs(font_obj=target_font_obj, debug=debug))}",
            debug,
        )

    # 匿名化を行う
    if anonymize:
        print("匿名化を実施しています...")
        dprint("匿名化前の対象フォント", debug)
        dprint(get_info(font_obj=target_font_obj, debug=debug), debug)
        target_font_obj = anonymize_info(
            font_obj=target_font_obj, family_name=base_type
        )
        dprint("匿名化後の対象フォント", debug)
        dprint(get_info(font_obj=target_font_obj, debug=debug), debug)

    # 結果を出力する
    print("フォントを出力しています...")
    save_font(
        font_obj=target_font_obj,
        input=target_font_path,
        output=output_font_path,
        suffix=f"_{base_type}_{condense_type}",
    )
    print("フォント情報を出力しています...")
    save_text(
        text=str(get_info(target_font_obj)),
        input=target_font_path,
        suffix=f"_{base_type}_{condense_type}",
    )

    print("処理が完了しました！")


if __name__ == "__main__":
    main()
