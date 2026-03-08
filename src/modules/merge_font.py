import traceback
from copy import deepcopy

from fontTools.ttLib import TTFont

from utils.file_io import save_font


def merge_font(
    base_font: TTFont, interp_font: TTFont, *, debug: bool = False
) -> TTFont:
    """
    ピュアPython(fontToolsのみ)で、base_fontに不足しているUnicodeのグリフを
    interp_fontから必要分だけコピーして統合する。
    """
    try:
        if debug:
            print(
                f"[DEBUG:v2] マージ開始: Base(Glyphs={len(base_font.getGlyphOrder())}) <- Interp(Glyphs={len(interp_font.getGlyphOrder())})"
            )

        # 1) サポート判定: TrueType(glyf)のみ正式対応。
        has_glyf = "glyf" in base_font and "glyf" in interp_font
        if not has_glyf:
            raise NotImplementedError(
                "merge_font_objects_v2: 現在はTrueType(glyf)フォント間のマージのみ対応しています。"
            )

        # 2) 参照用ショートカット
        base_glyf = base_font["glyf"]
        interp_glyf = interp_font["glyf"]
        base_hmtx = base_font["hmtx"]
        interp_hmtx = interp_font["hmtx"]

        has_base_vmtx = "vmtx" in base_font
        has_interp_vmtx = "vmtx" in interp_font
        base_vmtx = base_font["vmtx"] if has_base_vmtx else None
        interp_vmtx = interp_font["vmtx"] if has_interp_vmtx else None
        base_vhea = base_font["vhea"] if "vhea" in base_font else None

        # 3) cmap差分の抽出
        interp_best = interp_font.getBestCmap() or {}
        base_best = base_font.getBestCmap() or {}
        missing_codepoints: list[int] = [
            cp for cp in interp_best.keys() if cp not in base_best
        ]

        if debug:
            print(f"[DEBUG:v2] 不足Unicode数: {len(missing_codepoints)}")
        if not missing_codepoints:
            return base_font

        # 4) 便利関数群 (最適化)
        base_glyph_order = list(base_font.getGlyphOrder())
        base_glyph_set = set(base_glyph_order)
        rename_map: dict[str, str] = {}

        def _unique_name(desired: str) -> str:
            if desired not in base_glyph_set and desired not in rename_map.values():
                return desired
            suffix = ".interp"
            candidate = desired + suffix
            idx = 2
            while candidate in base_glyph_set or candidate in rename_map.values():
                candidate = f"{desired}{suffix}{idx}"
                idx += 1
            return candidate

        def _iter_unicode_cmap_subtables(tt: TTFont):
            cmap_tbl = tt["cmap"]
            for st in cmap_tbl.tables:
                try:
                    is_uni = st.isUnicode()
                except Exception:
                    is_uni = False
                if is_uni or (
                    (st.platformID == 0)
                    or (st.platformID == 3 and st.platEncID in (1, 10))
                ):
                    yield st

        def _copy_glyph_with_deps(orig_name: str) -> str:
            if orig_name in rename_map:
                return rename_map[orig_name]
            if orig_name in base_glyph_set:
                rename_map[orig_name] = orig_name
                return orig_name
            if orig_name not in interp_glyf.glyphs:
                rename_map[orig_name] = orig_name
                return orig_name

            src_g = interp_glyf[orig_name]
            if hasattr(src_g, "isComposite") and src_g.isComposite():
                for comp in src_g.components:
                    comp_new = _copy_glyph_with_deps(comp.glyphName)
                    comp.glyphName = comp_new

            dst_g = deepcopy(src_g)
            new_name = _unique_name(orig_name)
            rename_map[orig_name] = new_name

            # 追加
            base_glyf[new_name] = dst_g
            base_glyph_order.append(new_name)
            base_glyph_set.add(new_name)

            if orig_name in interp_hmtx.metrics:
                base_hmtx.metrics[new_name] = tuple(interp_hmtx.metrics[orig_name])
            else:
                base_hmtx.metrics[new_name] = (0, 0)

            if has_base_vmtx:
                if (
                    has_interp_vmtx and orig_name in interp_vmtx.metrics
                ):  # type: ignore[union-attr]
                    base_vmtx.metrics[new_name] = tuple(interp_vmtx.metrics[orig_name])  # type: ignore[index, union-attr]
                else:
                    adv_h = (
                        int(base_vhea.ascent) - int(base_vhea.descent)
                        if base_vhea
                        else 0
                    )
                    base_vmtx.metrics[new_name] = (adv_h, 0)  # type: ignore[union-attr]

            return new_name

        # 5) 実際のコピー
        for i, cp in enumerate(missing_codepoints):
            orig_name = interp_best.get(cp)
            if orig_name:
                _copy_glyph_with_deps(orig_name)
            if debug and i > 0 and i % 1000 == 0:
                print(
                    f"[DEBUG:v2] 進捗: {i}/{len(missing_codepoints)} グリフコピー済み"
                )

        # 5.5) cmap Format 12 (UCS-4) の用意: base に無く、かつ 0xFFFF を超えるコードがある場合は新規作成
        try:
            has_fmt12 = any(
                getattr(st, "format", None) == 12 for st in base_font["cmap"].tables
            )
        except Exception:
            has_fmt12 = False
        if (not has_fmt12) and any(cp > 0xFFFF for cp in missing_codepoints):
            try:
                from fontTools.ttLib.tables._c_m_a_p import cmap_format_12

                new_st = cmap_format_12(12)
                new_st.platformID = 3  # Windows
                new_st.platEncID = 10  # UCS-4
                new_st.language = 0
                # 既存の全マッピングを全サブテーブルから集約して引き継ぐ（getBestCmapだけに頼らない）
                existing_cmap = {}
                for st in base_font["cmap"].tables:
                    if hasattr(st, "cmap") and isinstance(st.cmap, dict):
                        existing_cmap.update(st.cmap)

                new_st.cmap = deepcopy(existing_cmap)
                base_font["cmap"].tables.append(new_st)
                if debug:
                    print("[DEBUG:v2] 追加: cmap Format 12 (platform=3, enc=10)")
            except Exception:
                # 生成失敗は致命ではないが、サロゲート文字が消える可能性がある
                print("[WARN:v2] cmap Format 12 の生成に失敗しました。")

        # グリフ順序確定
        base_font.setGlyphOrder(base_glyph_order)

        # 6) テーブル整合性更新
        if debug:
            print("[DEBUG:v2] テーブル整合性更新中...")
        if "maxp" in base_font:
            base_font["maxp"].numGlyphs = len(base_glyph_order)
            if debug:
                print(f"[DEBUG:v2] maxp.numGlyphs = {base_font['maxp'].numGlyphs}")

        if "hhea" in base_font:
            base_font["hhea"].numberOfHMetrics = len(base_hmtx.metrics)
            if debug:
                print(
                    f"[DEBUG:v2] hhea.numberOfHMetrics = {base_font['hhea'].numberOfHMetrics}"
                )

        if has_base_vmtx and "vhea" in base_font:
            base_font["vhea"].numberOfVMetrics = len(base_vmtx.metrics)  # type: ignore[union-attr]
            if debug:
                print(
                    f"[DEBUG:v2] vhea.numberOfVMetrics = {base_font['vhea'].numberOfVMetrics}"
                )

        # 6.1) Loca 32bit 化でオーバーフローを防止
        if "head" in base_font:
            base_font["head"].indexToLocFormat = 1  # 0: short, 1: long(32bit)

        # 6.2) OS/2 の整合 (必要に応じてクリップ)
        if "OS/2" in base_font:
            try:
                os2 = base_font["OS/2"]
                if hasattr(os2, "usMaxContext") and os2.usMaxContext is not None:
                    os2.usMaxContext = max(0, min(int(os2.usMaxContext), 0xFFFF))
                # BMPの範囲外に出ないように念のためクリップ
                if (
                    hasattr(os2, "usFirstCharIndex")
                    and os2.usFirstCharIndex is not None
                ):
                    os2.usFirstCharIndex = max(
                        0, min(int(os2.usFirstCharIndex), 0xFFFF)
                    )
                if hasattr(os2, "usLastCharIndex") and os2.usLastCharIndex is not None:
                    os2.usLastCharIndex = max(0, min(int(os2.usLastCharIndex), 0xFFFF))
            except Exception:
                # クリップ失敗は致命ではないため握りつぶす
                pass

        # cmap更新（全サブテーブルを同期。Format 4 には 0xFFFF 超を入れない）
        for cp in missing_codepoints:
            orig_name = interp_best.get(cp)
            new_name = rename_map.get(orig_name) if orig_name else None
            if new_name:
                for st in getattr(base_font["cmap"], "tables", []):
                    try:
                        fmt = getattr(st, "format", None)
                    except Exception:
                        fmt = None
                    # 書き込み先が辞書でない(例: format 14など)場合はスキップ
                    if not hasattr(st, "cmap") or not isinstance(
                        getattr(st, "cmap", None), dict
                    ):
                        continue
                    if fmt == 4 and cp > 0xFFFF:
                        continue
                    st.cmap[cp] = new_name

        # 6.3) 内部キャッシュを削除して、次の getBestCmap() で確実に再評価させる
        if hasattr(base_font["cmap"], "unicodeData"):
            del base_font["cmap"].unicodeData

        try:
            _ = base_font.getBestCmap()
        except Exception:
            pass

        if debug:
            print(f"[DEBUG:v2] マージ完了 (最終グリフ数: {len(base_glyph_order)})")
        return base_font

    except Exception:
        print("[ERROR:v2] マージ中に例外が発生しました:")
        traceback.print_exc()
        raise


def action_merge_font(
    *, base_path: str, interpolation_path: str, output_path: str, debug: bool = False
) -> None:
    """
    単体マージ実行アクション。

    - `base_path`: ベースとなるTTFパス
    - `interpolation_path`: 取り込み元TTFパス
    - `output_path`: 出力先パス
    - `debug`: デバッグ出力の有無
    """
    # フォントを開いてマージし、保存するだけの薄いラッパー
    with TTFont(str(base_path)) as base_font, TTFont(
        str(interpolation_path)
    ) as interp_font:
        merged = merge_font(base_font=base_font, interp_font=interp_font, debug=debug)
        save_font(
            font_obj=merged, input_path=str(base_path), output_path=str(output_path)
        )
