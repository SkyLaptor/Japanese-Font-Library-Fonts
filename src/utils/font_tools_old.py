#!/usr/bin/env venv
import re
import fontforge
import psMat
import sys
import os

os.environ["LANG"] = "C"
os.environ["LC_ALL"] = "C"


def is_ttf(input_font_path):
    """フォントファイルが本当にTTFなのかを判定する

    Args:
        input_font_path (str): チェック対象のフォントパス

    Returns:
        result (bool): チェック結果
    """
    # パラメータチェック
    if not os.path.exists(input_font_path):
        raise FileNotFoundError(
            f"フォントファイルが見つかりません。: {input_font_path}"
        )

    # TTFチェック
    try:
        with open(input_font_path, "rb") as f:
            header = f.read(4)
            return header in (b"\x00\x01\x00\x00", b"true")
    except Exception:
        return False


def clear_hints(font_obj):
    """フォントからヒント情報を削除する

    メトリクスやグリフのサイズを変更する際にヒント情報が残っていると、実際に表示した際に文字にガタつきが出る場合があります。
    ヒント情報が欲しい場合には、フォント生成直前に生成すると良いでしょう。

    Args:
        font_obj (fontforge.font): 変更対象のフォント

    Returns:
        font_obj (fontforge.font): 変更後のフォント
    """
    # ヒント情報削除
    for glyph in font_obj.glyphs():
        glyph.removePosInt()
        glyph.removeHintMasks()
    font_obj.private = {}

    return font_obj


def apply_hints(font_obj):
    """フォントにヒント情報を適用する

    Args:
        font_obj (fontforge.font): 変更対象のフォント

    Returns:
        font_obj (fontforge.font): 変更後のフォント
    """
    # 自動ヒント情報適用
    print("ヒント情報を適用します。")
    font_obj.autohint()

    return font_obj


def change_font_metrics(font_obj, ascent, descent):
    """フォントのメトリクスを変更する

    AscentとDescentはペアで渡すこと。合計値は1024を強く推奨。

    Args:
        font_obj (fontforge.font): 変更対象のフォント
        ascent (int): Ascentの値(units)
        descent (int): Descentの値(units)

    Returns:
        font_obj (fontforge.font): 変更後のフォント
    """
    # パラメータチェック
    if not (isinstance(ascent, int) and isinstance(descent, int)):
        raise TypeError(
            f"引数は整数で指定してください (ascent: {type(ascent)}, descent: {type(descent)})"
        )

    em = ascent + descent

    if em % 8 != 0:
        raise ValueError("ascentとdescentの値の合計は8の倍数にしてください。")

    # メトリクス変更
    print(f"メトリクスを変更します (ascent:{ascent}, descent:{descent}, em:{em})")
    if font_obj.em != em:
        scale = float(em) / font_obj.em
        font_obj.selection.all()
        font_obj.transform(psMat.scale(scale))
        font_obj.em = em
    font_obj.ascent = ascent
    font_obj.descent = descent
    font_obj.upos = -100
    font_obj.uwidth = 50
    font_obj.hasvmetrics = False
    font_obj.os2_winascent = ascent
    font_obj.os2_windescent = descent
    font_obj.os2_typoascent = ascent
    font_obj.os2_typodescent = -descent
    font_obj.os2_use_typo_metrics = False
    font_obj.os2_typolinegap = 0
    font_obj.os2_subxsize = int(font_obj.em * 0.635)
    font_obj.os2_subysize = int(font_obj.em * 0.6)
    font_obj.os2_subxoff = 0
    font_obj.os2_subyoff = int(font_obj.em * 0.075)
    font_obj.os2_supxsize = int(font_obj.em * 0.635)
    font_obj.os2_supysize = int(font_obj.em * 0.6)
    font_obj.os2_supxoff = 0
    font_obj.os2_supyoff = int(font_obj.em * 0.34)
    font_obj.os2_strikeysize = int(font_obj.em * 0.050)
    font_obj.os2_strikeypos = int(font_obj.em * 0.03)
    font_obj.hhea_ascent = ascent
    font_obj.hhea_descent = -descent

    return font_obj


def anonymize_font_info(font_obj, fontname):
    """フォント情報を匿名化する

    フォントには様々な情報が記載されてあり、その組み合わせで元のフォントを特定可能です。
    それらの情報を消去することで特定を回避します。

    Args:
        font_obj (fontforge.font): 匿名化対象のフォント
        fontname (str): フォント名

    Returns:
        font_obj (fontforge.font): 匿名化後のフォント
    """
    # パラメータチェック
    if not fontname or fontname.isspace():
        raise ValueError("文字列が空、または空白のみです。")

    if re.search(r"[^a-zA-Z0-9_-]", fontname):
        raise ValueError(
            f"不適切な文字が含まれています: '{fontname}' (英数字、ハイフン、アンダースコアのみ使用可能です)"
        )

    # フォント情報匿名化
    font_obj.fontname = fontname
    font_obj.fullname = fontname
    font_obj.familyname = fontname
    font_obj.uniqueid = 1
    font_obj.version = "1.000"
    font_obj.copyright = ""
    font_obj.os2_vendor = "    "
    new_names = []
    for lang in ("English (US)",):
        new_names.append((lang, "Copyright", font_obj.copyright))
        new_names.append((lang, "Family", font_obj.fontname))
        new_names.append((lang, "SubFamily", "Regular"))
        new_names.append((lang, "UniqueID", "Unknown"))
        new_names.append((lang, "Fullname", font_obj.fontname))
        new_names.append((lang, "Version", f"Version {font_obj.version}"))
        new_names.append((lang, "PostScriptName", font_obj.fontname))
    font_obj.sfnt_names = tuple(new_names)

    return font_obj


if __name__ == "__main__":
    print("--------------------------------------------------")
    print("このファイルはツールライブラリです。")
    print("直接実行ではなく、他のスクリプトからインポートして使用してください。")
    print("--------------------------------------------------")
    sys.exit(1)
