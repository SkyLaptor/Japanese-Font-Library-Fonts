from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph
from otf2ttf.cli import otf_to_ttf

from utils import is_otf
from utils.inspector import get_average_size, get_empty_glyphs
from utils.models import SubsetResult
from utils.modifier import set_metrics, transform_glyphs


def create_subset(font_obj: TTFont, subset_chars: str) -> SubsetResult:
    """
    # フォントとサブセット文字列を用いてサブセットフォントを作成する

    :param font_obj: フォントオブジェクト
    :type font_obj: TTFont
    :param subset_chars: サブセット文字列
    :type subset_chars: str
    :return: サブセット作成結果
    :rtype: SubsetResult
    """
    cmap = font_obj.getBestCmap()
    empty_glyphs = get_empty_glyphs(font_obj)

    input_char_set = set(subset_chars)
    keep_glyphs = {".notdef"}

    # 欠落文字を記録するためのリスト
    missing_chars = []

    for char in input_char_set:
        code = ord(char)
        if code in cmap:
            gname = cmap[code]
            if gname not in empty_glyphs:
                # 存在する、かつ中身がある場合のみ採用
                keep_glyphs.add(gname)
            else:
                # 中身が空だったので「欠落」扱いにする
                missing_chars.append(char)
        else:
            # そもそもフォントにない
            missing_chars.append(char)

    # サブセッタの設定と実行
    options = subset.Options()
    options.layout_features = ["*"]  # OpenType機能（合字、カーニング等）を維持
    options.name_IDs = ["*"]  # フォント名や著作権情報をすべて維持
    options.notdef_outline = True  # .notdef（豆腐）の形を維持
    options.glyph_names = True  # グリフ名を維持（デバッグしやすくなる）
    options.legacy_kern = True  # 古い形式のカーニングも維持
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(glyphs=list(keep_glyphs))

    # サブセット処理の適用 (インプレース書き換え)
    subsetter.subset(font_obj)

    # リストをソートしてレポートの可読性向上
    non_existed_glyphs = "".join(sorted(missing_chars))

    return SubsetResult(font_obj=font_obj, non_existed_glyphs=non_existed_glyphs)


def merge_fonts(
    font_obj_a: TTFont, font_obj_b: TTFont, ascent: int, descent: int
) -> TTFont:
    """
    Font A をベースに、足りないグリフを Font B からコピーして結合します。
    (TTF形式同士を想定)
    """
    print("DEBUG: Phase 1 - メトリクスの統一")

    if is_otf(font_obj_a):
        print("AフォントがOTFのため変換します")
        otf_to_ttf(font_obj_a)
    if is_otf(font_obj_b):
        print("BフォントがOTFのため変換します")
        otf_to_ttf(font_obj_b)

    # Font A のメトリクス設定
    a_metrics_res = set_metrics(font_obj_a, ascent, descent)
    font_obj_a = a_metrics_res.font_obj

    # Font B のサイズを A に合わせる (平均サイズ基準)
    size_a = get_average_size(font_obj_a)
    size_b = get_average_size(font_obj_b)
    target_ratio = size_a.avg_h / size_b.avg_h
    font_obj_b = transform_glyphs(font_obj_b, target_ratio)

    print("DEBUG: Phase 2 - グリフの抽出とコピー")
    cmap_a = font_obj_a.getBestCmap()
    cmap_b = font_obj_b.getBestCmap()
    glyf_a = font_obj_a['glyf']
    glyf_b = font_obj_b['glyf']
    hmtx_a = font_obj_a['hmtx']
    hmtx_b = font_obj_b['hmtx']

    # Aに存在せず、Bに存在するUnicodeコードポイントを特定
    missing_codes = sorted(set(cmap_b.keys()) - set(cmap_a.keys()))

    for code in missing_codes:
        gname_b = cmap_b[code]
        # Bのグリフ名がAで既に使われていれば接頭辞をつける
        new_gname = f"b_{gname_b}" if gname_b in font_obj_a.getGlyphOrder() else gname_b

        # 形状と横幅をコピー
        glyf_a[new_gname] = glyf_b[gname_b]
        hmtx_a.metrics[new_gname] = hmtx_b.metrics[gname_b]

        # Font A の文字コード表(cmap)に追加
        cmap_a[code] = new_gname

    print("DEBUG: Phase 3 - 内部データの完全同期")
    # GlyphOrder（名簿）を更新
    new_order = font_obj_a.getGlyphOrder()
    # コピーしたグリフ名が名簿に含まれていない場合があるので、cmapから全抽出して再整理
    all_names = set(new_order) | set(cmap_a.values())
    # 順番を保ちつつ、漏れがないリストを作成
    final_order = []
    seen = set()
    for name in list(new_order) + list(cmap_a.values()):
        if name not in seen:
            final_order.append(name)
            seen.add(name)

    font_obj_a.setGlyphOrder(final_order)

    # 最後のバリデーション：名簿にあるが実体がないグリフ（幽霊）を抹殺
    empty_glyph = Glyph()
    empty_glyph.numberOfContours = 0

    for name in final_order:
        if name not in glyf_a or glyf_a[name] is None:
            glyf_a[name] = empty_glyph
        if name not in hmtx_a.metrics:
            hmtx_a.metrics[name] = (font_obj_a["head"].unitsPerEm, 0)

    print(f"DEBUG: マージ完了 - 合計グリフ数: {len(final_order)}")
    return font_obj_a


# def merge_fonts(
#     font_obj_a: TTFont, font_obj_b: TTFont, ascent: int, descent: int
# ) -> TTFont:
#     """
#     1. A, B 個別にメトリクスを調整
#     2. A, B 個別に不要な空白グリフを掃除
#     3. A に無い文字を B からインデックス参照で確実にコピー
#     4. 保存時の不整合を物理的に排除
#     """

#     # --- Phase 1: 各フォントのコンディションを整える ---
#     # print("Standardizing Font A...")
#     a_result = get_average_size(font_obj_a)  # いろいろする前に測定しておくこと
#     font_obj_a = set_metrics(font_obj_a, ascent, descent)
#     font_obj_a = remove_empty_glyphs(font_obj_a).font_obj

#     # print("Standardizing Font B...")
#     b_result = get_average_size(font_obj_b)  # いろいろする前に測定しておくこと
#     font_obj_b = set_metrics(font_obj_b, ascent, descent)
#     font_obj_b = remove_empty_glyphs(font_obj_b).font_obj

#     # --- Phase 1 内の B 調整セクション ---
#     # print("Calculating scale ratio based on average glyph size...")

#     # print(f"Font A Average Height: {a_result.avg_bbox_size_raw_h:.2f} units")
#     # print(f"Font B Average Height: {b_result.avg_bbox_size_raw_h:.2f} units")

#     # 高さを基準に比率を算出 (例: 850 / 950 = 0.894)
#     target_ratio = a_result.avg_h / b_result.avg_h

#     # 安全策: 異常な倍率にならないようリミッターをかける (任意)
#     # target_ratio = max(0.5, min(target_ratio, 1.2))

#     # print(f"Automated Scaling: Resizing Font B by x{target_ratio:.4f} to match Font A")

#     # スケーリング実行
#     font_obj_b = transform_glyphs(font_obj_b, target_ratio)

#     # --- Phase 2: マージ準備 ---
#     print("--- Phase 2: Merging Glyphs ---")
#     cmap_a = font_obj_a.getBestCmap()
#     cmap_b = font_obj_b.getBestCmap()
#     glyf_a = font_obj_a["glyf"]
#     glyf_b = font_obj_b["glyf"]
#     hmtx_a = font_obj_a["hmtx"]
#     hmtx_b = font_obj_b["hmtx"]

#     # BにあってAにないUnicodeを特定
#     missing_codes = sorted(set(cmap_b.keys()) - set(cmap_a.keys()))

#     if not missing_codes:
#         print("No missing glyphs to fill.")
#         return font_obj_a

#     print(f"Transferring {len(missing_codes)} characters from Font B to Font A...")

#     existing_glyph_names = set(font_obj_a.getGlyphOrder())
#     new_glyph_order = list(font_obj_a.getGlyphOrder())

#     # --- Phase 3: グリフ・メトリクス・cmap のコピー ---
#     for code in missing_codes:
#         original_name = cmap_b[code]

#         if original_name is None:
#             continue

#         # グリフ名が glyf テーブルにあるか確認
#         if original_name not in glyf_b:
#             continue

#         # 名前衝突回避（同じ名前があれば .fallback を付与）
#         dest_name = original_name
#         if dest_name in existing_glyph_names:
#             dest_name = f"{original_name}.fallback"

#         # 1. グリフ形状のコピー
#         glyf_a[dest_name] = glyf_b[original_name]

#         # 2. 横幅(hmtx)のコピー：名前ではなくID(Index)経由で確実に引く
#         try:
#             # Source Han Serif のように内部名と外部名が違う場合への対策
#             gid = font_obj_b.getGlyphID(original_name)
#             real_name_in_b = font_obj_b.getGlyphOrder()[gid]
#             hmtx_a.metrics[dest_name] = hmtx_b.metrics[real_name_in_b]
#         except (KeyError, IndexError):
#             # 万が一取得失敗した場合はデフォルト（UPM幅）
#             hmtx_a.metrics[dest_name] = (font_obj_a["head"].unitsPerEm, 0)

#         # 3. cmap の更新：16bit Overflow (U+FFFF超え) 対策
#         for table in font_obj_a["cmap"].tables:
#             # Format 4 (16bit) の場合は U+FFFF 以下のみ書き込む
#             if table.format == 4:
#                 if code <= 0xFFFF:
#                     table.cmap[code] = dest_name
#             else:
#                 # Format 12 (32bit) などは全て書き込む
#                 table.cmap[code] = dest_name

#         # 4. オーダーリストへの追加
#         if dest_name not in existing_glyph_names:
#             new_glyph_order.append(dest_name)
#             existing_glyph_names.add(dest_name)

#     # --- Phase 4: 最終同期 (物理的抹殺版) ---
#     # print("--- Final Phase: Enforcing Table Consistency ---")

#     # 1. グリフ順序を一旦確定させる
#     font_obj_a.setGlyphOrder(new_glyph_order)
#     final_order = font_obj_a.getGlyphOrder()

#     # 2. hmtxテーブルを直接操作
#     hmtx_table = font_obj_a["hmtx"]
#     current_metrics = hmtx_table.metrics

#     # 新しいデータセットを準備
#     temp_metrics = {}
#     default_val = (font_obj_a["head"].unitsPerEm, 0)
#     for name in final_order:
#         temp_metrics[name] = current_metrics.get(name, default_val)

#     # 【ここが重要】辞書オブジェクトを差し替えるのではなく、中身を直接入れ替える
#     current_metrics.clear()
#     current_metrics.update(temp_metrics)

#     # 3. ついでに vmtx (縦書き用メトリクス) がある場合も同様に処理（エラー防止）
#     if "vmtx" in font_obj_a:
#         vmtx_table = font_obj_a["vmtx"]
#         v_metrics = vmtx_table.metrics
#         temp_v_metrics = {}
#         for name in final_order:
#             temp_v_metrics[name] = v_metrics.get(name, (default_val[0], 0))
#         v_metrics.clear()
#         v_metrics.update(temp_v_metrics)

#     # print(f"Successfully merged! Total glyphs: {len(final_order)}")
#     return font_obj_a
