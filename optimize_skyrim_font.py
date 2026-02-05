#!/usr/bin/env fontforge
import sys
import os

import constants
import analyze_average_metrics
import optimize_font

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"

def main(input_path, subset_path=constants.DEFAULT_SUBSET, mode=constants.MODE_EVERY, ratio_width=100, weight_offset=0, suffix=""):
    """フォントをスカイリムに最適化されたTTFフォントにする
           input_path: フォントファイルパス
           subset_path: サブセットファイルパス
           mode: 最適化モード(every,book,handwrite)
           ratio_width: ratio_width: 横幅指定(%)
           weight_offset: ウェイト調整値(em)
           suffix: 最適化済みフォントファイル名の末尾に付与する文字
           return: 最適化済みフォントファイルパス
    """

    # パラメータ解析
    mode_map = {
        constants.MODE_EVERY:     constants.SKYRIM_EVERY_FONT,
        constants.MODE_BOOK:      constants.SKYRIM_BOOK_FONT,
        constants.MODE_HANDWRITE: constants.SKYRIM_HANDWRITE_FONT
    }
    vanilla_font = mode_map.get(mode)
    # 不正なモードが指定された場合
    if vanilla_font is None:
        print(f"モードに不正な値が設定されたため、{constants.MODE_EVERY}として作動。")
        vanilla_font = constants.SKYRIM_EVERY_FONT

    # 処理開始
    print(f"--- スカイリム専用最適化開始: {input_path} ---")
    print(f"設定: サブセットファイル{subset_path}, 最適化モード{mode}")

    # 拡大縮小倍率を算出
    vanilla_result = analyze_average_metrics.main(vanilla_font)
    target_result = analyze_average_metrics.main(input_path)
    print(f"バニラフォントの縦方向平均値: {vanilla_result[3]}em")
    print(f"対象フォントの縦方向平均値: {target_result[3]}em")
    ratio_total = round(vanilla_result[3] / target_result[3] * 100)
    metrics = vanilla_result[0], vanilla_result[1]
    print(f"拡大縮小倍率: {ratio_total}%")
    print(f"メトリクス: Ascent:{metrics[0]}em Descent:{metrics[1]}em")
    
    # 最適化処理を実行
    output_path = optimize_font.main(input_path,subset_path,ratio_total,ratio_width,weight_offset,metrics,"","_"+mode+suffix)

    # 処理終了
    print(f"--- スカイリム専用最適化完了: {output_path} ---")
    
    return output_path


if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)