import argparse
import subprocess
import sys
from pathlib import Path

from utils.common import long_path

ENCODE = "utf-8"
FONTFILE_EXT = ".swf"
XMLFILE_EXT = ".xml"

# 定数自体をPathにしておくと、以降の連結が楽になります
SUBSETS_DIR = Path(r"data\subsets")
ASSETS_FONT_DIR = Path(r"assets\font")
BUILD_DIR = Path(r"build")
TEMPLATE_FONTSWF_PATH = Path(r"data\fontsswf\fonts_template.swf")

BASE_FONTS = {
    "everywhere": Path(r"data\basefonts\everywhere.ttf").resolve(),
    # "book": Path(r"data\basefonts\book.ttf").resolve(),
    # "handwrite": Path(r"data\basefonts\handwrite.ttf").resolve(),
}

# フォントテンプレートSWFで設定したフォント名であること
DUMMY_NAME = "REPLACE_ME_FONT_NAME_LENGTH_MAX_XXXXXXXXXXXXXXX"
DUMMY_BIN = DUMMY_NAME.encode(ENCODE) + b"\x00"

FONTFILE_NAME_PREFIX = "fonts_"


def main():
    parser = argparse.ArgumentParser(
        description="フォントの最終処理を行い、フォントSWFに変換するためのスクリプト。"
    )

    parser.add_argument(
        "--action",
        choices=list(ACTION_MAP.keys()),
        help="実行する操作を指定します。",
    )
    parser.add_argument(
        "-w",
        "--work_dir",
        type=str,
        default=BUILD_DIR,
        help="作業対象ディレクトリ",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモード",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    dispatch_action(**vars(args))


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def action_run_batch_premerge_export(work_dir: str, **_) -> None:
    run_batch_premerge_export(work_dir=work_dir)


def run_batch_premerge_export(work_dir: str) -> None:
    """
    異なるフォント同士をマージする前の事前調整を一括で行う。

    以下の順で処理されます。
    1. 空白グリフ削除: 先に消しておかないと、UPM変更時に正しい拡大縮小率を得られません。
    2. UPM変更:
        バニラEverywhere(UPM1024)フォントを基準にします。
        他のheadタグ情報も書き換わってしまいますが最終処理時に上書きされるため特に気にしなくてもよいです。
    3. 上下オフセット適用
        フォントによって適正値が異なるため、各フォントディレクトリ直下の `offset_height_everywhere.txt` を読んで設定します。
        オフセット値は別途 util.inspector.get_offset_to_align_bottom() を使用して算出できます。

    NOTE: これを走らせたときにエラーになるフォントは、一度fontforgeで再エクスポートしてみると大抵治ります。

    :param work_dir: 作業ディレクトリ
    :type work_dir: str
    """
    suffix = "-premerge"
    search_root = Path(work_dir).resolve()

    # 処理前にベースフォントがあるか確認
    for mode, path in BASE_FONTS.items():
        if not path.exists():
            print(f"[FATAL]: ベースフォントが見つかりません: {path}")
            print("         .gitignore で除外されていないか、配置を確認してください。")
            return

    # 最初にリスト化し、尚且つ suffix (-premerge) が付いているものは処理済みフォントとして除外する
    font_files = [f for f in search_root.rglob("*.ttf") if suffix not in f.name]

    for font_path in font_files:
        if suffix in font_path.name:
            print(f"\n[SKIP]: {font_path.name}")
            continue

        print(f"\n[PROCESS]: {font_path.name}")

        for mode, base_path in BASE_FONTS.items():
            offset_height = "0"
            offset_height_filename = f"offset_height_{mode}.txt"
            offset_height_file = font_path.parent / offset_height_filename

            if offset_height_file.exists():
                try:
                    content = offset_height_file.read_text(encoding=ENCODE).strip()
                    if content:
                        offset_height = content
                        print(
                            f"  [CONFIG]: {offset_height_filename} 適用（{offset_height}）"
                        )
                except Exception:
                    print(f"  [WARNING]: {offset_height_filename} 読み込み失敗")

            output_name = f"{font_path.stem}{suffix}.ttf"
            output_path = font_path.parent / output_name

            cmd = [
                "uv",
                "run",
                "convert_for_skyrim",
                long_path(font_path),
                "--base",
                mode,
                "-o",
                long_path(output_path),
                "--offset_height",
                offset_height,
            ]

            print(f"Command: {cmd}")
            print(f"  -> {mode} 生成開始...")

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"  [ERROR]: {output_name} 生成失敗")
                print(f"  {e.stderr[:200]}")

    print("\n--- 一括事前調整処理が完了しました！ ---")


def action_run_batch_variant_export(work_dir: str, **_) -> None:
    run_batch_variant_export(work_dir=work_dir)


def run_batch_variant_export(work_dir: str) -> None:
    """
    結合まで完了したフォントを各種バリエーション用に変換する。

    * 作業ディレクトリ内にある結合済みの各ウェイトフォントに対し、以下のパターンで作成します。
        * Everywhere用は通常、長体、超長体の3種類
        * Book・Handwritten用は通常のみ。
    * 各フォント毎にフルサブセットとSkyrimバニラサブセットの2種類のバリエーションが作成されます。

    :param work_dir: 作業ディレクトリ
    :type work_dir: str
    """
    search_root = Path(work_dir).resolve()
    target_suffix = "*-merged.ttf"

    matrix = [
        ("everywhere", "normal", "subset_jp_full.txt", "full"),
        ("everywhere", "condense", "subset_jp_full.txt", "full"),
        ("everywhere", "skinny", "subset_jp_full.txt", "full"),
        ("everywhere", "normal", "subset_jp_skyrim.txt", "skyrim"),
        ("everywhere", "condense", "subset_jp_skyrim.txt", "skyrim"),
        ("everywhere", "skinny", "subset_jp_skyrim.txt", "skyrim"),
        ("book", "normal", "subset_jp_full.txt", "full"),
        ("book", "normal", "subset_jp_skyrim.txt", "skyrim"),
        ("handwrite", "normal", "subset_jp_full.txt", "full"),
        ("handwrite", "normal", "subset_jp_skyrim.txt", "skyrim"),
    ]

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        merged_fonts = list(font_dir.glob(target_suffix))
        if not merged_fonts:
            continue

        print(f"\n[FINAL EXPORT]: {font_dir.name}")

        # フォルダ内の各フォント（heavy, mediumなど）を回すループ
        for target_font in merged_fonts:
            print(f"  Processing base font: {target_font.name}")

            # そのフォントに対して、各バリエーションを作るループ
            for base, condense, subset_file, label in matrix:
                subset_path = SUBSETS_DIR / subset_file

                out_name = f"{target_font.stem}-{base}-{condense}-{label}.ttf"
                out_path = font_dir / out_name

                cmd = [
                    "convert_for_skyrim",
                    str(target_font),
                    "--base",
                    base,
                    "--subset",
                    str(subset_path),
                    "--condense",
                    condense,
                    "-o",
                    str(out_path),
                    "--anonymize",
                ]

                print(f"Command: {cmd}")
                print(f"  -> Generating: {out_name}...")

                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError:
                    print(f"  [ERROR]: {out_name} の生成に失敗しました。")

    print("\n--- 一括バリエーションフォントエクスポート処理が完了しました！ ---")


def get_swf_name(font_name: str, font_file_name: str) -> str:
    """
    ファイル名からスカイリムの命名規則に従ったSWF名を生成する。

    ある程度の表記ブレを吸収します。
    MOD利用者向けにアナウンスしているパターンとなるように注意して下さい。
    参考: https://github.com/SkyLaptor/Japanese-Font-Library

    :param font_name: フォント名
    :type font_name: str
    :param font_file_name: フォントファイル名
    :type font_file_name: str
    :return: フォントファイル名
    :rtype: str
    """

    # 判定用の文字列を作成（ファイル名からフォント名部分を削除して小文字化）
    # これにより、フォント名自体に含まれる "every" や "hand" を無視します
    font_file_name_low = font_file_name.lower()
    font_name_low = font_name.lower()
    # フォント名部分を除去した、純粋な「属性（weightやui等）」判定用の文字列
    features_part = font_file_name_low.replace(font_name_low, "")
    weight_type = ""
    ui_type = ""
    condense_type = ""
    subset_type = ""

    if "bold" in features_part:
        weight_type = "_bold"
    elif "light" in features_part:
        weight_type = "_light"
    elif "heavy" in features_part or "extrabold" in features_part:
        weight_type = "_heavy"

    if "everywhere" in features_part or "every" in features_part:
        ui_type = "_every"
    elif "book" in features_part:
        ui_type = "_book"
    elif (
        "handwritten" in features_part
        or "handwrite" in features_part
        or "hand" in features_part
    ):
        ui_type = "_handwrite"

    if (
        "condensed" in features_part
        or "condense" in features_part
        or "cond" in features_part
    ):
        condense_type = "_condensed"
    elif "skinny" in features_part or "skin" in features_part:
        condense_type = "_skinny"

    if "skyrim" in features_part or "lightweight" in features_part:
        subset_type = "_lightweight"

    return f"{FONTFILE_NAME_PREFIX}{font_name}{weight_type}{ui_type}{condense_type}{subset_type}{FONTFILE_EXT}"


def patch_swf_internal_fontname(swf_path: str, font_name: str) -> bool:
    """
    SWF内のフォント名をXML経由で安全に書き換える。

    SWFそのものを操作するのはトラブルの元であるため、一旦XMLにしてから操作して書き戻す対応を行います。
    フォントサイズが大きいほど時間がかかります。また、一時的に100-500MB程度のファイルが作業ディレクトリに作成されます。

    :param swf_path: SWFファイルパス
    :type swf_path: str
    :param font_name: フォント名
    :type font_name: str
    :return: 書き換え結果
    :rtype: bool
    """
    xml_path = swf_path.with_suffix(XMLFILE_EXT)

    try:
        # SWF -> XML
        subprocess.run(
            ["ffdec-cli", "-swf2xml", str(swf_path), str(xml_path)],
            check=True,
            capture_output=True,
        )

        # 置換処理
        xml_content = xml_path.read_text(encoding=ENCODE)
        xml_path.write_text(xml_content.replace(DUMMY_NAME, font_name), encoding=ENCODE)

        # XML -> SWF
        subprocess.run(
            ["ffdec-cli", "-xml2swf", str(xml_path), str(swf_path)],
            check=True,
            capture_output=True,
        )
        return True
    except Exception as e:
        print(f"  [ERROR] XML Patch failed: {e}")
        if xml_path.exists():
            xml_path.unlink()
        return False
    finally:
        # finally で書くことで、成功・失敗に関わらず一時ファイルを掃除
        if xml_path.exists():
            xml_path.unlink()


def action_run_batch_swf_export(work_dir: str, **_) -> None:
    run_batch_swf_export(work_dir=work_dir)


def run_batch_swf_export(work_dir: str) -> None:
    """
    フォントファイルを一括でフォントSWFファイルに変換する。

    外部コマンドとしてFFDec(ffdec-cli)を使用するため、忘れずに環境変数へ設定して下さい。

    :param work_dir: 作業ディレクトリ
    :type work_dir: str
    """
    search_root = Path(work_dir).resolve()
    template_swf = Path(TEMPLATE_FONTSWF_PATH).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue
        font_name = font_dir.name
        font_files = [
            font_file
            for font_file in font_dir.glob("*.ttf")
            if "full" in font_file.name.lower() or "skyrim" in font_file.name.lower()
        ]
        if not font_files:
            continue

        target_out_dir = search_root / font_name
        target_out_dir.mkdir(parents=True, exist_ok=True)

        for ttf in font_files:
            swf_filename = get_swf_name(font_name, ttf.name)
            output_swf = target_out_dir / swf_filename
            internal_font_name = swf_filename.replace(FONTFILE_NAME_PREFIX, "").replace(
                FONTFILE_EXT, ""
            )

            cmd = [
                "ffdec-cli",
                "-replace",
                str(template_swf),
                str(output_swf),
                "1",
                str(ttf),
            ]

            print(f"Command: {cmd}")
            print(f"[{font_name}] Processing: {ttf.name}")
            try:
                subprocess.run(
                    cmd, check=True, capture_output=True, text=True, shell=True
                )
                if patch_swf_internal_fontname(output_swf, internal_font_name):
                    print(
                        f"  => [SUCCESS] {swf_filename} (Internal: {internal_font_name})"
                    )
                else:
                    print(f"  => [FAILED] Tag lookup failed for {swf_filename}")
            except Exception as e:
                print(f"  => [ERROR] {e}")

    print("\n--- 一括フォントSWFエクスポート処理が完了しました！ ---")


ACTION_MAP = {
    "run_batch_premerge_export": action_run_batch_premerge_export,
    "run_batch_variant_export": action_run_batch_variant_export,
    "run_batch_swf_export": action_run_batch_swf_export,
}

if __name__ == "__main__":
    main()
