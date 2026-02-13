import argparse
import sys

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

from utils.common import (
    BLANK_GLYPHS,
    dprint,
    generate_subset_jp_full,
    is_cff,
    is_cff2,
    load_text,
    reload_font,
    save_font,
)
from utils.inspector import get_info


def main():
    parser = argparse.ArgumentParser(
        description="フォントへ各種最適化を施すためのツールボックス"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
    )
    parser.add_argument(
        "-i",
        "--input_font_file",
        type=str,
        help="フォントファイル",
    )
    parser.add_argument(
        "-o",
        "--output_font_file",
        type=str,
        help="ファイルの書き出し先",
    )
    parser.add_argument(
        "-s",
        "--subset_file",
        type=str,
        default="",
        help="サブセットファイル デフォルト: ''",
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

    dispatch_action(**vars(args))


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def action_optimize_for_swf(
    input_font_file: str, output_font_file: str, debug: bool = False, **_
):
    font_obj = TTFont(input_font_file)
    font_obj = optimize_for_swf(font_obj=font_obj, debug=debug)
    output_font_file = save_font(
        font_obj=font_obj, input=input_font_file, output=output_font_file
    )
    print(f"フォントを保存しました: {output_font_file}")


def optimize_for_swf(font_obj: TTFont, debug: bool = False) -> TTFont:
    """
    SWFに埋め込むためのフォントに最適化する

    :param font_obj: フォント
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: 最適化済みフォント
    :rtype: TTFont
    """
    # 縦書き関連などSWFに不要なテーブル
    drop_tables = [
        'mort',
        'vhea',
        'vmtx',
        'VORG',
        'BASE',
        'DSIG',
        'gasp',
        'hdmx',
        'LTSH',
        'PCLT',
        'GSUB',
        'GPOS',
    ]

    for table_tag in drop_tables:
        if table_tag in font_obj:
            del font_obj[table_tag]
            print(f"削除しました: {table_tag}")

    return reload_font(font_obj=font_obj)


def action_create_subset(
    input_font_file: str,
    output_font_file: str,
    subset_file: str = "",
    debug: bool = False,
    **_,
):
    font_obj = TTFont(input_font_file)
    subset_text = load_text(subset_file)
    dprint(f"入力文字数: {len(subset_text)}", debug)
    dprint("元フォント情報", debug)
    dprint(get_info(font_obj=font_obj, debug=debug), debug)
    font_obj = create_subset(font_obj=font_obj, subset_text=subset_text, debug=debug)
    dprint(f"サブセット後の文字数(GlyphOrder): {len(font_obj.getGlyphOrder())}", debug)
    dprint(f"サブセット後の文字数(cmap): {len(font_obj.getBestCmap().keys())}", debug)
    dprint("サブセットフォント情報", debug)
    dprint(get_info(font_obj=font_obj, debug=debug), debug)
    output_font_file = save_font(
        font_obj=font_obj, input=input_font_file, output=output_font_file
    )
    print(f"フォントを保存しました: {output_font_file}")


def create_subset(font_obj: TTFont, subset_text: str, debug: bool = False) -> TTFont:
    """
    サブセットフォントを作成する

    サブセッターによりタグ情報の一部書き換えが発生するため、
    もしタグ情報の編集を行うのであればサブセット後に実施するようにして下さい。

    :param font_obj: フォント
    :type font_obj: TTFont
    :param subset_text: サブセット文字列
    :type subset_text: str
    :return: サブセットフォント
    :rtype: TTFont
    """
    # サブセットフォントのオプション設定
    options = Options()
    options.notdef_glyph = True  # 常に .notdef を含める（安全対策）
    options.notdef_outline = True  # .notdef（豆腐）の形を維持
    # options.glyph_names = True  # デバッグ用 Format 3.0への更新が行われなくなるため、古いシステムでは読み込みエラーの可能性あり。
    options.retain_gids = False  # グリフIDを保持せず再割り当てする（軽量化のため）
    options.legacy_kern = True  # 古い形式のカーニングも維持
    options.name_IDs = ['*']  # 全てのnameレコードを保持する
    options.name_languages = ['*']  # 全てのnameレコードを保持する
    options.hinting = True  # ヒンティングの維持（デフォルトTrueですが念のため）
    options.layout_features = ['*']  # レイアウト機能（合字やカーニング）を保持
    options.recalc_timestamp = False  # 更新日時を変更したくない場合

    subsetter = Subsetter(options=options)
    subsetter.populate(text=subset_text)
    subsetter.subset(font=font_obj)

    return reload_font(font_obj=font_obj)


def action_remove_empty_glyphs(
    input_font_file: str, output_font_file: str, debug: bool = False, **_
):
    font_obj = TTFont(input_font_file)
    dprint("作業前", debug)
    dprint(get_info(font_obj=font_obj, debug=debug), debug)
    font_obj = remove_empty_glyphs(font_obj=font_obj, debug=debug)
    output_font_file = save_font(
        font_obj=font_obj,
        input=input_font_file,
        output=output_font_file,
        suffix="empty_glyphs_removed",
    )
    dprint("作業後", debug)
    dprint(get_info(font_obj=font_obj, debug=debug), debug)
    print(f"フォントを保存しました: {output_font_file}")


def remove_empty_glyphs(font_obj: TTFont, debug: bool = False) -> TTFont:
    """
    実質的なアウトラインを持たないグリフをcmapから削除し、
    ゲーム内で豆腐(.notdef)が表示されるようにする。
    """
    # CFF/CFF2の場合は非対応
    if is_cff(font_obj) or is_cff2(font_obj):
        raise ValueError("この関数はCFF/CFF2には対応していません。")

    glyf = font_obj['glyf']
    cmap = font_obj.getBestCmap()
    deleted_glyphs = []

    for code, name in cmap.items():
        if code in BLANK_GLYPHS:
            continue

        glyph = glyf[name]

        # TrueTypeの場合、numberOfContours が 0 ならアウトラインがない
        # (複合グリフの場合は -1 になるので、0 かどうかで判定)
        if glyph.numberOfContours == 0:
            deleted_glyphs.append(code)

    # cmapから削除（これでフォント的に「持っていない文字」になる）
    for code in deleted_glyphs:
        del cmap[code]
        # dprint(f"グリフをcmapから削除: U+{code:04X}", debug)

    # このままでは実体が残りっぱなしになるが、
    # JIS第四基準+αまで網羅したサブセットを行うことで、実質的にGIDを整理した綺麗なフォントになる。
    font_obj = create_subset(
        font_obj=font_obj, subset_text=generate_subset_jp_full(), debug=debug
    )

    return reload_font(font_obj)


def action_remove_black_circles(
    input_font_file: str, output_font_file: str, debug: bool = False
):
    font_obj = TTFont(input_font_file)
    font_obj = remove_black_circles(font_obj=font_obj, debug=debug)
    output_font_file = save_font(
        font_obj=font_obj,
        input=input_font_file,
        output=output_font_file,
        suffix="_black_circles_removed",
    )
    print(f"フォントを保存しました: {output_font_file}")


def remove_black_circles(font_obj: TTFont, debug: bool = False):
    """
    フォントから黒丸（●）と思われるグリフを検出し、削除する。
    ただし、. や , などの基本文字は除外する。
    """
    glyf_table = font_obj['glyf']
    cmap = font_obj.getBestCmap()

    # 1. 漢字（CJK Unified Ideographs）の範囲を定義
    # 一般的な漢字の範囲: U+4E00 - U+9FFF
    # (必要に応じて拡張 A: 3400-4DBF も含めることがありますが、まずは基本の 4E00-9FFF を「判定対象」にします)
    kanji_range = range(0x4E00, 0x9FFF + 1)

    # 2. ホワイトリスト（保護対象）を作成
    keep_glyphs = set()
    keep_glyphs.add('.notdef')

    for code, name in cmap.items():
        # 「漢字の範囲」に入っていない文字はすべて保護！
        if code not in kanji_range:
            keep_glyphs.add(name)

    removed_count = 0
    glyphs_to_remove = []

    # 3. 判定ループ（漢字エリアにあるグリフだけをチェック）
    for glyph_name in font_obj.getGlyphOrder():
        if glyph_name in keep_glyphs:
            continue

        if glyph_name not in glyf_table:
            continue

        glyph = glyf_table[glyph_name]

        # 黒丸判定（サイズを 90 まで下げて、小さなゴミも逃さない）
        if glyph.numberOfContours == 1:
            xMin, yMin, xMax, yMax = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
            width = xMax - xMin
            height = yMax - yMin

            aspect_ratio = width / height if height != 0 else 0
            if 0.8 < aspect_ratio < 1.2 and width > 90:
                glyphs_to_remove.append(glyph_name)

    # 4. 実行（物理削除せず、中身を空にする）
    from fontTools.ttLib.tables._g_l_y_f import Glyph

    for g_name in glyphs_to_remove:
        # cmapからも消す（検索に引っかからないようにする）
        for code in [k for k, v in cmap.items() if v == g_name]:
            del cmap[code]
        # 中身を空にする
        glyf_table[g_name] = Glyph()
        removed_count += 1

    return reload_font(font_obj)


ACTION_MAP = {
    "optimize_for_swf": action_optimize_for_swf,
    "create_subset": action_create_subset,
    "remove_empty_glyphs": action_remove_empty_glyphs,
    "remove_black_circles": action_remove_black_circles,
}

if __name__ == "__main__":
    main()
