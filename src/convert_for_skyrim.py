import argparse
import os
import sys

from fontTools.ttLib import TTFont

from utils import ASCENT, DESCENT, UPM, load_text, save_font, save_text
from utils.inspector import get_average_size, get_info
from utils.modifier import anonymize_info, set_metrics, transform_glyphs
from utils.optimizer import remove_empty_glyphs
from utils.reconstructor import create_subset

BASE_FONT_CONFIGS = {
    "everywhere": {
        "file": "./data/skyrim/1_Skyrim_JP_EveryFont_0805_empty_removed.ttf",
    },
    "book": {
        "file": "./data/skyrim/22_Skyrim_JP_BookFont_0805_empty_removed.ttf",
    },
    "handwritten": {
        "file": "./data/skyrim/5_Skyrim_JP_HandWriteFont_0805_empty_removed.ttf",
    },
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
        + ", ".join(BASE_FONT_CONFIGS.keys()),
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
        + ", ".join(CONDENSE_RATIO_CONFIGS.keys()),
    )
    parser.add_argument(
        "--monospace",
        action="store_true",
        help="等幅フォントなど、幅を変えたくない場合に有効化して下さい。有効の場合、長体タイプ設定は無視されます。",
    )
    parser.add_argument(
        "--height_offset",
        type=int,
        default=None,
        help="上下の位置調整の値です。正の値で上方向へ、負の値で下方向へ移動します。設定しない場合は推奨値が自動適用されます。",
    )
    parser.add_argument(
        "--anonymize",
        action="store_true",
        help="匿名化を行いたい場合に有効化して下さい。",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    convert(
        target_font_path=args.input,
        output_font_path=args.output,
        base_type=args.base,
        subset_file_path=args.subset,
        condense_type=args.condense,
        mode_monospace=args.monospace,
        height_offset=args.height_offset,
        anonymize=args.anonymize,
    )


# height_offsetはNoneにしておかないと定数適用が出来ないので注意
def convert(
    target_font_path: str,
    output_font_path: str,
    subset_file_path: str,
    base_type: str = "everywhere",
    condense_type: str = "normal",
    mode_monospace: bool = False,
    height_offset: int = None,
    anonymize: bool = False,
):
    """
    # スカイリム向けにフォントを変換する
    """
    if not target_font_path or not os.path.exists(target_font_path):
        raise FileNotFoundError(
            f"フォントファイルが見当たりません。: {target_font_path}"
        )

    base_font_path = None
    base_font_config = BASE_FONT_CONFIGS.get(base_type)

    if base_font_config:
        base_font_path = base_font_config['file']
        # 引数で個別に指定がない場合のみ、マップのデフォルト値（-96等）を適用
        if height_offset is None:
            height_offset = base_font_config['height_offset']
    else:
        # 想定外のbase_typeが来た場合の安全策
        raise ValueError(f"不正なベースタイプです。: {base_type}")

    if not base_font_path or not os.path.exists(base_font_path):
        raise FileNotFoundError(
            f"比較用のベースフォントファイルが見当たりません。: {base_font_path}"
        )

    if subset_file_path != "" and not os.path.exists(subset_file_path):
        raise FileNotFoundError(
            f"サブセットファイルが見当たりません。: {subset_file_path}"
        )

    # 基準用のフォントと処理対象のフォントを開く
    base_font_obj = TTFont(base_font_path)
    target_font_obj = TTFont(target_font_path)

    # 空白グリフ（正規の空白は除く）を消去
    print("空白グリフを消去しています...")
    remove_empty_result = remove_empty_glyphs(target_font_obj)
    removed_glyphs_count = len(remove_empty_result.removed_glyphs)
    if removed_glyphs_count > 0:
        print(f"空白グリフが {removed_glyphs_count}個 ありました。")
    else:
        print("空白グリフはありませんでした。")

    # サブセットファイルが渡された場合にサブセットを作成
    if subset_file_path != "":
        print(f"サブセットを作成しています...: {subset_file_path}")
        subset_result = create_subset(target_font_obj, load_text(subset_file_path))
        non_existed_glyphs_count = len(subset_result.non_existed_glyphs)
        if non_existed_glyphs_count > 0:
            print(f"サブセット欠落グリフが {non_existed_glyphs_count}個 ありました。")
            save_text(
                text=subset_result.non_existed_glyphs,
                input=target_font_path,
                suffix="_nonexisted_glyphs",
            )

    # 必要に応じてメトリクス情報（及び実グリフサイズ）を変更
    target_upm = get_info(target_font_obj).upm
    if target_upm != UPM:
        print(f"UPMを変更しています...: UPM: {UPM}")
        set_metrics_result = set_metrics(
            font_obj=target_font_obj, ascent=ASCENT, descent=DESCENT
        )
        need_scale_size = set_metrics_result.need_scale_size
        if need_scale_size != 1.0:
            print("UPM変更に合わせて実サイズを変更しています...")
            target_font_obj = transform_glyphs(
                font_obj=target_font_obj,
                scale_width=need_scale_size,
                scale_height=need_scale_size,
            )

    # 基準フォントとサイズを合わせる

    base_avg_result = get_average_size(base_font_obj)
    target_avg_result = get_average_size(target_font_obj)
    # いろいろな判定方式がありますが、一番UIへの影響が大きいと考えられる縦方向の大きさを基準とします。
    scale_ratio = base_avg_result.avg_h / target_avg_result.avg_h
    print(
        f"基準フォントとサイズを合わせています...: タイプ: {base_type} 倍率: x{scale_ratio:.3f}"
    )
    target_font_obj = transform_glyphs(
        font_obj=target_font_obj,
        scale_width=scale_ratio,
        scale_height=scale_ratio,
    )

    # 長体モードの変形を行う（等幅モードと排他）
    if not mode_monospace:
        condense_ratio = CONDENSE_RATIO_CONFIGS.get(condense_type)
        if condense_ratio != 1.0:
            print(
                f"指定された長体モードで変形しています...: モード: {condense_type} 横倍率: x{condense_ratio}"
            )
            target_font_obj = transform_glyphs(
                target_font_obj, scale_width=condense_ratio
            )
    else:
        print("等幅モードが設定されているため、横幅単体での変更は行いません。")

    # 上下位置をずらす
    if height_offset != 0:
        print(f"上下位置を調整しています...: 調整値: {height_offset}")
        target_font_obj = transform_glyphs(target_font_obj, height_offset=height_offset)

    # 匿名化を行う
    if anonymize:
        print("匿名化を実施しています...")
        target_font_obj = anonymize_info(target_font_obj)

    # デバッグ表示
    base_avg_result = get_average_size(base_font_obj)
    target_avg_result = get_average_size(target_font_obj)

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
