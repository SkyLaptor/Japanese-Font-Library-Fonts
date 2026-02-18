import time

import pytest

from src.utils.modifier.anonymize_info import EPOCH_DIFF, anonymize_info

# あなたの提示した create_mock_font フィクスチャがここにある前提です


def test_anonymize_info_logic(create_mock_font):
    # 1. 汚れた（情報が詰まった）モックフォントを作成
    font = create_mock_font()

    # 追加で消去対象のレコード（著作権など）を手動で入れる
    from fontTools.ttLib.tables._n_a_m_e import NameRecord

    name_table = font['name']

    extra_record = NameRecord()
    extra_record.nameID = 0  # Copyright
    extra_record.platformID = 3
    extra_record.platEncID = 1
    extra_record.langID = 0x409
    extra_record.string = "Copyright (c) 2024 Tester".encode("utf-16-be")
    name_table.names.append(extra_record)

    new_name = "MyShadowFont"

    # 2. 実行
    cleaned_font = anonymize_info(font, font_name=new_name, debug=True)

    # 3. 検証
    # 名前が書き換わっているか
    # ID 1 (Family Name) を取得して確認
    family_name_record = cleaned_font['name'].getName(
        nameID=1, platformID=3, platEncID=1
    )
    assert family_name_record.toUnicode() == new_name

    # 不要なID(0: Copyright)が削除されているか
    all_ids = [r.nameID for r in cleaned_font['name'].names]
    assert 0 not in all_ids

    # OS/2 ベンダーID
    assert cleaned_font['OS/2'].achVendID == "NONE"

    # 日付の更新（誤差5秒以内）
    now_expected = int(time.time()) + EPOCH_DIFF
    assert abs(cleaned_font['head'].modified - now_expected) < 5


def test_anonymize_info_invalid_name(create_mock_font):
    font = create_mock_font()

    # 不正な名前で例外が出るか
    with pytest.raises(ValueError, match="フォント名に空白や記号類は使用できません。"):
        anonymize_info(font, font_name="Bad Name")
