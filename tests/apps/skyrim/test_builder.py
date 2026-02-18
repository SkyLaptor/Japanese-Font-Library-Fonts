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

    # 4. 検証: 特定のバリエーションが生成されているか
    expected_swf = font_dir / "fonts_test-font_bold_every.swf"
    assert expected_swf.exists(), "SWFファイルが生成されていません"

    # ログ等で internal_font_name が正しいか確認できればベストですが
    # まずは「エラーなく完走すること」を確認します
