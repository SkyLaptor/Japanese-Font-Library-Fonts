import tempfile
from pathlib import Path

from fontTools.ttLib import TTFont

from core.fontforge_wrapper import ff_merge_fonts
from modules.get_average_size import get_average_size


def _calculate_auto_scale(
    base_path: str, interpolation_path: str
) -> tuple[float, float, str]:
    """
    ベースと補完側のフォントを読み込み、平均サイズから自動スケーリング倍率を計算する
    """
    with TTFont(base_path) as base_font, TTFont(interpolation_path) as interp_font:
        base_avg = get_average_size(base_font)
        target_avg = get_average_size(interp_font)

    if target_avg.count and target_avg.avg_w and target_avg.avg_h:
        scale_x = base_avg.avg_w / target_avg.avg_w
        scale_y = base_avg.avg_h / target_avg.avg_h
        name = "CJK"
    elif target_avg.count_latin and target_avg.avg_w_latin and target_avg.avg_h_latin:
        scale_x = base_avg.avg_w_latin / target_avg.avg_w_latin
        scale_y = base_avg.avg_h_latin / target_avg.avg_h_latin
        name = "Latin"
    else:
        scale_x, scale_y, name = 1.0, 1.0, "Fallback"

    return scale_x, scale_y, name


def action_merge_font(
    base_path: str,
    interpolation_path: str,
    output_path: str,
    scale_width: float = 1.0,
    scale_height: float = 1.0,
    debug: bool = False,
    **kwargs,
):
    """
    レシピから呼び出されるメインエントリ。
    FontForge エンジンを使用してフォントをマージします。
    """
    # 1. 自動スケーリング倍率の計算
    auto_x, auto_y, baseline = _calculate_auto_scale(base_path, interpolation_path)

    # ユーザー指定の倍率を乗算
    final_scale_x = auto_x * scale_width
    final_scale_y = auto_y * scale_height

    if debug:
        print(
            f"[action_merge_font] AutoScale({baseline}): x={auto_x:.3f}, y={auto_y:.3f}"
        )
        print(
            f"[action_merge_font] FinalScale: x={final_scale_x:.3f}, y={final_scale_y:.3f}"
        )

    # 2. FontForge ラッパーの呼び出し
    # FontForge側で「不足Unicodeの特定」「スケーリング」「32bit loca書き出し」を一括で行います
    try:
        result = ff_merge_fonts(
            base_path=base_path,
            interp_path=interpolation_path,
            output_path=output_path,
            scale_x=final_scale_x,
            scale_y=final_scale_y,
        )

        if debug and result.stdout:
            print(f"--- FontForge Output ---\n{result.stdout}")

        print(f"フォントを保存しました: {output_path}")

    except Exception as e:
        print(f"❌ マージ中にエラーが発生しました: {e}")
        raise


# 以下、古い関数の掃除
def merge_font(*args, **kwargs):
    # 以前のコードがこの関数を期待している場合のエラー回避用
    # 実体は action_merge_font に移行したため、直接呼ぶべきではない
    raise NotImplementedError(
        "merge_font は廃止されました。action_merge_font を使用してください。"
    )


def merge_font_objects(
    base_font_obj: TTFont, interpolation_font_obj: TTFont, **kwargs
) -> TTFont:
    """
    batch_processorから送られてきた『メモリ上のフォント』を
    一時ファイルに書き出して、FontForgeエンジンに処理させます。
    """
    debug = kwargs.get("debug", False)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_base = Path(tmpdir) / "base.ttf"
        tmp_interp = Path(tmpdir) / "interp.ttf"
        tmp_out = Path(tmpdir) / "merged.ttf"

        # 1. 今のメモリ状態を一旦ファイルにする
        base_font_obj.save(tmp_base)
        interpolation_font_obj.save(tmp_interp)

        if debug:
            print(
                f"[Bridge] FontForgeマージ開始 - 一時ファイル: {tmp_base}, {tmp_interp}"
            )

        # 2. FontForgeを呼び出す (ff_merge_fonts は core.fontforge_wrapper から)
        # この関数はフォントオブジェクトを返したりはしないため、出力パスからTTFontに再ロードする必要があります
        ff_merge_fonts(
            base_path=str(tmp_base),
            interp_path=str(tmp_interp),
            output_path=str(tmp_out),
        )

        # 【重要】マージ済みのファイルを読み込み直して、新しいオブジェクトとして返す
        if Path(tmp_out).exists():
            if debug:
                print(f"[Bridge] マージ済みファイルを再ロードします: {tmp_out}")
            # fontToolsオブジェクトとして再構成
            return TTFont(str(tmp_out))
        else:
            print("[Bridge] 警告: マージ出力ファイルが見つかりません。")
            return base_font_obj
