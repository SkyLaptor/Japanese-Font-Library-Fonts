# Dependencies: FFDec=False, FontForge=False
from const import EXTRA_UNICODES
from core.text_processor import escape_for_validnamechars


def generate_subset_jp_full(validnamechars_escape: bool = False) -> str:
    """
    日本語圏向けフルサブセットテキストを生成する

    :param validnamechars_escape: validNameChars向けエスケープ
    :type validnamechars_escape: bool
    :return: 日本語圏向けフルサブセットテキスト
    :rtype: str
    """
    target_chars = set()

    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    for plane in [1, 2]:
        for ku in range(1, 95):
            for ten in range(1, 95):
                try:
                    if plane == 1:
                        b_data = bytes([ku + 0xA0, ten + 0xA0])
                    else:
                        b_data = bytes([0x8F, ku + 0xA0, ten + 0xA0])

                    char = b_data.decode("euc_jis_2004")

                    if char.isprintable():
                        target_chars.add(char)
                except (UnicodeDecodeError, LookupError):
                    continue

    for i in range(0x2460, 0x2500):
        target_chars.add(chr(i))

    for code in EXTRA_UNICODES:
        target_chars.add(chr(code))

    subset_text = "".join(sorted(target_chars))

    if validnamechars_escape:
        subset_text = escape_for_validnamechars(subset_text)

    return subset_text


def generate_subset_jp_jisx0208(validnamechars_escape: bool = False) -> str:
    """
    JIS第二基準(JISX0208)サブセットテキストを生成する

    :param validnamechars_escape: validNameChars向けエスケープ
    :type validnamechars_escape: bool
    :return: JIS第二基準(JISX0208)サブセットテキスト
    :rtype: str
    """
    target_chars = set()

    for i in range(0x20, 0x7F):
        target_chars.add(chr(i))

    for ku in range(1, 95):
        for ten in range(1, 95):
            try:
                b_data = bytes([ku + 0xA0, ten + 0xA0])
                char = b_data.decode("euc_jp", errors="strict")

                if char.isprintable():
                    target_chars.add(char)
            except UnicodeDecodeError:
                continue

    for code in EXTRA_UNICODES:
        target_chars.add(chr(code))

    subset_text = "".join(sorted(target_chars))

    if validnamechars_escape:
        subset_text = escape_for_validnamechars(subset_text)

    return subset_text


def gen_subset_jp_full(validnamechars_escape: bool = False) -> str:
    return generate_subset_jp_full(validnamechars_escape=validnamechars_escape)


def gen_subset_jp_jisx0208(validnamechars_escape: bool = False) -> str:
    return generate_subset_jp_jisx0208(validnamechars_escape=validnamechars_escape)
