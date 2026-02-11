import argparse
import os
import sys
from pathlib import Path

from fontTools.merge import Merger
from fontTools.ttLib import TTFont
from otf2ttf.cli import otf_to_ttf

from optimizer import remove_empty_glyphs
from utils import BUILD_DIR, ENCODE, is_otf, is_ttf, load_text
from utils.inspector import get_average_size, get_glyphs, get_info
from utils.modifier import (
    anonymize_info,
    change_weight,
    set_metrics,
    transform_glyphs,
)
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
    if is_otf(font_obj):
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
    font_obj = change_weight(font_obj=font_obj, weight_offset=weight_offset)
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
    print(f"消去後のグリフ数は {get_info(font_obj=font_obj).glyph_count_uni} です。")
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


def action_merge_fonts(input, input2, output, ascent, descent, no_otf2ttf, **_):
    print("フォント同士を結合し新しいフォントを作成します。")
    merger = Merger()
    merged_font = merger.merge([input, input2])
    print(get_info(merged_font))
    save_font(
        font_obj=merged_font,
        input=input,
        output=output,
        suffix="_merged",
        otf2ttf=not no_otf2ttf,
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
}


def save_text(text: str, input: str = "", output: str = "", suffix: str = ""):
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}.txt"
    else:
        output = Path(output)
    output.write_text(text, encoding=ENCODE)
    print(f"テキストファイルを保存しました。: {output}")


def save_font(
    font_obj: TTFont,
    input: str = "",
    output: str = "",
    suffix: str = "",
    otf2ttf: bool = True,
):
    if not input and not output:
        raise ValueError(
            "入力ファイルパスと出力ファイルパスの両方を空にすることは出来ません。"
        )
    if not output:
        os.makedirs(BUILD_DIR, exist_ok=True)
        ext = Path(input).suffix
        if is_otf(font_obj) and otf2ttf:
            ext = ".ttf"
        output = Path(BUILD_DIR) / f"{Path(input).stem}{suffix}{ext}"
    else:
        output = Path(output)
    # 特に指定が無い場合はOTFであればTTFに変換する。
    if is_otf(font_obj) and otf2ttf:
        # 破壊的変更のため、font_objectには代入しないこと。
        print("OTFからTTFへの変換を行います。")
        print(
            "注: 出力ファイルパスで.otfを指定したとしても中身はTTFとなります。変換したくない場合は --no_otf2ttf フラグを有効にして下さい。"
        )
        otf_to_ttf(font_obj)
    font_obj.save(output)
    print(f"フォントファイルを保存しました。: {output}")


if __name__ == "__main__":
    main()
