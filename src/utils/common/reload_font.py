from io import BytesIO

from fontTools.ttLib import TTFont


def reload_font(font_obj: TTFont, debug: bool = False) -> TTFont:
    """
    フォントの再読み込みを行う

    フォントオブジェクトのまま加工を続けていくとフォントが破損する場合があります。
    そこで、一度メモリ上に書き出して読み直しさせることで回避します。
    再読み込みしたデータは全く別物扱いのため、必ず戻り値で受け取る必要があります。

    :param font_obj: 再読み込みさせるフォントオブジェクト
    :type font_obj: TTFont
    :param debug: デバッグモード
    :type debug: bool
    :return: 再読み込みを行ったフォントオブジェクト
    :rtype: TTFont
    """
    buffer = BytesIO()
    font_obj.save(buffer)
    buffer.seek(0)
    reloaded_font_obj = TTFont(buffer)
    return reloaded_font_obj
