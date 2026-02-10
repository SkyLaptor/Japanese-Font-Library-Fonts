import argparse
import os
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from utils.font_tools import (
    ASCENT,
    BASE＿UPM,
    DESCENT,
    adjust_font_metrics,
    anonymize_font_info,
    clean_empty_glyphs,
    create_subset,
    get_metrics_average,
    load_subset_text,
    report_font_info,
    resize_glyphs,
)

MODE_SIZE_EVERY = "every"
MODE_SIZE_BOOK = "book"
MODE_SIZE_HAND = "hand"
MODE_COND_NORM = "norm"
MODE_COND_COND = "cond"
MODE_COND_SKIN = "skin"
BASE_FONT_EVERY = "./assets/fonts/skyrim/skyrim_jp_every.ttf"
BASE_FONT_BOOK = "./assets/fonts/skyrim/skyrim_jp_book.ttf"
BASE_FONT_HAND = "./assets/fonts/skyrim/skyrim_jp_hand.ttf"
TARGET_RATIO_COND = 0.64  # バニラの英字フォント(Futura Condensed)と比較検討し決定
TARGET_RATIO_SKIN = 0.42  # 視認性の限界まで詰めた値
SHIFT_HEIGHT_EVERY = -96
SHIFT_HEIGHT_BOOK = 0
SHIFT_HEIGHT_HAND = 0


# shift_heightはNoneにしておかないと定数適用が出来ないので注意
def main(
    target_font_path: str,
    output_font_path: str,
    subset_file_path: str,
    mode_size: str = MODE_SIZE_EVERY,
    mode_cond: str = MODE_COND_NORM,
    mode_mono: int = 0,
    shift_height: int = None,
):

    if not target_font_path or not os.path.exists(target_font_path):
        raise FileNotFoundError(
            f"入力されたファイルが正しくありません。: {target_font_path}"
        )

    # TODO: doc
    vanilla_font_path = None
    if mode_size == MODE_SIZE_EVERY:
        # バニラのEverywhereフォントを基準にします
        vanilla_font_path = BASE_FONT_EVERY
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_EVERY
    elif mode_size == MODE_SIZE_BOOK:
        # バニラのBookフォントを基準にします
        vanilla_font_path = BASE_FONT_BOOK
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_BOOK
    elif mode_size == MODE_SIZE_HAND:
        # バニラのHandwriteフォントを基準にします
        vanilla_font_path = BASE_FONT_HAND
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_HAND

    if not vanilla_font_path or not os.path.exists(vanilla_font_path):
        raise FileNotFoundError(
            f"バニラのフォントファイルが見当たりません。: {vanilla_font_path}"
        )

    if subset_file_path != "" and not os.path.exists(subset_file_path):
        raise FileNotFoundError(
            f"サブセットファイルが見当たりません。: {subset_file_path}"
        )

    # フォントを開く
    vanilla_font_obj = TTFont(vanilla_font_path)
    target_font_obj = TTFont(target_font_path)

    # バニラのフォントの大きさとカスタムフォントの大きさを比較し、拡大縮小率を算出します。
    # この際にUPMはBASE_UPMを基準としますので、あとから忘れずにスケーリングすること。
    vanilla_result = get_metrics_average(vanilla_font_obj, BASE_UPM)
    target_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: バニラフォントのサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{vanilla_result.avg_bbox_size_norm_w:.1f} 縦幅:{vanilla_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(
    #     f"DEBUG: 対象フォントのサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{target_result.avg_bbox_size_norm_w:.1f} 縦幅:{target_result.avg_bbox_size_norm_h:.1f}"
    # )
    scale_height = (
        vanilla_result.avg_bbox_size_norm_h / target_result.avg_bbox_size_norm_h
    )
    scale_width = target_result.avg_bbox_size_norm_w * scale_height
    # 長形モードの場合はそれらも考慮します。
    if mode_cond == MODE_COND_COND:
        scale_width = (
            vanilla_result.avg_bbox_size_norm_w * TARGET_RATIO_COND / scale_width
        )
    elif mode_cond == MODE_COND_SKIN:
        scale_width = (
            vanilla_result.avg_bbox_size_norm_w * TARGET_RATIO_SKIN / scale_width
        )
    else:
        scale_width = vanilla_result.avg_bbox_size_norm_w / scale_width

    # 横方向の拡大率は、縦方向の拡大率も考慮する。
    scale_width = scale_height * scale_width

    # 計算の結果、横幅が意図せず拡大されてしまうのを防ぎます。
    if scale_width > 1.0:
        scale_width = 1.0

    # 等幅モードが有効の時には幅変更は強制的にオフにします。
    if mode_mono > 0:
        scale_width = 1.0

    print("=== 処理実行前の各種パラメーター表示")
    print(f"* 基準とするバニラの対象UI: {mode_size}")
    print(f"* 使用するバニラフォントのパス: {vanilla_font_path}")
    if subset_file_path != "":
        print(f"* 使用するサブセットファイル: {subset_file_path}")
    else:
        print("* サブセットは行いません")
    print(f"* 横方向の拡大縮小率: x{scale_width:.3f} (長形モード: {mode_cond})")
    print(f"* 縦方向の拡大縮小率: x{scale_height:.3f}")
    print(f"* 縦方向の移動量: {shift_height}")

    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # 意図しない空白グリフを削除
    print("=== 意図しない空白グリフのクリーンアップ実施")
    cleanup_result = clean_empty_glyphs(target_font_obj)
    target_font_obj = cleanup_result.font_obj
    if len(cleanup_result.removed_glyphs) > 0:
        print(
            f"意図しない空白グリフが {len(cleanup_result.removed_glyphs)}個 ありました。"
        )
    else:
        print("意図しない空白グリフはありませんでした。")
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # サブセット化
    if subset_file_path != "":
        print("=== サブセット実施")
        subset_result = create_subset(
            target_font_obj, load_subset_text(subset_file_path)
        )
        if len(subset_result.non_existed_glyphs) > 0:
            non_existed_glyphs_path = (
                Path("build") / f"{Path(target_font_path).stem}_nonexisted_glyphs.txt"
            )
            non_existed_glyphs_path.write_text(
                subset_result.non_existed_glyphs, encoding="utf-8"
            )
            print(
                f"警告: サブセットと比較したところ、欠落している文字を発見したため {non_existed_glyphs_path} に対象の文字を出力しました。"
            )
        else:
            print("サブセットと比較したところ、文字の欠落はありませんでした。")
        target_font_obj = subset_result.font_obj
        # print("DEBUG:現時点でのフォント情報")
        # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
        # print(
        #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
        # )
        # print(report_font_info(target_font_obj))

    # メトリクス調整
    print("=== メトリクス調整の実施")
    target_font_obj = adjust_font_metrics(target_font_obj, ASCENT, DESCENT)
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # サイズ調整・縦方向調整
    print("=== サイズおよび縦方向調整の実施")
    target_font_obj = resize_glyphs(
        target_font_obj, scale_width, scale_height, shift_height
    )
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # 匿名化
    print("=== 匿名化の実施")
    target_font_obj = anonymize_font_info(target_font_obj)
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # 最適化が完了したTTFを出力
    print("=== 最適化済みフォントの出力")
    if not output_font_path:
        base_dir = "build"
        os.makedirs(base_dir, exist_ok=True)
        file_name = os.path.basename(target_font_path)
        name_without_ext = os.path.splitext(file_name)[0]
        output_font_path = os.path.join(base_dir, f"{name_without_ext}_optimized.ttf")
    target_font_obj.save(output_font_path)

    # 最終のフォント情報レポートを出力
    print("=== フォント情報レポートを出力")
    report = report_font_info(target_font_obj)
    report_path = Path("build") / f"{Path(target_font_path).stem}_report.txt"
    report_path.write_text(report, encoding="utf-8")

    print("=== 処理完了")
    print(f"* フォント出力先: {output_font_path}")
    print(f"* レポート出力先: {report_path}")
    return output_font_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="スカイリムのUI向けに入力されたフォントを最適化します。"
    )

    parser.add_argument(
        "input",
        type=str,
        help="最適化したいフォントの入力元ファイルパス",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="最適化したフォントの出力先ファイルパス",
    )
    parser.add_argument(
        "-s", "--subset", type=str, default="", help="サブセットのファイルパス"
    )
    parser.add_argument(
        "--size",
        choices=[
            MODE_SIZE_EVERY,
            MODE_SIZE_BOOK,
            MODE_SIZE_HAND,
        ],
        type=str,
        default=MODE_SIZE_EVERY,
        help=f"基準とするUIのサイズ デフォルト:{MODE_SIZE_EVERY}",
    )
    parser.add_argument(
        "--cond",
        choices=[
            MODE_COND_NORM,
            MODE_COND_COND,
            MODE_COND_SKIN,
        ],
        type=str,
        default=MODE_COND_NORM,
        help=f"長形プリセット デフォルト: {MODE_COND_NORM}",
    )
    parser.add_argument(
        "--mono",
        type=int,
        default=0,
        help="等幅フォント用モード(1で有効化) デフォルト: 0(無効)",
    )
    parser.add_argument(
        "--shift_height",
        type=int,
        default=None,
        help="上下の位置調整",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    main(
        target_font_path=args.input,
        output_font_path=args.output,
        subset_file_path=args.subset,
        mode_size=args.size,
        mode_cond=args.cond,
        mode_mono=args.mono,
        shift_height=args.shift_height,
    )
