import shutil
from pathlib import Path

import pytest

from apps.skyrim.builder import run_batch_swf_export, run_batch_variant_export


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


def test_swf_internal_name_consistency(test_workspace):
    """
    SWFが生成され、内部名が期待通り(fonts_抜き)になっているかの結合テスト
    """
    # 1. 疑似マージ（テストフォントを merged という名前にリネームして準備）
    font_dir = test_workspace / "test-font"
    for ttf in font_dir.glob("*-bold.ttf"):
        shutil.copy(ttf, font_dir / "test-font-bold-merged.ttf")

    # 2. Variant展開を実行
    run_batch_variant_export(str(test_workspace))

    # 3. SWFエクスポートを実行
    run_batch_swf_export(str(test_workspace))

    # 4. 検証の準備：まず「期待する名前」を定義する（★ここが重要！）
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
