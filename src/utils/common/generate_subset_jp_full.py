import argparse
import sys

from const import EXTRA_UNICODES
from utils.common.dprint import dprint
from utils.common.escape_for_validnamechars import escape_for_validnamechars
from utils.common.save_text import save_text


def main():
    parser = argparse.ArgumentParser(
        description="日本語圏向けフルサブセットテキストを生成する"
    )

    parser.add_argument(
        "output_path",
        type=str,
        help="サブセットテキストの書き出し先",
    )
    parser.add_argument(
        "--validnamechars_escape",
        action="store_true",
        help="fontconfig.txtのvalidNameChars向けエスケープ有効化",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグ表示の有効化",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    action_generate_subset_jp_full(**vars(args))


def action_generate_subset_jp_full(
    output_path: str, validnamechars_escape: bool, debug: bool = False, **_
):
    subset_text = generate_subset_jp_full(debug)
    if validnamechars_escape:
        subset_text = escape_for_validnamechars(subset_text)
    dprint(subset_text, debug)
    if output_path is not None:
        saved_output_path = save_text(
            subset_text,
            output_path=output_path,
        )
        print(f"生成したサブセットを出力しました。: {saved_output_path}")


def generate_subset_jp_full(debug: bool = False) -> str:
    """
    日本語圏向けフルサブセットテキストを生成する

    :param debug: デバッグモード
    :type debug: bool
    :return: 日本語圏向けフルサブセットテキスト
    :rtype: str
    """
    # 重複を防ぐため set を使用
    target_chars = set()

    # --- ASCII (0x20 - 0x7E) ---
    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    # --- JIS X 0213 (第1, 2, 3, 4水準) を網羅的に収集 ---
    # 面1 (1面): 第1, 2, 3水準の一部
    # 面2 (2面): 第4水準
    for plane in [1, 2]:
        for ku in range(1, 95):
            for ten in range(1, 95):
                try:
                    # EUC-JIS-2004 のバイト順序に変換
                    # 1面は 0xA1-0xFE, 2面は 0x8F + 0xA1-0xFE
                    if plane == 1:
                        b_data = bytes([ku + 0xA0, ten + 0xA0])
                    else:
                        b_data = bytes([0x8F, ku + 0xA0, ten + 0xA0])

                    char = b_data.decode("euc_jis_2004")

                    if char.isprintable():
                        target_chars.add(char)
                except (UnicodeDecodeError, LookupError):  # コーデック不在も考慮
                    continue

    # NEC/IBM拡張文字などの範囲 (CP932でよく使われる範囲)
    # 0x2460 - 0x24FF (囲み英数字)
    for i in range(0x2460, 0x2500):
        target_chars.add(chr(i))

    # 手動追加文字を設定
    for code in EXTRA_UNICODES:
        target_chars.add(chr(code))

    # 生成された文字列をソートして返す
    subset_text = "".join(sorted(target_chars))

    return subset_text


if __name__ == "__main__":
    main()
