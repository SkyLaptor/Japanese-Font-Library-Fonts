from io import BytesIO

from fontTools.ttLib import TTFont


def reopen_font(font_obj: TTFont) -> TTFont:
    """
    フォントをメモリ上で再オープンする

    フォントオブジェクトのまま加工を続けていくとフォントが破損する場合があります。
    そこで、一度メモリ上に書き出して読み直しさせることで回避します。
    再オープンしたデータは全く別物扱いのため、必ず戻り値で受け取る必要があります。

    :param font_obj: 再オープンさせるフォントオブジェクト
    :type font_obj: TTFont
    :return: 再オープンを行ったフォントオブジェクト
    :rtype: TTFont
    """
    buffer = BytesIO()
    font_obj.save(buffer)
    buffer.seek(0)
    reopened_font_obj = TTFont(buffer)
    return reopened_font_obj
