import os
import shutil
from pathlib import Path

import pytest

import modules.skyrim_builder as skyrim_builder_module
from core.ffdec_wrapper import run_ffdec
from modules.skyrim_builder import (
    swf_export,
    variant_export,
)


def _is_ffdec_operational() -> bool:
    try:
        result = run_ffdec(["-help"], check=False)
        return result.returncode == 0
    except Exception:
        return False


# テスト実行前に、毎回 build/test-env という作業用フォルダを作って実験する設定
@pytest.fixture
def test_workspace(tmp_path):
    # tests/data/test-font から一時フォルダにコピーして、本番データを汚さないようにする
    source_data = Path("tests/data/test-font")
    work_dir = tmp_path / "test-build"
    font_dir = work_dir / "test-font"
    font_dir.mkdir(parents=True)

    for ttf in source_data.glob("*.ttf"):
        shutil.copy(ttf, font_dir)

    return work_dir


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") == "true",
    reason="FFDecを使用する結合テストは重いためCIでは実行しません",
)
@pytest.mark.skipif(
    not _is_ffdec_operational(),
    reason="FFDec実行環境が利用できないためスキップします",
)
def test_swf_internal_name_consistency(test_workspace):
    """
    SWFが生成され、内部名が期待通り(fonts_抜き)になっているかの結合テスト
    """
    # 1. 疑似マージ（テストフォントの末尾に _merged をつけて）
    font_dir = test_workspace / "test-font"
    for ttf in font_dir.glob("*-bold.ttf"):
        shutil.copy(ttf, font_dir / "test-font-bold_merged.ttf")

    # 1.5 フォルダ構成変更対応: サブセットパスを data/subsets 直下へ補正
    original_matrix = skyrim_builder_module.SKYRIM_EXPORT_MATRIX
    patched_matrix = [
        {**item, "path": Path("data/subsets") / Path(item["path"]).name}
        for item in original_matrix
    ]
    skyrim_builder_module.SKYRIM_EXPORT_MATRIX = patched_matrix

    try:
        # 2. Variant展開を実行
        variant_export(str(test_workspace))

        # 3. SWFエクスポートを実行
        swf_export(str(test_workspace))
    finally:
        # 3.5 テスト後に元へ戻す
        skyrim_builder_module.SKYRIM_EXPORT_MATRIX = original_matrix

    # 4. 検証の準備：
    # 命名ルール（medium, normal, full を削る、フォント名以外の-は_に置換する、ベース情報(every,book,handwrite)がつく など）に合わせる。
    # 元が "test-font-bold_merged" で、ここから "_merged" が消え、さらに他も省略されると、期待値はこうなります。
    variant_name = "test-font_bold_every"

    font_dir = test_workspace / "test-font"
    expected_swf = font_dir / f"fonts_{variant_name}.swf"

    # 5. デバッグ表示（失敗した時にファイル一覧が見えるように）
    print(f"\nGenerated files in {font_dir}:")
    for f in font_dir.iterdir():
        print(f"  - {f.name}")

    # 6. 検証: ファイルが存在するか
    assert (
        expected_swf.exists()
    ), f"SWFファイルが見つかりません。期待値: {expected_swf.name} / 生成済み: {[f.name for f in font_dir.iterdir()]}"

    # 7. 検証: SWF内部に書き込まれたフォント名が正しいか（簡易バイナリチェック）
    with open(expected_swf, "rb") as f:
        content = f.read()
        assert (
            variant_name.encode("ascii") in content
        ), f"SWF内部のフォント名が {variant_name} に更新されていない可能性があります"


# @pytest.mark.skipif(
#     os.environ.get("GITHUB_ACTIONS") == "true",
#     reason="結合テストは重いためCIでは実行しません",
# )
# def test_run_merge_font_consistency(test_workspace):
#     """
#     マージが実行され、意図した形になっているか
#     """
#     # 1. 疑似的な事前最適化（テストフォントの末尾に _premerged をつける）
#     src_csv = Path("tests/data/test_merge_conf.csv")
#     merge_conf = test_workspace / "test_merge_conf.csv"
#     shutil.copy(src_csv, merge_conf)
#     font_dir1 = test_workspace / "test-font"
#     font_dir2 = test_workspace / "test-font2"
#     for ttf1 in font_dir1.glob("*-medium.ttf"):
#         shutil.copy(ttf1, font_dir1 / "test-font_premerge.ttf")
#     for ttf2 in font_dir2.glob("*.ttf"):
#         shutil.copy(ttf2, font_dir2 / "test-font2_premerge.ttf")

#     # 2. マージを実行
#     merge_font(str(test_workspace), merge_conf=merge_conf, debug=True)

#     # 3. 検証の準備：
#     marged_name1 = (
#         "test-font_merged.ttf"  # font1とfont2をマージしてこれに出力するとCSVに記載。
#     )
#     marged_name2 = (
#         "test-font2_merged.ttf"  # font2をコピーしてこれに出力するとCSVに記載。
#     )

#     expected_ttf1 = font_dir1 / marged_name1
#     expected_ttf2 = font_dir2 / marged_name2

#     # 6. 検証: ファイルが存在するか
#     assert (
#         expected_ttf1.exists()
#     ), f"マージ済TTFファイルが見つかりません。期待値: {expected_ttf1.name} / フォルダの中: {[f.name for f in font_dir1.iterdir()]}"
#     assert (
#         expected_ttf2.exists()
#     ), f"コピー済TTFファイルが見つかりません。期待値: {expected_ttf2.name} / フォルダの中: {[f.name for f in font_dir2.iterdir()]}"
