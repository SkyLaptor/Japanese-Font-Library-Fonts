import argparse
import sys

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont

from const import EXCLUDE_CHARS
from utils.common.load_text import load_text
from utils.common.reload_font import reload_font
from utils.common.save_font import save_font


def main():
    parser = argparse.ArgumentParser(description="サブセットフォントを作成する")

    parser.add_argument(
        "input_path",
        type=str,
        help="フォントファイルのパス",
    )
    parser.add_argument(
        "-o",
        "--output_path",
        type=str,
        help="グリフ一覧の書き出し先",
    )
    parser.add_argument(
        "-s",
        "--subset_path",
        type=str,
        help="サブセットファイルのパス",
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

    action_create_subset(**vars(args))


def action_create_subset(
    input_path: str,
    output_path: str,
    subset_path: str,
    debug: bool = False,
    **_,
):
    font_obj = TTFont(input_path)
    font_obj = create_subset(font_obj, load_text(subset_path, EXCLUDE_CHARS), debug)
    if output_path is not None:
        saved_output_path = save_font(font_obj, input_path, output_path, "_subsetted")
        print(f"フォントを保存しました: {saved_output_path}")


def create_subset(font_obj: TTFont, subset_text: str, debug: bool = False) -> TTFont:
    """
    サブセットフォントを作成する

    サブセッターによりタグ情報の一部書き換えが発生するため、
    もしタグ情報の編集を行うのであればサブセット後に実施するようにして下さい。

    :param font_obj: フォント
    :type font_obj: TTFont
    :param subset_text: サブセット文字列
    :type subset_text: str
    :return: サブセットフォント
    :rtype: TTFont
    """
    # サブセットフォントのオプション設定
    options = Options()
    options.notdef_glyph = True  # 常に .notdef を含める（安全対策）
    options.notdef_outline = True  # .notdef（豆腐）の形を維持
    # options.glyph_names = True  # デバッグ用 Format 3.0への更新が行われなくなるため、古いシステムでは読み込みエラーの可能性あり。
    options.retain_gids = False  # グリフIDを保持せず再割り当てする（軽量化のため）
    options.legacy_kern = True  # 古い形式のカーニングも維持
    options.name_IDs = ['*']  # 全てのnameレコードを保持する
    options.name_languages = ['*']  # 全てのnameレコードを保持する
    options.hinting = True  # ヒンティングの維持（デフォルトTrueですが念のため）
    options.layout_features = ['*']  # レイアウト機能（合字やカーニング）を保持
    options.recalc_timestamp = False  # 更新日時を変更したくない場合

    subsetter = Subsetter(options=options)
    subsetter.populate(text=subset_text)
    subsetter.subset(font=font_obj)

    return reload_font(font_obj)


if __name__ == "__main__":
    main()
