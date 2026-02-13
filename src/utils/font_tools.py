import argparse
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from utils import (
    generate_jisx0208,
    is_cff,
    is_ttf,
    load_text,
    merge_text_files,
    save_font,
    save_text,
)
from utils.inspector import get_average_size, get_glyphs, get_info
from utils.modifier import (
    anonymize_info,
    change_weight,
    set_metrics,
    transform_glyphs,
)
from utils.optimizer import remove_black_circles, remove_empty_glyphs
from utils.reconstructor import create_subset


def main():
    parser = argparse.ArgumentParser(
        description="フォントに対する様々な操作を行うためのツールボックスです。"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        default="get_info",
        help="実行する操作を指定します。デフォルト: get_info(フォント情報の表示および出力)",
    )
    parser.add_argument(
        "input",
        help="入力するファイルパス。フォントやフォントコレクションなどであり、actionにより用途は変化します。",
    )
    parser.add_argument(
        "--input2",
        help="入力するファイルパス2。フォントやフォントコレクションなどであり、actionにより用途は変化します。",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="出力先のファイルパス。フォントやテキストファイルなどであり、actionにより内容は変化します。",
    )
    parser.add_argument(
        "--output2",
        default="",
        help="出力先のファイルパス2。フォントやテキストファイルなどであり、actionにより内容は変化します。",
    )
    parser.add_argument("--subset", help="サブセットフォントファイルのパス")
    parser.add_argument(
        "--ascent",
        type=int,
        default=None,
        help="Ascentの値(units)。かならずDescentとペアで入力して下さい。通常は正の値となります。",
    )
    parser.add_argument(
        "--descent",
        type=int,
        default=None,
        help="Descentの値(units)。かならずAscentとペアで入力して下さい。通常は負の値となります。",
    )
    parser.add_argument(
        "--scale_width", type=float, default=1.0, help="横方向の拡大縮小率(1.0=100.0%%)"
    )
    parser.add_argument(
        "--scale_height",
        type=float,
        default=1.0,
        help="縦方向の拡大縮小率",
    )
    parser.add_argument(
        "--width_offset",
        type=int,
        default=0,
        help="文字の左右調整(units)。正の値で右方向、負の値で左方向に移動します。対象フォントのUPMに比例します。",
    )
    parser.add_argument(
        "--height_offset",
        type=int,
        default=0,
        help="文字の上下調整(units)。正の値で上方向、負の値で下方向に移動します。対象フォントのUPMに比例します。",
    )
    parser.add_argument(
        "--weight_offset",
        type=int,
        default=0,
        help="文字の太さ調整値(units)。正の値で太く、負の値で細くなります。対象フォントのUPMに比例します。",
    )
    parser.add_argument(
        "--no_otf2ttf",
        action="store_true",
        help="OTFをTTFに変換したくない場合に有効化して下さい。",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    try:
        dispatch_action(**vars(args))
    except Exception as e:
        print(f"エラーが発生しました: {e}", file=sys.stderr)


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def action_check_fonttype(input, **_):
    ext = Path(input).suffix.lower()
    font_obj = TTFont(input)
    if is_cff(font_obj):
        if ".otf" != ext:
            print(
                f"拡張子は{ext}ですが、フォントの形式はOTFです。拡張子が間違っています。"
            )
        else:
            print("フォントの形式はOTFです。(正常)")
    elif is_ttf(font_obj):
        if ".ttf" != ext:
            print(
                f"拡張子は{ext}ですが、フォントの形式はTTFです。拡張子が間違っています。"
            )
        else:
            print("フォントの形式はTTFです。(正常)")
    else:
        print(
            "フォントの形式が判別できませんでした。本スクリプトでは正常に動作しない可能性が高いです。"
        )


def action_get_info(input, output="", **_):
    print("フォント情報を取得します。")
    font_obj = TTFont(input)
    info = get_info(font_obj=font_obj)
    print(info)
    save_text(text=str(info), input=input, output=output, suffix="_info")


def action_get_glyphs(input, output, **_):
    print("フォントに含まれるグリフ一覧を取得します。")
    font_obj = TTFont(input)
    print("フォントから空白グリフ（実質的に含まれているとは言えない）を削除します。")
    result = remove_empty_glyphs(font_obj=font_obj)
    glyphs = get_glyphs(font_obj=result.font_obj)
    print(f"文字数: {len(glyphs)}")
    save_text(text=glyphs, input=input, output=output, suffix="_glyphs")


def action_get_average_size(input, output, **_):
    print("フォントに含まれるグリフのサイズ平均値を取得します。")
    font_obj = TTFont(input)
    result = get_average_size(font_obj=font_obj)
    print(result)
    save_text(text=str(result), input=input, output=output, suffix="_avg_result")


def action_set_metrics(input, output, ascent, descent, no_otf2ttf, **_):
    print("フォントのメトリクスを設定します。")
    font_obj = TTFont(input)
    result = set_metrics(font_obj=font_obj, ascent=ascent, descent=descent)
    if result.old_upm != result.new_upm:
        print(
            f"UPMが{result.old_upm}から{result.new_upm}に変更されました。{result.need_scale_size:.3f}倍のスケール変更を実施します。"
        )
        font_obj = transform_glyphs(
            font_obj=result.font_obj,
            scale_width=result.need_scale_size,
            scale_height=result.need_scale_size,
        )
    save_font(
        font_obj=font_obj,
        input=input,
        output=output,
        suffix="_metrics_set",
        otf2ttf=not no_otf2ttf,
    )


def action_transform_glyphs(
    input,
    output,
    scale_width,
    scale_height,
    width_offset,
    height_offset,
    no_otf2ttf,
    **_,
):
    print("フォントを変形します。")
    font_obj = TTFont(input)
    font_obj = transform_glyphs(
        font_obj=font_obj,
        scale_width=scale_width,
        scale_height=scale_height,
        width_offset=width_offset,
        height_offset=height_offset,
    )
    save_font(
        font_obj=font_obj,
        input=input,
        output=output,
        suffix="_transformed",
        otf2ttf=not no_otf2ttf,
    )


def action_anonymize_info(input, output, no_otf2ttf, **_):
    print("フォントを匿名化します。")
    font_obj = TTFont(input)
    print("匿名化前の情報を表示します。")
    before_info = get_info(font_obj=font_obj)
    print(before_info)
    font_obj = anonymize_info(font_obj=font_obj)
    print("匿名化後の情報を表示します。")
    after_info = get_info(font_obj=font_obj)
    print(after_info)
    save_font(
        font_obj=font_obj,
        input=input,
        output=output,
        suffix="_anonymized",
        otf2ttf=not no_otf2ttf,
    )


def action_change_weight(input, output, weight_offset, no_otf2ttf, **_):
    print("フォントの太さを変更します。")
    font_obj = TTFont(input)
    font_obj = change_weight(font_obj=font_obj, offset_weight=weight_offset)
    save_font(
        font_obj=font_obj,
        input=input,
        output=output,
        suffix="_weight_changed",
        otf2ttf=not no_otf2ttf,
    )


def action_remove_empty_glyphs(input, output, no_otf2ttf, **_):
    print("フォントから空白グリフを消去します。")
    font_obj = TTFont(input)
    print(f"消去前のグリフ数は {get_info(font_obj=font_obj).glyph_count_uni} です。")
    result = remove_empty_glyphs(font_obj=font_obj)
    print(
        f"消去後のグリフ数は {get_info(font_obj=result.font_obj).glyph_count_uni} です。"
    )
    print(result)
    save_font(
        font_obj=result.font_obj,
        input=input,
        output=output,
        suffix="_empty_removed",
        otf2ttf=not no_otf2ttf,
    )


def action_create_subset(input, output, output2, subset, no_otf2ttf, **_):
    print("フォントからサブセットを作成します。")
    font_obj = TTFont(input)
    subset_chars = load_text(subset)
    print(
        f"サブセット元フォントのグリフ数は {get_info(font_obj=font_obj).glyph_count_uni} です。"
    )
    print(f"サブセットテキストの文字数は {len(subset_chars)} です。")
    result = create_subset(font_obj=font_obj, subset_chars=subset_chars)
    print(
        f"サブセットフォントのグリフ数は {get_info(font_obj=result.font_obj).glyph_count_uni} です。"
    )
    save_font(
        font_obj=result.font_obj,
        input=input,
        output=output,
        suffix="_subsetted",
        otf2ttf=not no_otf2ttf,
    )
    if len(result.non_existed_glyphs) > 0:
        print(
            f"サブセット元フォントから欠落しているグリフが {len(result.non_existed_glyphs)} 個ありました。"
        )
        save_text(
            text=result.non_existed_glyphs,
            input=input,
            output=output2,
            suffix="_non_existed_glyphs",
        )
    else:
        print("サブセット元フォントから欠落しているグリフはありませんでした。")


# TODO: 結合うまくいってない
def action_merge_fonts(
    input, input2, output, output2, ascent, descent, weight_offset, no_otf2ttf, **_
):
    print(
        "フォント同士を結合し新しいフォントを作成します。フォントA（input側）がベースとなります。"
    )
    print(
        "注: 現在結合が正常に動作していないため、fontforgeでの統合向けに出力するようにしています。"
    )
    font_obj_a = TTFont(input)
    font_obj_b = TTFont(input2)
    print(f"結合前の事前処理を行います: {input}, {input2}")
    print("フォントBは、事前にフォントAの太さにそろえておいて下さい。")
    # フォントAの太さにフォントBの太さをそろえる
    #  自動化が難しいため、事前にウェイト変更機能でいろいろ試して値を決定すること。
    # print("フォントB側のウェイトをフォントAに合わせて調整します。")
    # if weight_offset != 0:
    #     weight_offset_font_b = change_weight(
    #         font_obj=font_obj_b, weight_offset=weight_offset
    #     )
    # transform_glyphsに組み込むのが難しいため、事前に太さ調整しておいたものを使用すること。
    print("空白グリフの削除")
    result_a = remove_empty_glyphs(font_obj=font_obj_a)
    result_b = remove_empty_glyphs(font_obj=font_obj_b)
    print("メトリクスの調整")
    setmet_a = set_metrics(font_obj=result_a.font_obj, ascent=ascent, descent=descent)
    setmet_b = set_metrics(font_obj=result_b.font_obj, ascent=ascent, descent=descent)
    print(
        f"メトリクス調整により、フォントAは元フォントから x{setmet_a.need_scale_size:.3f} に変更する必要があります。"
    )
    print(
        f"メトリクス調整により、フォントBは元フォントから x{setmet_b.need_scale_size:.3f} に変更する必要があります。"
    )
    print("メトリクス変更、フォントAにフォントBのサイズを合わせるように実サイズ調整")
    font_obj_b_trans = setmet_b.font_obj
    # サイズ変更はtransform_glyphsの仕様により、一括で行う必要があるため、事前に計算する。
    # ひとまずUPM変更による拡大縮小率を取得
    scale_size_a = setmet_a.need_scale_size
    scale_size_b = setmet_b.need_scale_size
    # グリフサイズを取得し、フォントAにフォントBを合わせるための倍率を計算する。
    #  setmet_X.font_obj の中身はメトリクスの調整を通したあとなので、**ノーマライズ**された値が入っている。
    #  もしメトリクス調整をとおしていなければ生の平均値が出てズレが生じるので注意
    #  結果のUPMの値がそろっていればOK（＝ノーマライズされているということ）
    avg_result_a = get_average_size(font_obj=setmet_a.font_obj)
    print("フォントA")
    print(avg_result_a)
    avg_result_b = get_average_size(font_obj=setmet_b.font_obj)
    print("フォントB")
    print(avg_result_b)
    # フォントA: メトリクス調整分のみでOK
    scale_h_a = setmet_a.need_scale_size
    # フォントB: メトリクスノーマライズ＋サイズ調整はフォントAの縦方向の値を基準とする方式でいく。
    # フォントBをフォントAの平均サイズに一致させるためのベース倍率
    # (純粋なフォント間の体格差を埋める)
    base_ratio_b_to_a = avg_result_a.avg_h / avg_result_b.avg_h
    print(
        f"メトリクスノーマライズしたフォントBはメトリクスノーマライズしたフォントAと比較して x{base_ratio_b_to_a:.3f} に変更する必要があります。"
    )
    # フォントBをAのサイズに合わせた後、フォントAに適用するのと同じ「枠への収まり調整」をかける
    scale_h_b = base_ratio_b_to_a * scale_h_a

    print(f"最終的にフォントAは元フォントから x{scale_h_a:.3f} に変更します。")
    print(f"最終的にフォントBは元フォントから x{scale_h_b:.3f} に変更します。")

    font_obj_a_trans = setmet_a.font_obj
    if scale_h_a != 1.0:
        font_obj_a_trans = transform_glyphs(
            font_obj=setmet_a.font_obj,
            scale_width=scale_h_a,
            scale_height=scale_h_a,
        )
    font_obj_b_trans = setmet_b.font_obj
    if scale_h_b != 1.0:
        font_obj_b_trans = transform_glyphs(
            font_obj=setmet_b.font_obj,
            scale_width=scale_h_b,
            scale_height=scale_h_b,
        )
    print(get_info(font_obj_a_trans))
    print(get_info(font_obj_b_trans))
    # フォントA
    save_font(
        font_obj=font_obj_a_trans,
        input=input,
        output=output,
        suffix="_pre_merge",
        otf2ttf=not no_otf2ttf,
    )
    # フォントB
    save_font(
        font_obj=font_obj_b_trans,
        input=input2,
        output=output2,
        suffix="_pre_merge",
        otf2ttf=not no_otf2ttf,
    )


def action_merge_text_files(input, output, **_):
    merge_text_files(input_dir=input, output_file=output)


def action_generate_jisx0208(input, output="", **_):
    generate_jisx0208(output=output)


def action_remove_black_circles(input, output, **_):
    save_font(
        font_obj=remove_black_circles(TTFont(input)),
        input=input,
        output=output,
        suffix="_blackcircles_removed",
    )


ACTION_MAP = {
    "check_fonttype": action_check_fonttype,
    "get_info": action_get_info,
    "get_glyphs": action_get_glyphs,
    "get_average_size": action_get_average_size,
    "set_metrics": action_set_metrics,
    "transform_glyphs": action_transform_glyphs,
    "anonymize_info": action_anonymize_info,
    "change_weight": action_change_weight,
    "remove_empty_glyphs": action_remove_empty_glyphs,
    "create_subset": action_create_subset,
    "merge_fonts": action_merge_fonts,
    "merge_text_files": action_merge_text_files,
    "generate_jisx0208": action_generate_jisx0208,
    "remove_black_circles": action_remove_black_circles,
}


if __name__ == "__main__":
    main()
