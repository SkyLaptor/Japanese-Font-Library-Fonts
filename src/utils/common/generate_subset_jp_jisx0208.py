import argparse
import sys

from const import EXTRA_UNICODES
from utils.common.dprint import dprint
from utils.common.escape_for_validnamechars import escape_for_validnamechars
from utils.common.save_text import save_text


def main():
    parser = argparse.ArgumentParser(
        description="JIS第二基準(JISX0208)サブセットテキストを生成する"
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

    action_generate_subset_jp_jisx0208(**vars(args))


def action_generate_subset_jp_jisx0208(
    output_path: str, validnamechars_escape: bool, debug: bool = False, **_
):
    subset_text = generate_subset_jp_jisx0208(debug)
    if validnamechars_escape:
        subset_text = escape_for_validnamechars(subset_text)
    dprint(subset_text, debug)
    if output_path is not None:
        saved_output_path = save_text(
            subset_text,
            output_path=output_path,
        )
        print(f"生成したサブセットを出力しました。: {saved_output_path}")


def generate_subset_jp_jisx0208(debug: bool = False) -> str:
    """
    JIS第二基準(JISX0208)サブセットテキストを生成する

    :param debug: デバッグモード
    :type debug: bool
    :return: JIS第二基準(JISX0208)サブセットテキスト
    :rtype: str
    """
    target_chars = set()

    # --- ASCII (0x20 - 0x7E) ---
    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    # --- JIS X 0208 (第1水準, 第2水準, 非漢字) ---
    # EUC-JPの漢字範囲（0xA1-0xFE）を利用すると、
    # 拡張文字を含まない純粋なJIS X 0208だけを抽出できます。
    for ku in range(1, 95):
        for ten in range(1, 95):
            try:
                # EUC-JPの区点番号へのマッピング
                # 第1・第2水準は 0xA1〜0xFE の範囲に収まります
                b_data = bytes([ku + 0xA0, ten + 0xA0])

                # 'euc_jp' は純粋な JIS X 0208 範囲（+補助漢字など）を扱います
                char = b_data.decode("euc_jp", errors="strict")

                if char.isprintable():
                    target_chars.add(char)
            except UnicodeDecodeError:
                continue

    # 手動追加文字を設定
    for code in EXTRA_UNICODES:
        target_chars.add(chr(code))

    # 生成された文字列をソートして返す
    subset_text = "".join(sorted(target_chars))

    return subset_text


if __name__ == "__main__":
    main()
