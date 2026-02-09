import argparse
import io
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
BASE_UPM = 1024


def main(
    action: str,
    input_font_path: str,
    output_font_path: str,
    scale_size: float,
    scale_width: float,
    **kwargs,
) -> None:
    # TODO: あとでちゃんとしたPyDoc
    if not input_font_path or not os.path.exists(input_font_path):
        raise FileNotFoundError(
            f"入力されたファイルが正しくありません。: {input_font_path}"
        )

    font_obj = TTFont(input_font_path)

    suffix = ""
    if action == "report_font_info":
        report = report_font_info(font_obj)
        print(report)
        report_path = Path("build") / f"{Path(input_font_path).stem}_info.txt"
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
        result = get_metrics_average(font_obj)
        print("--- Glyph Metrics (BBox) ---")
        print(f"Sample Kanji Count:      {result.count}")
        print(
            f"Avg BBox Size (Raw):     {result.avg_bbox_size_raw_w:.1f} x {result.avg_bbox_size_raw_h:.1f} (font is {result.upm} UPM)"
        )
        print(
            f"Avg BBox Size (Norm):    {result.avg_bbox_size_norm_w:.1f} x {result.avg_bbox_size_norm_h:.1f} (per {BASE_UPM} UPM)"
        )
        return

    elif action == "resize_glyphs":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_resized"
        font_obj = resize_glyphs(font_obj, scale_size)

    elif action == "resize_glyphs_width_only":
        if is_otf(font_obj):
            raise TypeError(
                "本機能はOTFに対応していません。otf2ttfを使用してTTFに変換したものをご利用下さい。"
            )
        suffix = "_resized"
        font_obj = resize_glyphs_width_only(font_obj, scale_width)

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
    if "CFF " in font_obj:
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

    report_print("--- General ---")
    report_print(f"Glyph count: {len(font_obj.getGlyphOrder())}")
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
    """フォントの名称情報を徹底的に匿名化またはダミーに置き換える"""

    # 1. nameテーブルの処理
    name_table = font_obj["name"]
    new_names = []

    # 保持したい、あるいは安全なダミー値の定義
    dummy_str = "Anonymized Font"
    family_name = "Anonymized"

    for record in name_table.names:
        # IDごとの処理
        if record.nameID in [1, 4, 16]:  # Family, Full Name
            record.string = family_name.encode(record.getEncoding())
        elif record.nameID == 2:  # Subfamily (Regularなどは残さないと壊れる場合がある)
            pass
        elif record.nameID == 3:  # Unique ID
            record.string = f"0.000;NONE;{family_name}".encode(record.getEncoding())
        elif record.nameID == 5:  # Version
            record.string = "Version 0.000".encode(record.getEncoding())
        elif record.nameID == 6:  # PostScript Name (重要: スペース不可)
            record.string = "Anonymized-Regular".encode(record.getEncoding())
        else:
            # それ以外（著作権、デザイナー、URL、ライセンス等）はすべて空にする
            record.string = "".encode(record.getEncoding())

    # headテーブルのタイムスタンプを「現在時刻」に更新
    if "head" in font_obj:
        # fontToolsの内部では1904年からの経過秒数(Macエポック)を期待していますが、
        # fontTools自体が time.time() の値を適切に扱ってくれるため
        # int(time.time()) を入れるのが最も確実です。
        now = int(time.time())
        # Appleの基準(1904年)に合わせるためのオフセット加算
        font_obj["head"].created = now + 2082844800
        font_obj["head"].modified = now + 2082844800

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


def get_metrics_average(font_obj: TTFont) -> MetricsStats:
    """漢字の範囲に絞ってBBoxの平均値と対象文字数を取得する"""
    # TODO: doc
    glyf_table = font_obj["glyf"]
    # Unicode -> GlyphName のマッピングを取得
    cmap = font_obj.getBestCmap()

    # デバッグ用に、cmapの中身を少しだけ見てみる
    # all_codes = list(cmap.keys())
    glyph_set = font_obj.getGlyphSet()
    # print(f"DEBUG: First 10 codes in cmap: {all_codes[:10]}")  # 念のため

    total_width = 0
    total_height = 0
    count = 0
    upm = font_obj["head"].unitsPerEm

    # デバッグ：漢字の範囲（0x4E00以降）に何文字あるか強制カウント
    # kanji_in_cmap = [c for c in cmap.keys() if c >= 0x4E00]
    # print(f"DEBUG: Characters >= 0x4E00 count: {len(kanji_in_cmap)}")
    # if len(kanji_in_cmap) > 0:
    #    print(f"DEBUG: Sample Kanji codes: {kanji_in_cmap[:5]}")

    for code, name in cmap.items():
        if 0x4E00 <= code <= 0x9FFF:
            # glyph_set[name] ではなく、直接 glyf テーブルを参照する
            if name in glyf_table:
                g = glyf_table[name]

                # TTFのグリフオブジェクト(g)は xMin などの属性を直接持っている
                if hasattr(g, "xMin"):
                    xMin, yMin, xMax, yMax = g.xMin, g.yMin, g.xMax, g.yMax
                    width = xMax - xMin
                    height = yMax - yMin

                    # じゆちょうフォント等は空白グリフがある可能性があるため、
                    # 少なくともどちらかが0より大きい場合にカウント
                    if width > 0 or height > 0:
                        total_width += width
                        total_height += height
                        count += 1
                else:
                    # 複合グリフなどの場合、座標が即座に取得できないことがある
                    # その場合は glyph_set の getBounds を使う
                    try:
                        bounds = glyph_set[name].getBounds(glyph_set)
                        if bounds:
                            xMin, yMin, xMax, yMax = bounds
                            total_width += xMax - xMin
                            total_height += yMax - yMin
                            count += 1
                    except:
                        continue

    if count == 0:
        print("対象範囲に漢字が見つかりませんでした。")
        return MetricsStats(
            upm=upm,
            count=count,
            avg_bbox_size_raw_w=0.0,
            avg_bbox_size_raw_h=0.0,
            avg_bbox_size_norm_w=0.0,
            avg_bbox_size_norm_h=0.0,
        )

    avg_w = total_width / count
    avg_h = total_height / count

    # 正規化（基準UPM換算）
    norm_w = (avg_w / upm) * BASE_UPM
    norm_h = (avg_h / upm) * BASE_UPM

    return MetricsStats(
        upm=upm,
        count=count,
        avg_bbox_size_raw_w=avg_w,
        avg_bbox_size_raw_h=avg_h,
        avg_bbox_size_norm_w=norm_w,
        avg_bbox_size_norm_h=norm_h,
    )


def resize_glyphs(font_obj: TTFont, target_scale: float) -> TTFont:
    """
    全グリフを指定した倍率でスケーリングし、
    あわせて横送りの幅（hmtx）も調整する
    """
    glyph_set = font_obj.getGlyphSet()
    glyf_table = font_obj["glyf"]
    hmtx_table = font_obj["hmtx"]
    upm = font_obj["head"].unitsPerEm

    # --- 横方向の移動量 (dx) の計算 ---
    # UPMの半分（中心）を基準に、縮小して空いたスペースの半分だけ上に持ち上げる
    # 例: UPM 1000 で target_scale 0.5 なら、(1000 * 0.5) / 2 = 250 だけ右ににずらす
    dx = (upm * (1.0 - target_scale)) / 2
    # --- 縦方向の移動量 (dy) の計算 ---
    # UPMの半分（中心）を基準に、縮小して空いたスペースの半分だけ上に持ち上げる
    # 例: UPM 1000 で target_scale 0.5 なら、(1000 * 0.5) / 2 = 250 だけ上にずらす
    dy = (upm * (1.0 - target_scale)) / 2

    for glyph_name in font_obj.getGlyphOrder():

        # 1. 元のグリフを読み込む
        old_glyph = glyph_set[glyph_name]

        # 2. 変形行列の作成
        transformation = (target_scale, 0, 0, target_scale, dx, dy)

        # 3. 新しいグリフデータの作成
        # TTGlyphPen を使い、既存の glyph_set を参照させてコンポーネントを維持する
        tt_pen = TTGlyphPen(glyph_set)
        trans_pen = TransformPen(tt_pen, transformation)

        # 描画（座標変換）を実行
        old_glyph.draw(trans_pen)

        # 4. glyfテーブルの書き換え
        # glyph() メソッドで新しいグリフオブジェクトを生成
        glyf_table[glyph_name] = tt_pen.glyph()

        # # 5. 横送り（アドバンス幅）の調整
        # width, lsb = hmtx_table[glyph_name]
        # hmtx_table[glyph_name] = (
        #     int(round(width * target_scale)),
        #     int(round(lsb * target_scale)),
        # )

        # 5. 横送り（アドバンス幅）の調整
        width, lsb = hmtx_table[glyph_name]

        # 幅そのものもスケールして、隙間を詰める
        new_width = int(round(width * target_scale))

        # LSBは「元々の左余白をスケールしたもの」に「中央寄せの移動量dx」を加える
        new_lsb = int(round(lsb * target_scale + dx))

        hmtx_table[glyph_name] = (new_width, new_lsb)

    # UPMを更新する場合はここで行う
    # font_obj["head"].unitsPerEm = 1024

    return font_obj


def resize_glyphs_width_only(font_obj: TTFont, target_scale: float) -> TTFont:
    """
    全グリフの幅（横方向）だけを指定した倍率でスケーリングする。
    """
    glyph_set = font_obj.getGlyphSet()
    glyf_table = font_obj["glyf"]
    hmtx_table = font_obj["hmtx"]
    upm = font_obj["head"].unitsPerEm

    # --- 横方向の移動量 (dx) の計算 ---
    # UPMの半分（中心）を基準に、縮小して空いたスペースの半分だけ上に持ち上げる
    # 例: UPM 1000 で target_scale 0.5 なら、(1000 * 0.5) / 2 = 250 だけ右ににずらす
    dx = (upm * (1.0 - target_scale)) / 2

    for glyph_name in font_obj.getGlyphOrder():
        # 1. 元のグリフを読み込む
        old_glyph = glyph_set[glyph_name]

        # 2. 変形行列の作成
        transformation = (target_scale, 0, 0, 1.0, dx, 0)  # 高さは変えない

        # 3. 新しいグリフデータの作成
        # TTGlyphPen を使い、既存の glyph_set を参照させてコンポーネントを維持する
        tt_pen = TTGlyphPen(glyph_set)
        trans_pen = TransformPen(tt_pen, transformation)

        # 描画（座標変換）を実行
        old_glyph.draw(trans_pen)

        # 4. glyfテーブルの書き換え
        # glyph() メソッドで新しいグリフオブジェクトを生成
        glyf_table[glyph_name] = tt_pen.glyph()

        # # 5. 横送り（アドバンス幅）の調整
        # width, lsb = hmtx_table[glyph_name]
        # hmtx_table[glyph_name] = (
        #     int(round(width * target_scale)),
        #     int(round(lsb * target_scale)),
        # )

        # 5. 横送り（アドバンス幅）の調整
        width, lsb = hmtx_table[glyph_name]

        # 幅そのものもスケールして、隙間を詰める
        new_width = int(round(width * target_scale))

        # LSBは「元々の左余白をスケールしたもの」に「中央寄せの移動量dx」を加える
        new_lsb = int(round(lsb * target_scale + dx))

        hmtx_table[glyph_name] = (new_width, new_lsb)

    # UPMを更新する場合はここで行う
    # font_obj["head"].unitsPerEm = 1024

    return font_obj


# TODO: フォントメトリクスの修正

# TODO: 任意のサブセット文字列とフォントを比較して、サブセットにない文字は消す

# TODO: 任意のサブセット文字列とフォントを比較して、サブセットに無い文字（不足している文字）を検査する

# TODO: グリフサイズを比率で変更する

# TODO: グリフの横幅を比率で変更する

# TODO: グリフの太さを変更する

# TODO: グリフの上下位置を変更する

# TODO: 黒ぽちょグリフを消す

# TODO: フォント同士を結合する

# 直接実行
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="fontToolsを用いてフォントに対する様々な操作を行うためのライブラリ"
    )

    parser.add_argument("-i", "--input", help="入力元のフォントファイルパス")
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
        help="Ascentの値(units)",
    )
    parser.add_argument(
        "--descent",
        type=int,
        help="Descentの値(units)",
    )
    parser.add_argument("--scale_size", type=float, help="拡大縮小率(1.0=100.0%%)")
    parser.add_argument(
        "--scale_width", type=float, help="横幅の拡大縮小率(1.0=100.0%%)"
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
            "resize_glyphs_width_only",
        ],
        default="print_font_info",
        help="実行する操作(デフォルト: print_font_info)",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    main(
        input_font_path=args.input,
        output_font_path=args.output,
        subset_chars_path=args.subset,
        ascent=args.ascent,
        descent=args.descent,
        scale_size=args.scale_size,
        scale_width=args.scale_width,
        weight_offset=args.weight_offset,
        shift_height=args.shift_height,
        action=args.action,
    )
