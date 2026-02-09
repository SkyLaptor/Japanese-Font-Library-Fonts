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
    subset_glyphs_path: str,
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
        return

    elif action == "adjust_font_metrics":
        suffix = "_metrics_adjusted"
        font_obj = adjust_font_metrics(font_obj, 880, -144)

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
            f"Invalid metrics: Ascent({ascent}) + |Descent({descent})| = UPM({upm}). "
            f"UPM must be a multiple of 8."
        )

    # 2. UPMが異なる場合のみ、グリフ自体のサイズを調整
    if old_upm != new_upm:
        scale = new_upm / old_upm
        print(f"Resizing glyphs: {old_upm} -> {new_upm} (scale: {scale:.4f})")
        # 以前作成した resize_glyphs を呼び出し (引数は dx=0, dy=0 を想定)
        # ※resize_glyphs(font_obj, scale_x, scale_y, dx, dy) の形式に合わせてください
        resize_glyphs(font_obj, scale)
    else:
        print(f"UPM already matches {new_upm}. Skipping glyph resize.")

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

    print(f"Metrics adjusted: UPM={new_upm} (Ascent:{ascent}, Descent:{descent})")
    return font_obj


# TODO: フォントメトリクスの修正


# TODO: グリフの太さを変更する

# TODO: グリフの上下位置を変更する

# TODO: 黒ぽちょグリフを消す

# TODO: フォント同士を結合する

# TODO: サブセットを作る

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
            "export_glyph_list",
            "create_subset",
            "adjust_font_metrics",
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
        subset_glyphs_path=args.subset,
        ascent=args.ascent,
        descent=args.descent,
        scale_size=args.scale_size,
        scale_width=args.scale_width,
        weight_offset=args.weight_offset,
        shift_height=args.shift_height,
        action=args.action,
    )
