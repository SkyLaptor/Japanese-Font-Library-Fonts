import argparse
import os
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from utils import load_text
from utils.font_tools import (
    ASCENT,
    DESCENT,
    UPM,
)
from utils.inspector import get_average_size, get_info
from utils.modifier import set_metrics, transform_glyphs
from utils.optimizer import remove_empty_glyphs
from utils.reconstructor import create_subset

BASE_FONT_EVERY = "every"
BASE_FONT_BOOK = "book"
BASE_FONT_HAND = "hand"
MODE_COND_NORM = "norm"
MODE_COND_COND = "cond"
MODE_COND_SKIN = "skin"
BASE_FONT_FILE_EVERY = "./assets/fonts/skyrim/skyrim_jp_every.ttf"
BASE_FONT_FILE_BOOK = "./assets/fonts/skyrim/skyrim_jp_book.ttf"
BASE_FONT_FILE_HAND = "./assets/fonts/skyrim/skyrim_jp_hand.ttf"
TARGET_RATIO_COND = 0.64  # バニラの英字フォント(Futura Condensed)と比較検討し決定
TARGET_RATIO_SKIN = 0.42  # 視認性の限界まで詰めた値
SHIFT_HEIGHT_EVERY = -96
SHIFT_HEIGHT_BOOK = 0
SHIFT_HEIGHT_HAND = 0


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
        choices=[
            BASE_FONT_EVERY,
            BASE_FONT_BOOK,
            BASE_FONT_HAND,
        ],
        type=str,
        default=BASE_FONT_EVERY,
        help=f"基準とするフォントの種類です。{BASE_FONT_EVERY}で一般的なUI（字幕・メニュー等）、{BASE_FONT_BOOK}で本UI、{BASE_FONT_HAND}で手書きUI（メモ・手紙等）を基準とします。 デフォルト:{BASE_FONT_EVERY}",
    )
    parser.add_argument(
        "--subset",
        type=str,
        default="",
        help="サブセット文字ファイルへのファイルパスです。渡さなかった場合はサブセットを行いません。文字コードはUTF-8にして下さい。",
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
        help=f"長体タイプ設定です。{MODE_COND_NORM}で変更なし、{MODE_COND_COND}で少し細長く、{MODE_COND_SKIN}でかなり細長くなります。 デフォルト: {MODE_COND_NORM}",
    )
    parser.add_argument(
        "--mono",
        action="store_true",
        help="等幅フォントなど、幅を変えたくない場合に有効化して下さい。有効の場合、長体タイプ設定は無視されます。",
    )
    parser.add_argument(
        "--shift_height",
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
        cond_type=args.cond,
        mode_mono=args.mono,
        shift_height=args.shift_height,
        anonymize=args.anonymize,
    )


# shift_heightはNoneにしておかないと定数適用が出来ないので注意
def convert(
    target_font_path: str,
    output_font_path: str,
    subset_file_path: str,
    base_type: str = BASE_FONT_EVERY,
    cond_type: str = MODE_COND_NORM,
    mode_mono: bool = False,
    shift_height: int = None,
    anonymize: bool = False,
):

    if not target_font_path or not os.path.exists(target_font_path):
        raise FileNotFoundError(
            f"入力されたファイルが正しくありません。: {target_font_path}"
        )

    # TODO: doc
    vanilla_font_path = None
    if base_type == BASE_FONT_EVERY:
        # バニラのEverywhereフォントを基準にします
        vanilla_font_path = BASE_FONT_FILE_EVERY
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_EVERY
    elif base_type == BASE_FONT_BOOK:
        # バニラのBookフォントを基準にします
        vanilla_font_path = BASE_FONT_FILE_BOOK
        if shift_height is None:
            shift_height = SHIFT_HEIGHT_BOOK
    elif base_type == BASE_FONT_HAND:
        # バニラのHandwriteフォントを基準にします
        vanilla_font_path = BASE_FONT_FILE_HAND
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
    vanilla_result = get_average_size(vanilla_font_obj, UPM)
    target_result = get_average_size(target_font_obj, UPM)
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
    if cond_type == MODE_COND_COND:
        scale_width = (
            vanilla_result.avg_bbox_size_norm_w * TARGET_RATIO_COND / scale_width
        )
    elif cond_type == MODE_COND_SKIN:
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
    if mode_mono:
        scale_width = 1.0

    print("=== 処理実行前の各種パラメーター表示")
    print(f"* 基準とするバニラの対象UI: {base_type}")
    print(f"* 使用するバニラフォントのパス: {vanilla_font_path}")
    if subset_file_path != "":
        print(f"* 使用するサブセットファイル: {subset_file_path}")
    else:
        print("* サブセットは行いません")
    print(f"* 横方向の拡大縮小率: x{scale_width:.3f} (長形モード: {cond_type})")
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
    cleanup_result = remove_empty_glyphs(target_font_obj)
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
        subset_result = create_subset(target_font_obj, load_text(subset_file_path))
        if len(subset_result.non_existed_glyphs) > 0:
            non_existed_glyphs_path = (
                Path("build") / f"{Path(target_font_path).stem}_nonexisted_glyphs.txt"
            )
            non_existed_glyphs_path.write_text(
                subset_result.non_existed_glyphs, encoding="utf-8"
            )
            print(
                f"警告: サブセット文字列と比較したところ、欠落している文字を {len(subset_result.non_existed_glyphs)}個 発見しました。"
            )
            print(f"対象の文字は {non_existed_glyphs_path} に出力しています。")
        else:
            print("サブセット文字列と比較したところ、文字の欠落はありませんでした。")
        target_font_obj = subset_result.font_obj
        # print("DEBUG:現時点でのフォント情報")
        # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
        # print(
        #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
        # )
        # print(report_font_info(target_font_obj))

    # メトリクス調整
    print("=== メトリクス調整の実施")
    target_font_obj = set_metrics(target_font_obj, ASCENT, DESCENT)
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # サイズ調整・縦方向調整
    print("=== サイズおよび縦方向調整の実施")
    target_font_obj = transform_glyphs(
        target_font_obj, scale_width, scale_height, shift_height
    )
    # print("DEBUG:現時点でのフォント情報")
    # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
    # print(
    #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
    # )
    # print(report_font_info(target_font_obj))

    # 匿名化
    if anonymize:
        print("=== 匿名化の実施")
        target_font_obj = anonymize(target_font_obj)
        # print("DEBUG:現時点でのフォント情報")
        # debug_result = get_metrics_average(target_font_obj, BASE_UPM)
        # print(
        #     f"DEBUG: 対象フォント現在のサイズ平均値(UPM={BASE_UPM}の場合): 横幅:{debug_result.avg_bbox_size_norm_w:.1f} 縦幅:{debug_result.avg_bbox_size_norm_h:.1f}"
        # )
        # print(report_font_info(target_font_obj))

    # TODO: ヒンティング情報消さなくていいの？

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
    report = get_info(target_font_obj)
    report_path = Path("build") / f"{Path(target_font_path).stem}_report.txt"
    report_path.write_text(report, encoding="utf-8")

    print("=== 処理完了")
    print(f"* フォント出力先: {output_font_path}")
    print(f"* レポート出力先: {report_path}")
    return output_font_path


if __name__ == "__main__":
    main()
