import argparse
import os
import sys
from dataclasses import dataclass
from fontTools import subset
from fontTools.ttLib import TTFont, newTable
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen

# --- 設定：一般的に空白として扱われる（削除してはいけない）グリフ ---
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


def main(action: str, input_font_path: str, output_font_path: str, **kwargs) -> None:
    # TODO: あとでちゃんとしたPyDoc
    if not input_font_path or not os.path.exists(input_font_path):
        raise FileNotFoundError(
            f"入力されたファイルが正しくありません。: {input_font_path}"
        )

    font = TTFont(input_font_path)
    suffix = ""

    if action == "print_font_info":
        print_font_info(font)
        return

    elif action == "convert_otf_to_ttf":
        font = convert_otf_to_ttf(font)

    elif action == "clean_empty_glyphs":
        result = clean_empty_glyphs(font)
        print(
            f"不正な空白グリフの消去が完了しました。総グリフ数:{len(result.all_glyphs)}, 削除グリフ数:{len(result.removed_glyphs)}, 残グリフ数:{len(result.all_glyphs) - len(result.removed_glyphs)}"
        )
        suffix = "_emptyclean"
        font = result.font_obj

    elif action == "anonymize_font_info":
        suffix = "_anonymized"
        font = anonymize_font_info(font)

    # --- 2. 出力パスの自動生成 ---
    if not output_font_path:
        # TODO: 入力ファイルがOTFなら出力前にTTF変換を行う。
        # パスを「ディレクトリ」「ファイル名」「拡張子」に分解
        base_dir = "build"
        os.makedirs(base_dir, exist_ok=True)  # buildフォルダがなければ作成

        file_name = os.path.basename(input_font_path)  # 例: "font.otf"
        name_without_ext = os.path.splitext(file_name)[0]  # 例: "font"

        # 形式はTTFに固定
        output_font_path = os.path.join(base_dir, f"{name_without_ext}{suffix}.ttf")

    font.save(output_font_path)
    print(f"保存完了: {output_font_path}")


def print_font_info(font_obj: TTFont):
    """現在のフォント情報を表示する"""
    # TODO: あとでちゃんとしたPyDoc
    head = font_obj["head"]
    hhea = font_obj["hhea"]
    os2 = font_obj["OS/2"]

    print(f"Glyph count: {len(font_obj.getGlyphOrder())}")

    print(f"--- General ---")
    print(f"Units Per Em (UPM): {head.unitsPerEm}")

    print(f"--- OS/2 Table (Windows & Typo) ---")
    # Clipping Metrics (Windowsでの表示範囲)
    print(f"WinAscent:          {os2.usWinAscent}")
    print(f"WinDescent:         {os2.usWinDescent}")
    # Typo Metrics (多くのアプリでの行間基準)
    print(f"TypoAscender:       {os2.sTypoAscender}")
    print(f"TypoDescender:      {os2.sTypoDescender}")
    print(f"TypoLineGap:        {os2.sTypoLineGap}")
    # fsSelectionのビットチェック（後述の重要なフラグ）
    print(f"USE_TYPO_METRICS:   {bool(os2.fsSelection & 0b10000000)}")

    print(f"--- hhea Table (Mac/iOS) ---")
    print(f"hhea Ascender:      {hhea.ascender}")
    print(f"hhea Descender:     {hhea.descender}")
    print(f"hhea LineGap:       {hhea.lineGap}")

    print(f"{'ID':<5} | {'Name Key':<20} | {'Value'}")
    print("-" * 60)

    name_table = font_obj["name"]

    # 主要なNameIDの定義
    target_ids = {
        0: "Copyright",
        1: "Family Name",
        2: "Subfamily Name",
        3: "Unique ID",
        4: "Full Name",
        5: "Version",
        6: "PostScript Name",
        7: "Trademark",
        8: "Manufacturer",
        9: "Designer",
        10: "Description",
        11: "Vendor URL",
        12: "Designer URL",
        13: "License",
        14: "License URL",
        16: "Typog. Family",
        17: "Typog. Subfamily",
    }

    # 取得できた情報を表示
    for name_id, label in target_ids.items():
        # 指定したIDのレコードを抽出
        record = (
            name_table.getName(name_id, 3, 1, 0x411)
            or name_table.getName(name_id, 3, 1, 0x409)
            or name_table.getName(name_id, 1, 0, 0)
        )

        # レコードが存在すれば表示（デコードして文字列にする）
        if record:
            try:
                value = record.toUnicode()
            except Exception:
                value = str(record.string)
            print(f"{name_id:<5} | {label:<20} | {value}")
        else:
            print(f"{name_id:<5} | {label:<20} | (Not Found)")


def convert_otf_to_ttf(font_obj: TTFont):
    """
    極力テーブルを破壊せず、アウトライン形式だけをTTFへ変換する
    """
    if "CFF " not in font_obj and "CFF2" not in font_obj:
        return font_obj

    print("ACTION: シンプル変換を開始します...")

    # 1. アウトラインの2次ベジェ化
    glyph_set = font_obj.getGlyphSet()
    glyph_names = font_obj.getGlyphOrder()  # 元の順序を取得

    new_glyf = newTable("glyf")
    new_glyf.glyphs = {}
    new_glyf.glyphOrder = (
        glyph_names  # ここが抜けていたため AttributeError になりました
    )

    # --- シンプル変換のループ部分 ---
    for name in glyph_names:
        tt_pen = TTGlyphPen(glyph_set)
        cu2qu_pen = Cu2QuPen(tt_pen, max_err=1.0, reverse_direction=True)
        glyph_set[name].draw(cu2qu_pen)

        g = tt_pen.glyph()
        # これが重要！各グリフの xMin, xMax, yMin, yMax を計算してセットします
        g.recalcBounds(new_glyf)

        new_glyf.glyphs[name] = g

    font_obj["glyf"] = new_glyf
    font_obj["loca"] = newTable("loca")

    # 2. 形式をOTFからTTFへ変更
    font_obj.sfntVersion = "\x00\x01\x00\x00"

    # 3. CFFテーブルの削除 (これがないとTTFとして認識されません)
    for tag in ["CFF ", "CFF2", "VORG"]:
        if tag in font_obj:
            del font_obj[tag]

    # 5. すべてのテーブルの再計算 (fontToolsに整合性を取らせる)
    for table in font_obj.tables.values():
        if hasattr(table, "recalc"):
            table.recalc(font_obj)

    print("SUCCESS: シンプル変換が完了しました。")
    return font_obj


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
    """フォントの名称情報をクリアまたはダミーに置き換える"""
    # TODO: あとでちゃんとしたPyDoc
    name_table = font_obj["name"]
    for record in name_table.names:
        # 著作権(0), デザイナー名(9), 説明(10) などを空にする
        if record.nameID in [0, 9, 10, 11, 12]:
            record.string = "".encode(record.getEncoding())
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
            "print_font_metrics",
            "convert_otf_to_ttf",
            "clean_empty_glyphs",
            "anonymize_font_info",
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
        ratio_total=args.scale_size,
        ratio_width=args.scale_width,
        weight_offset=args.weight_offset,
        shift_height=args.shift_height,
        action=args.action,
    )
