def escape_for_validnamechars(text: str, debug: bool = False) -> str:
    """
    validNameChars向けにエスケープを行う

    validNameCharsとは、スカイリムのfontconfig.txt内にあるキャラクター名に使用できる文字列を指します。

    :return: エスケープ後の文字列
    :rtype: str
    """
    replaced_text = text.replace('"', '\\"')
    return replaced_text
