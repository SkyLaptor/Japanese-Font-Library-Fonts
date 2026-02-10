import argparse
import io
import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from fontTools import subset
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont

# 一般的に空白として扱われる（削除してはいけない）グリフ
PROTECTED_BLANK_GLYPH_LIST = {
    ".notdef",  # 未定義文字の代替（必須）
    "space",  # 半角スペース
    "uni0020",  # 半角スペース(Unicode)
    "uni3000",  # 全角スペース
    "nbspace",  # 改行しないスペース
    "uni00A0",  # 改行しないスペース(Unicode)
    "uni2002",  # En Space
    "uni2003",  # Em Space
    "uni2007",  # Figure Space
    "uni2008",  # Punctuation Space
    "uni2009",  # Thin Space
    "uni200A",  # Hair Space
}

# 基準となるUnitsPerEM
ASCENT = 880
DESCENT = -144
BASE_UPM = ASCENT + abs(DESCENT)


def main():
    parser = argparse.ArgumentParser(
        description="fontToolsを用いてフォントに対する様々な操作を行うためのライブラリ"
    )

    parser.add_argument("-i", "--input", help="入力元のフォントファイルパス")
    parser.add_argument("--input2", help="入力元のフォントファイルパス2")
    parser.add_argument(
        "-o",
        "--output",
        default="",
        help="出力先のフォントファイルパス",
    )
    parser.add_argument("--subset", help="サブセットフォントファイルのパス")
    parser.add_argument(
        "--ascent",
        type=int,
        default=None,
        help="Ascentの値(units)",
    )
    parser.add_argument(
        "--descent",
        type=int,
        default=None,
        help="Descentの値(units)",
    )
    parser.add_argument(
        "--scale_width", type=float, help="横方向の拡大縮小率(1.0=100.0%%)"
    )
    parser.add_argument(
        "--scale_height", type=float, help="縦方向の拡大縮小率(1.0=100.0%%)"
    )
    parser.add_argument(
        "--weight_offset",
        type=int,
        help="文字の太さ調整(units)",
    )
    parser.add_argument(
        "--shift_height",
        type=int,
        help="文字の上下調整(units)",
    )

    parser.add_argument(
        "--action",
        choices=[
            "report_font_info",
            "clean_empty_glyphs",
            "anonymize_font_info",
            "get_metrics_average",
            "resize_glyphs",
            "export_glyph_list",
            "create_subset",
            "adjust_font_metrics",
            "expand_glyph_weight",
            "shift_glyph_height",
            "fill_missing_glyphs",
            "remove_specific_placeholder",
            "remove_hinting",
        ],
        default="print_font_info",
        help="実行する操作(デフォルト: print_font_info)",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    toolbox(
        input_font_path=args.input,
        input_font_path2=args.input2,
        output_font_path=args.output,
        subset_glyphs_path=args.subset,
        ascent=args.ascent,
        descent=args.descent,
        scale_width=args.scale_width,
        scale_height=args.scale_height,
        weight_offset=args.weight_offset,
        shift_height=args.shift_height,
        action=args.action,
    )


def toolbox(
    action: str,
    input_font_path: str,
    input_font_path2: str,
    output_font_path: str,
    subset_glyphs_path: str,
    scale_width: float,
    scale_height: float,
    weight_offset: int,
    shift_height: int,
    ascent: int,
    descent: int,
    **kwargs,
) -> None:
    # TODO: あとでちゃんとしたPyDoc
    if not input_font_path or not os.path.exists(input_font_path):
        raise FileNotFoundError(
            f"入力されたファイルが正しくありません。: {input_font_path}"
        )

    if ascent is not None and descent is None:
        raise ValueError(
            f"AscentとDescentは対で入力して下さい。: Ascent: {ascent}, Descent: {descent}"
        )

    if ascent is None and descent is not None:
        raise ValueError(
            f"AscentとDescentは対で入力して下さい。: Ascent: {ascent}, Descent: {descent}"
        )

    # 8の倍数チェック
    upm = BASE_UPM
    if ascent is not None and descent is not None:
        upm = ascent + abs(descent)
        if upm % 8 != 0:
            raise ValueError(
                f"Invalid metrics: Ascent({ascent}) + |Descent({descent})| = UPM({upm}). "
                f"UPM must be a multiple of 8."
            )

    font_obj = TTFont(input_font_path)

    suffix = ""
    if action == "report_font_info":
        suffix = "_info"
        report = report_font_info(font_obj)
        print(report)
        report_path = Path("build") / f"{Path(input_font_path).stem}{suffix}.txt"
        report_path.write_text(report, encoding="utf-8")
        return

    elif action == "clean_empty_glyphs":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        result = clean_empty_glyphs(font_obj)
        print(
            f"不正な空白グリフの消去が完了しました。総グリフ数:{len(result.all_glyphs)}, 削除グリフ数:{len(result.removed_glyphs)}, 残グリフ数:{len(result.all_glyphs) - len(result.removed_glyphs)}"
        )
        suffix = "_emptycleaned"
        font_obj = result.font_obj

    elif action == "anonymize_font_info":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_anonymized"
        font_obj = anonymize_font_info(font_obj)

    elif action == "get_metrics_average":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        result = get_metrics_average(font_obj, upm)
        print("--- Glyph Metrics (BBox) ---")
        print(f"Sample Kanji Count:      {result.count}")
        print(
            f"Avg BBox Size (Raw):     W{result.avg_bbox_size_raw_w:.1f} x H{result.avg_bbox_size_raw_h:.1f} (font is {result.upm} UPM)"
        )
        print(
            f"Avg BBox Size (Norm):    W{result.avg_bbox_size_norm_w:.1f} x H{result.avg_bbox_size_norm_h:.1f} (per {upm} UPM)"
        )
        return

    elif action == "resize_glyphs":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_resized"
        font_obj = resize_glyphs(font_obj, scale_width, scale_height)

    elif action == "export_glyph_list":
        suffix = "_glyph_list"
        glyph_list = export_glyph_list(font_obj)
        print(glyph_list)
        list_path = Path("build") / f"{Path(input_font_path).stem}{suffix}.txt"
        list_path.write_text(glyph_list, encoding="utf-8")
        return

    elif action == "create_subset":
        suffix = "_subset"
        suffix2 = "_nonexisted_glyphs"
        result = create_subset(font_obj, load_subset_text(subset_glyphs_path))
        font_obj = result.font_obj
        non_existed_glyphs = result.non_existed_glyphs
        print(
            f"サブセットテキストから欠落しているグリフの数: {len(non_existed_glyphs)}"
        )
        print(non_existed_glyphs)
        glyphs_path = Path("build") / f"{Path(input_font_path).stem}{suffix2}.txt"
        glyphs_path.write_text(non_existed_glyphs, encoding="utf-8")

    elif action == "adjust_font_metrics":
        suffix = "_metrics_adjusted"
        font_obj = adjust_font_metrics(font_obj, 880, -144)

    elif action == "expand_glyph_weight":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_weight_expanded"
        font_obj = expand_glyph_weight(font_obj, weight_offset)

    elif action == "shift_glyph_height":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_height_shifted"
        font_obj = shift_glyph_height(font_obj, shift_height)

    elif action == "fill_missing_glyphs":
        font_obj_b = TTFont(input_font_path2)
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_merged"
        font_obj = fill_missing_glyphs(font_obj, font_obj_b, 880, -144)

    elif action == "remove_specific_placeholder":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_specific_placeholder_removed"
        font_obj = remove_specific_placeholder(font_obj)

    elif action == "remove_hinting":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_hint_removed"
        font_obj = remove_hinting(font_obj)

    else:
        raise ValueError(f"正しくない動作が指定されています。: {action}")

    # TTFを出力
    if not output_font_path:
        base_dir = "build"
        os.makedirs(base_dir, exist_ok=True)
        file_name = os.path.basename(input_font_path)
        name_without_ext = os.path.splitext(file_name)[0]
        output_font_path = os.path.join(base_dir, f"{name_without_ext}{suffix}.ttf")

    font_obj.save(output_font_path)
    print(f"保存完了: {output_font_path}")


def is_otf(font_obj: TTFont) -> bool:
    # TODO: doc
    if "CFF " in font_obj or "CFF2" in font_obj:
        return True
    return False


def report_font_info(font_obj: TTFont) -> str:
    """フォント情報をレポート形式の文字列として生成する"""
    output = io.StringIO()

    # print関数の file 引数に output を指定することで、
    # 標準出力ではなく StringIO に書き込まれます。
    def report_print(*args, **kwargs):
        print(*args, **kwargs, file=output)

    head = font_obj["head"]
    hhea = font_obj["hhea"]
    os2 = font_obj["OS/2"]

    cmap = font_obj.getBestCmap()

    report_print("--- General ---")
    report_print(f"Glyph count: {len(font_obj.getGlyphOrder())}")
    report_print(f"Unicode characters count: {len(cmap.keys())}")
    report_print(f"Units Per Em (UPM): {head.unitsPerEm}")

    unix_created = head.created - 2082844800
    created_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(unix_created))
    report_print(f"Created:            {created_time}")

    report_print("--- OS/2 Table ---")
    report_print(f"Vendor ID:          '{os2.achVendID}'")
    report_print(f"WinAscent/Descent:  {os2.usWinAscent} / {os2.usWinDescent}")
    report_print(f"TypoAscender/Desc:  {os2.sTypoAscender} / {os2.sTypoDescender}")
    report_print(f"TypoLineGap:        {os2.sTypoLineGap}")
    report_print(f"USE_TYPO_METRICS:   {bool(os2.fsSelection & 0b10000000)}")

    report_print("--- hhea Table (Mac/iOS) ---")
    report_print(f"hhea Ascender/Desc: {hhea.ascender} / {hhea.descender}")
    report_print(f"hhea LineGap:       {hhea.lineGap}")

    report_print("-" * 60)
    report_print(f"{'ID':<5} | {'Name Key':<20} | {'Value'}")
    report_print("-" * 60)

    # nameテーブルのループ処理も同様に report_print を使用
    name_table = font_obj["name"]
    target_ids = {
        0: "Copyright",
        1: "Family Name",
        2: "Subfamily Name",
        3: "Unique ID",
        4: "Full Name",
        5: "Version",
        6: "PostScript Name",
        13: "License",
    }

    for name_id, label in target_ids.items():
        record = (
            name_table.getName(name_id, 3, 1, 0x411)
            or name_table.getName(name_id, 3, 1, 0x409)
            or name_table.getName(name_id, 1, 0, 0)
        )
        value = record.toUnicode() if record else "(Not Found)"
        report_print(f"{name_id:<5} | {label:<20} | {value}")

    return output.getvalue()


@dataclass
class CleanupResult:
    font_obj: TTFont
    all_glyphs: list[str]
    removed_glyphs: list[str]


def clean_empty_glyphs(font_obj: TTFont) -> CleanupResult:
    """
    フォントオブジェクトの中から、不正な空白グリフを消去します。

    :param font_obj: 処理するフォントオブジェクト
    :type font_obj: TTFont
    :return: 処理結果
    :rtype: CleanupResult
    """
    all_glyphs = font_obj.getGlyphOrder()
    removed_glyphs = []

    # 1. 削除対象の特定
    if "glyf" in font_obj:  # TTFの場合
        glyf_table = font_obj["glyf"]
        for name in all_glyphs:
            if name in PROTECTED_BLANK_GLYPH_LIST:
                continue

            # 輪郭(contours)が0個、かつコンポーネント(参照)も持っていないものを抽出
            glyph = glyf_table[name]
            if glyph.numberOfContours == 0 and not hasattr(glyph, "components"):
                removed_glyphs.append(name)

    elif "CFF " in font_obj:  # OTFの場合
        charstrings = font_obj["CFF "].cff.topDictIndex[0].CharStrings
        for name in all_glyphs:
            if name in PROTECTED_BLANK_GLYPH_LIST:
                continue
            if len(charstrings[name].bytecode) <= 1:  # ほぼデータなし
                removed_glyphs.append(name)

    # 2. サブセット機能を使って削除を実行
    # 残すべきグリフ = (全てのグリフ) - (削除対象)
    keep_glyphs = [g for g in all_glyphs if g not in removed_glyphs]

    options = subset.Options()
    # 念のため、ヒント情報やレイアウトテーブル(GSUB/GPOS)を維持する設定
    options.layout_features = ["*"]

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=keep_glyphs)
    subsetter.subset(font_obj)

    return CleanupResult(font_obj, all_glyphs, removed_glyphs)


def anonymize_font_info(font_obj: TTFont) -> TTFont:
    family_name = "Anonymized"
    ps_name = "Anonymized-Regular"
    subfamily = "Regular"

    # 1. nameテーブルの再構築
    name_table = font_obj["name"]
    new_names = []

    # 必須のIDだけを絞り込んで再定義する
    for record in name_table.names:
        encoding = record.getEncoding()

        if record.nameID in [1, 16, 17]:  # Family Name
            record.string = family_name.encode(encoding)
        elif record.nameID in [2, 18]:  # Subfamily Name
            record.string = subfamily.encode(encoding)
        elif record.nameID == 3:  # Unique ID
            record.string = f"0.000;NONE;{ps_name}".encode(encoding)
        elif record.nameID == 4:  # Full Name
            record.string = f"{family_name} {subfamily}".encode(encoding)
        elif record.nameID == 5:  # Version
            record.string = "Version 0.000".encode(encoding)
        elif record.nameID == 6:  # PostScript Name
            record.string = ps_name.encode(encoding)
        else:
            # 著作権やURLなどは、空文字を入れるのではなく「リストに入れない」ことで削除
            continue

        new_names.append(record)

    name_table.names = new_names

    # 2. headテーブルの更新
    if "head" in font_obj:
        # Mac epoch (1904) と Unix epoch (1970) の差分: 2,082,844,800秒
        now = int(time.time()) + 2082844800
        font_obj["head"].created = now
        font_obj["head"].modified = now

    # 3. OS/2テーブルの更新
    if "OS/2" in font_obj:
        font_obj["OS/2"].achVendID = "NONE"

    return font_obj


@dataclass
class MetricsStats:
    upm: int
    count: int
    avg_bbox_size_raw_w: float
    avg_bbox_size_raw_h: float
    avg_bbox_size_norm_w: float
    avg_bbox_size_norm_h: float


def get_metrics_average(font_obj: TTFont, norm_upm: int) -> MetricsStats:
    """メソッドを介さず、glyfテーブルの生データから直接座標を抽出する"""
    raw_upm = font_obj["head"].unitsPerEm
    total_width, total_height, count = 0, 0, 0

    # glyfテーブルを直接取得
    if "glyf" not in font_obj:
        print("CRITICAL: No 'glyf' table found. This font might be corrupted.")
        return MetricsStats(raw_upm, 0, 0.0, 0.0, 0.0, 0.0)

    glyf_table = font_obj["glyf"]
    glyph_names = font_obj.getGlyphOrder()

    # print(f"DEBUG: Force-scanning {len(glyph_names)} glyphs via raw table...")

    for name in glyph_names:
        # getGlyphSet()を通さず、テーブルから直接グリフオブジェクトを取り出す
        # これなら、中身が複雑な複合グリフでも、ヘッダーの座標情報だけは取れる
        try:
            glyph = glyf_table[name]

            # TTFのグリフオブジェクトは、中身を解析(draw)しなくても
            # ヘッダーに xMin, yMin, xMax, yMax を持っている
            if hasattr(glyph, "xMax"):
                xMin, yMin, xMax, yMax = glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax
                w, h = xMax - xMin, yMax - yMin

                # 判定（少し緩めに設定）
                if (h > raw_upm * 0.4) and (0.5 < w / h < 1.5):
                    total_width += w
                    total_height += h
                    count += 1

                    # if count <= 3:
                    #     print(f"DEBUG: Successfully extracted '{name}': {w}x{h}")
        except Exception:
            # ここで何が起きたか1回だけ表示
            if count == 0 and name == glyph_names[100]:
                # print(f"DEBUG: Error accessing glyph '{name}': {e}")
                pass
            continue

    if count == 0:
        return MetricsStats(raw_upm, 0, 0.0, 0.0, 0.0, 0.0)

    avg_w, avg_h = total_width / count, total_height / count
    norm_w = (avg_w / raw_upm) * norm_upm
    norm_h = (avg_h / raw_upm) * norm_upm

    return MetricsStats(
        upm=raw_upm,
        count=count,
        avg_bbox_size_raw_w=avg_w,
        avg_bbox_size_raw_h=avg_h,
        avg_bbox_size_norm_w=norm_w,
        avg_bbox_size_norm_h=norm_h,
    )


def resize_glyphs(
    font_obj: TTFont, scale_width: float, scale_height: float, shift_height: float = 0
) -> TTFont:
    """
    全グリフを指定した倍率で各方向にスケーリングし、
    あわせて横送りの幅（hmtx）も調整する。
    なお、1つのフォントオブジェクトに対し2回呼ぶと不具合が起きるので注意
    shift_y: スカイリム用の上下位置調整（既存のdyとは別に加算される移動量）
    """
    if hasattr(font_obj, "_glyphSet"):
        del font_obj._glyphSet

    glyph_set = font_obj.getGlyphSet()
    glyf_table = font_obj["glyf"]
    hmtx_table = font_obj["hmtx"]
    upm = font_obj["head"].unitsPerEm

    # --- 中央寄せの計算 ---
    # 横方向 (dx): 横幅を scale_w にしたときの中央寄せ
    dx = (upm * (1.0 - scale_width)) / 2

    # 縦方向 (dy):
    # 基本の中央寄せに加え、スカイリム特有の上下位置調整 (shift_y) を加算する
    dy = ((upm * (1.0 - scale_height)) / 2) + shift_height

    for glyph_name in font_obj.getGlyphOrder():
        old_glyph = glyph_set[glyph_name]

        # 【修正ポイント】 scale_w と scale_h を正しく使い分ける
        # 行列: (scale_x, 0, 0, scale_y, dx, dy)
        transformation = (scale_width, 0, 0, scale_height, dx, dy)

        tt_pen = TTGlyphPen(glyph_set)
        trans_pen = TransformPen(tt_pen, transformation)
        old_glyph.draw(trans_pen)

        new_glyph = tt_pen.glyph()
        new_glyph.recalcBounds(glyf_table)
        glyf_table[glyph_name] = new_glyph

        # --- 横送り（アドバンス幅）の調整 ---
        width, lsb = hmtx_table[glyph_name]

        # 幅とLSBは「横方向のスケール(scale_w)」のみに依存する
        new_width = int(round(width * scale_width))
        new_lsb = int(round(lsb * scale_width + dx))

        hmtx_table[glyph_name] = (new_width, new_lsb)

    return font_obj


def export_glyph_list(font_obj: TTFont) -> list[str]:
    """
    フォント内のUnicode定義がある有効なグリフを抽出し、
    UTF-8テキストファイルとして出力する。
    """
    # 1. cmap（文字コードとグリフ名の対応表）を取得
    cmap = font_obj.getBestCmap()

    # 2. Unicode値(int)から文字(str)に変換
    # cmapのキーはUnicode値(整数)
    valid_chars = []
    for code in sorted(cmap.keys()):
        char = chr(code)
        valid_chars.append(char)

    # 3. テキストファイルとして保存
    # 改行なしで一列に並べる、あるいは1行ずつ出すなど用途に合わせて調整可能
    # ここではサブセット定義ファイルとして使いやすいよう、結合した文字列で出力します
    glyph_text = "".join(valid_chars)

    return glyph_text


@dataclass
class SubsetResult:
    font_obj: TTFont
    non_existed_glyphs: str


def create_subset(font_obj: TTFont, subset_glyphs: str) -> SubsetResult:
    """
    指定した文字列(subset_glyphs)に含まれる文字だけを残した
    サブセットフォントを作成し、存在しなかった文字（重複排除済み）と共に返す。
    """
    # 1. フォントが持っている全Unicode値のセットを取得 (高速照合用)
    font_unicode_set = set(font_obj.getBestCmap().keys())

    # 2. 入力文字列を集合(set)にして重複を排除し、存在しない文字を抽出
    input_char_set = set(subset_glyphs)
    non_existed_chars = [c for c in input_char_set if ord(c) not in font_unicode_set]

    # リストをソートしておくと、レポートが見やすくなります
    non_existed_glyphs = "".join(sorted(non_existed_chars))

    # 3. サブセッタの設定と実行
    options = subset.Options()
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=subset_glyphs)

    # 4. サブセット処理の適用 (インプレース書き換え)
    subsetter.subset(font_obj)

    return SubsetResult(font_obj=font_obj, non_existed_glyphs=non_existed_glyphs)


def load_subset_text(subset_glyphs_path: str) -> str:
    """
    指定されたパスからテキストファイルを読み込み、
    重複を除去した1行の文字列として返す。
    """
    path = Path(subset_glyphs_path)
    if not path.exists():
        raise FileNotFoundError(f"Subset text file not found: {subset_glyphs_path}")

    # UTF-8で読み込み
    content = path.read_text(encoding="utf-8")

    # 改行やタブなどの制御文字を除去し、重複を排除（setを使用）
    # 空白文字(スペース)をサブセットに含めるかは用途によりますが、
    # 基本的には含めておいたほうが安全です。
    char_set = set(content.replace("\n", "").replace("\r", "").replace("\t", ""))

    # ソートして文字列に戻す（デバッグ時に中身を確認しやすくするため）
    return "".join(sorted(list(char_set)))


def adjust_font_metrics(font_obj: TTFont, ascent: int, descent: int) -> TTFont:
    """
    Ascent/Descentを調整し、その合計値をUPMとして設定する。
    Descentは負の値である
    UPMが8の倍数でない場合はエラーを投げる。
    """
    # 1. UPMの計算 (Descentは通常負の値なので abs を取る)
    old_upm = font_obj["head"].unitsPerEm
    new_upm = ascent + abs(descent)

    # 2. 8の倍数チェック
    if new_upm % 8 != 0:
        raise ValueError(
            f"Invalid metrics: Ascent({ascent}) + |Descent({descent})| = UPM({new_upm}). "
            f"UPM must be a multiple of 8."
        )

    # 2. UPMが異なる場合のみ、グリフ自体のサイズを調整
    if old_upm != new_upm:
        scale = new_upm / old_upm
        # print(f"Resizing glyphs: {old_upm} -> {new_upm} (scale: {scale:.4f})")
        # 以前作成した resize_glyphs を呼び出し (引数は dx=0, dy=0 を想定)
        # ※resize_glyphs(font_obj, scale_x, scale_y, dx, dy) の形式に合わせてください
        resize_glyphs(font_obj, scale, scale)
    else:
        # print(f"UPM already matches {new_upm}. Skipping glyph resize.")
        pass

    # 3. head テーブルの UPM 更新
    font_obj["head"].unitsPerEm = new_upm

    # 4. OS/2 テーブル (Windows 用)
    if "OS/2" in font_obj:
        os2 = font_obj["OS/2"]

        # バージョンが古い（4未満）場合は、4に引き上げる
        if os2.version < 4:
            # バージョン 2 で追加された項目
            if not hasattr(os2, "sxHeight"):
                os2.sxHeight = 0
            if not hasattr(os2, "sCapHeight"):
                os2.sCapHeight = 0
            if not hasattr(os2, "usDefaultChar"):
                os2.usDefaultChar = 0
            if not hasattr(os2, "usBreakChar"):
                os2.usBreakChar = 32  # 半角スペース
            if not hasattr(os2, "usMaxContext"):
                os2.usMaxContext = 0
            os2.version = 4

        os2.sTypoAscender = ascent
        os2.sTypoDescender = descent
        os2.usWinAscent = abs(ascent)
        os2.usWinDescent = abs(descent)
        os2.sTypoLineGap = 0
        # OS/2のメトリクス設定を優先させるフラグ
        os2.fsSelection |= 1 << 7

    # 5. hhea テーブル (Mac 用)
    if "hhea" in font_obj:
        hhea = font_obj["hhea"]
        hhea.ascent = ascent
        hhea.descender = descent
        hhea.lineGap = 0

    # 6. post テーブル (下線の位置と太さ)
    if "post" in font_obj:
        post = font_obj["post"]
        # UPM変更に合わせてスケールさせる
        if old_upm != new_upm:
            scale = new_upm / old_upm
            post.underlinePosition = int(round(post.underlinePosition * scale))
            post.underlineThickness = int(round(post.underlineThickness * scale))

    # print(f"Metrics adjusted: UPM={new_upm} (Ascent:{ascent}, Descent:{descent})")
    return font_obj


def expand_glyph_weight(font_obj: TTFont, weight_offset: int) -> TTFont:
    if "glyf" not in font_obj:
        return font_obj

    glyf_table = font_obj["glyf"]

    # 向きを反転させる（細くなったなら逆へ飛ばす）
    # TrueTypeの一般的な向きに合わせるため、オフセットを反転
    actual_offset = -weight_offset

    for glyph_name in font_obj.getGlyphOrder():
        glyph = glyf_table[glyph_name]
        if glyph.numberOfContours <= 0:
            continue

        coords = list(glyph.coordinates)
        new_coords = list(coords)
        start_idx = 0

        for end_idx in glyph.endPtsOfContours:
            contour_indices = list(range(start_idx, end_idx + 1))
            n = len(contour_indices)
            if n < 2:
                continue

            for i in range(n):
                curr_idx = contour_indices[i]
                prev_idx = contour_indices[(i - 1) % n]
                next_idx = contour_indices[(i + 1) % n]

                x0, y0 = coords[prev_idx]
                x1, y1 = coords[curr_idx]
                x2, y2 = coords[next_idx]

                v1x, v1y = x1 - x0, y1 - y0
                v2x, v2y = x2 - x1, y2 - y1

                def get_normal(dx, dy):
                    length = math.sqrt(dx * dx + dy * dy)
                    if length == 0:
                        return 0, 0
                    # ここで押し出し方向を制御（dy, -dx）
                    return dy / length, -dx / length

                n1x, n1y = get_normal(v1x, v1y)
                n2x, n2y = get_normal(v2x, v2y)

                nx, ny = n1x + n2x, n1y + n2y
                n_len = math.sqrt(nx * nx + ny * ny)

                if n_len != 0:
                    # actual_offset を使うことで外側へ！
                    new_coords[curr_idx] = (
                        x1 + (nx / n_len) * actual_offset,
                        y1 + (ny / n_len) * actual_offset,
                    )

            start_idx = end_idx + 1

        glyph.coordinates = type(glyph.coordinates)(new_coords)
        glyph.recalcBounds(glyf_table)

    # print(f"Bold expansion finished: +{weight_offset}")
    return font_obj


def shift_glyph_height(font_obj: TTFont, shift_height: int) -> TTFont:
    """
    全グリフの上下位置を指定したユニット分シフトする。
    shift_height: 正の値で上へ、負の値で下へ移動。
    """
    if "glyf" not in font_obj:
        # print("glyf table not found.")
        return font_obj

    glyf_table = font_obj["glyf"]
    glyph_order = font_obj.getGlyphOrder()

    # print(f"Shifting glyph heights by {shift_height} units...")

    for glyph_name in glyph_order:
        glyph = glyf_table[glyph_name]

        # 輪郭がないグリフ（スペースなど）も、
        # 境界線データ（yMin, yMax）を持っている場合があるので一応処理
        if glyph.numberOfContours != 0:
            # 1. 座標をすべて一律にずらす
            coords = glyph.coordinates
            new_coords = []
            for x, y in coords:
                new_coords.append((x, y + shift_height))

            glyph.coordinates = type(glyph.coordinates)(new_coords)

        # 2. 境界線情報を再計算（これをしないと表示位置がおかしくなる）
        glyph.recalcBounds(glyf_table)

    # print(f"Shift completed: {'+' if shift_height >= 0 else ''}{shift_height}")
    return font_obj


def fill_missing_glyphs(
    font_obj_a: TTFont, font_obj_b: TTFont, ascent: int, descent: int
) -> TTFont:
    """
    1. A, B 個別にメトリクスを調整
    2. A, B 個別に不要な空白グリフを掃除
    3. A に無い文字を B からインデックス参照で確実にコピー
    4. 保存時の不整合を物理的に排除
    """

    # --- Phase 1: 各フォントのコンディションを整える ---
    # print("Standardizing Font A...")
    a_result = get_metrics_average(font_obj_a)  # いろいろする前に測定しておくこと
    font_obj_a = adjust_font_metrics(font_obj_a, ascent, descent)
    font_obj_a = clean_empty_glyphs(font_obj_a).font_obj

    # print("Standardizing Font B...")
    b_result = get_metrics_average(font_obj_b)  # いろいろする前に測定しておくこと
    font_obj_b = adjust_font_metrics(font_obj_b, ascent, descent)
    font_obj_b = clean_empty_glyphs(font_obj_b).font_obj

    # --- Phase 1 内の B 調整セクション ---
    # print("Calculating scale ratio based on average glyph size...")

    # print(f"Font A Average Height: {a_result.avg_bbox_size_raw_h:.2f} units")
    # print(f"Font B Average Height: {b_result.avg_bbox_size_raw_h:.2f} units")

    # 高さを基準に比率を算出 (例: 850 / 950 = 0.894)
    target_ratio = a_result.avg_bbox_size_raw_h / b_result.avg_bbox_size_raw_h

    # 安全策: 異常な倍率にならないようリミッターをかける (任意)
    # target_ratio = max(0.5, min(target_ratio, 1.2))

    # print(f"Automated Scaling: Resizing Font B by x{target_ratio:.4f} to match Font A")

    # スケーリング実行
    font_obj_b = resize_glyphs(font_obj_b, target_ratio)

    # --- Phase 2: マージ準備 ---
    print("--- Phase 2: Merging Glyphs ---")
    cmap_a = font_obj_a.getBestCmap()
    cmap_b = font_obj_b.getBestCmap()
    glyf_a = font_obj_a["glyf"]
    glyf_b = font_obj_b["glyf"]
    hmtx_a = font_obj_a["hmtx"]
    hmtx_b = font_obj_b["hmtx"]

    # BにあってAにないUnicodeを特定
    missing_codes = sorted(set(cmap_b.keys()) - set(cmap_a.keys()))

    if not missing_codes:
        print("No missing glyphs to fill.")
        return font_obj_a

    print(f"Transferring {len(missing_codes)} characters from Font B to Font A...")

    existing_glyph_names = set(font_obj_a.getGlyphOrder())
    new_glyph_order = list(font_obj_a.getGlyphOrder())

    # --- Phase 3: グリフ・メトリクス・cmap のコピー ---
    for code in missing_codes:
        original_name = cmap_b[code]

        if original_name is None:
            continue

        # グリフ名が glyf テーブルにあるか確認
        if original_name not in glyf_b:
            continue

        # 名前衝突回避（同じ名前があれば .fallback を付与）
        dest_name = original_name
        if dest_name in existing_glyph_names:
            dest_name = f"{original_name}.fallback"

        # 1. グリフ形状のコピー
        glyf_a[dest_name] = glyf_b[original_name]

        # 2. 横幅(hmtx)のコピー：名前ではなくID(Index)経由で確実に引く
        try:
            # Source Han Serif のように内部名と外部名が違う場合への対策
            gid = font_obj_b.getGlyphID(original_name)
            real_name_in_b = font_obj_b.getGlyphOrder()[gid]
            hmtx_a.metrics[dest_name] = hmtx_b.metrics[real_name_in_b]
        except (KeyError, IndexError):
            # 万が一取得失敗した場合はデフォルト（UPM幅）
            hmtx_a.metrics[dest_name] = (font_obj_a["head"].unitsPerEm, 0)

        # 3. cmap の更新：16bit Overflow (U+FFFF超え) 対策
        for table in font_obj_a["cmap"].tables:
            # Format 4 (16bit) の場合は U+FFFF 以下のみ書き込む
            if table.format == 4:
                if code <= 0xFFFF:
                    table.cmap[code] = dest_name
            else:
                # Format 12 (32bit) などは全て書き込む
                table.cmap[code] = dest_name

        # 4. オーダーリストへの追加
        if dest_name not in existing_glyph_names:
            new_glyph_order.append(dest_name)
            existing_glyph_names.add(dest_name)

    # --- Phase 4: 最終同期 (物理的抹殺版) ---
    # print("--- Final Phase: Enforcing Table Consistency ---")

    # 1. グリフ順序を一旦確定させる
    font_obj_a.setGlyphOrder(new_glyph_order)
    final_order = font_obj_a.getGlyphOrder()

    # 2. hmtxテーブルを直接操作
    hmtx_table = font_obj_a["hmtx"]
    current_metrics = hmtx_table.metrics

    # 新しいデータセットを準備
    temp_metrics = {}
    default_val = (font_obj_a["head"].unitsPerEm, 0)
    for name in final_order:
        temp_metrics[name] = current_metrics.get(name, default_val)

    # 【ここが重要】辞書オブジェクトを差し替えるのではなく、中身を直接入れ替える
    current_metrics.clear()
    current_metrics.update(temp_metrics)

    # 3. ついでに vmtx (縦書き用メトリクス) がある場合も同様に処理（エラー防止）
    if "vmtx" in font_obj_a:
        vmtx_table = font_obj_a["vmtx"]
        v_metrics = vmtx_table.metrics
        temp_v_metrics = {}
        for name in final_order:
            temp_v_metrics[name] = v_metrics.get(name, (default_val[0], 0))
        v_metrics.clear()
        v_metrics.update(temp_v_metrics)

    # print(f"Successfully merged! Total glyphs: {len(final_order)}")
    return font_obj_a


def remove_specific_placeholder(font_obj: TTFont, target_w=350, target_h=350) -> TTFont:
    """
    特定のサイズ(350x350)を持つ『●』っぽいゴミデータを削除する。
    ただし、句読点などの重要な文字は保護する。
    """
    glyf_table = font_obj["glyf"]
    cmap = font_obj.getBestCmap()
    # 保護リスト: 句読点、中黒、読点など（Unicodeで指定）
    protected_codes = {0x3001, 0x3002, 0x30FB, 0x002E, 0x00B7}

    # 逆引きマップ（名前からコードを特定するため）
    name_to_code = {name: code for code, name in cmap.items()}

    removed_count = 0
    for name in font_obj.getGlyphOrder():
        if name not in glyf_table:
            continue

        g = glyf_table[name]
        if hasattr(g, "xMax"):
            w = g.xMax - g.xMin
            h = g.yMax - g.yMin

            # 条件: サイズが350x350で、かつ保護リストに入っていない
            if w == target_w and h == target_h:
                code = name_to_code.get(name)
                if code not in protected_codes:
                    # グリフの中身を空にする（輪郭データを消去）
                    g.numberOfContours = 0
                    if hasattr(g, "data"):
                        del g.data
                    removed_count += 1

    if removed_count > 0:
        # print(f"Removed {removed_count} placeholder glyphs ({target_w}x{target_h}).")
        pass

    return font_obj


def remove_hinting(font_obj: TTFont) -> TTFont:
    """
    フォントからヒンティング関連のテーブルを削除し、
    スケーリングによる表示の乱れを防止する。
    """
    # 削除対象のテーブル（ヒンティング、プログラム、ガスプ等）
    hinting_tables = [
        "gasp",  # Grid-fitting and Scan-conversion Procedure
        "prep",  # Control Value Program
        "fpgm",  # Font Program
        "cvt ",  # Control Value Table
        "hdmx",  # Horizontal Device Metrics (ピクセル単位の幅データ)
        "LTSH",  # Linear Threshold table
    ]

    removed = []
    for tag in hinting_tables:
        if tag in font_obj:
            del font_obj[tag]
            removed.append(tag)

    # glyfテーブル内の各グリフの命令データ(instructions)も空にする
    if "glyf" in font_obj:
        for glyph in font_obj["glyf"].glyphs.values():
            if hasattr(glyph, "program"):
                glyph.program = None

    if removed:
        # print(f"Removed hinting tables: {', '.join(removed)}")
        pass

    # print("Glyph instructions cleared.")

    return font_obj


if __name__ == "__main__":
    main()
