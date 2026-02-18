import argparse
import sys
import time
from pathlib import Path

from apps.skyrim.optimizer import convert
from apps.skyrim.swf_patcher import (
    get_swf_name,
    patch_swf_internal_fontname,
    replace_glyph_in_swf,
)
from const import (
    BUILD_DIR,
    ENCODE,
    SKYRIM_EXPORT_MATRIX,
    TEMPLATE_FONTSWF_PATH,
)


def main():
    parser = argparse.ArgumentParser(
        description="フォントファイルをスカイリム向けのフォントSWFに変換する"
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
    suffix = "-premerge"
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_files = [f for f in font_dir.glob("*.ttf") if suffix not in f.name]
        if not font_files:
            continue

        print(f"\n[PREMERGE PROCESS]: {font_dir.name}")

        for font_path in font_files:
            # ループを回さず、基本となる everywhere 用の設定で1回だけ書き出す
            mode = "everywhere"

            offset_height = 0
            offset_config_file = font_dir / f"offset_height_{mode}.txt"

            if offset_config_file.exists():
                try:
                    content = offset_config_file.read_text(encoding=ENCODE).strip()
                    offset_height = int(content) if content else 0
                    print(f"  [CONFIG]: {mode}用オフセット {offset_height} 適用")
                except Exception:
                    print(f"  [WARNING]: {offset_config_file.name} 読み込み失敗")

            output_path = font_dir / f"{font_path.stem}{suffix}.ttf"

            try:
                convert(
                    target_font_path=str(font_path),
                    output_font_path=str(output_path),
                    subset_file_path="",
                    base_type=mode,
                    condense_type="normal",
                    offset_height=offset_height,
                )
                print(f"  [SUCCESS]: {output_path.name}")
            except Exception as e:
                print(f"  [ERROR]: {font_path.name} 失敗: {e}")

    print("\n--- 一括事前調整処理が完了しました！ ---")


def action_run_batch_variant_export(work_dir: str, **_) -> None:
    run_batch_variant_export(work_dir=work_dir)


def run_batch_variant_export(work_dir: str) -> None:
    search_root = Path(work_dir).resolve()
    target_pattern = "*-merged.ttf"

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        merged_fonts = list(font_dir.glob(target_pattern))
        if not merged_fonts:
            continue

        print(f"\n[VARIANT EXPORT]: {font_dir.name}")

        for target_font in merged_fonts:
            for item in SKYRIM_EXPORT_MATRIX:
                base = item["base"]
                condense = item["condense"]
                label = item["label"]
                subset_path = item["path"]

                # 出力ファイル名にフォルダ名を含める必要があればここを調整
                # 今は target_font.stem (元ファイル名) を維持
                out_name = f"{target_font.stem}-{base}-{condense}-{label}.ttf"
                out_path = font_dir / out_name

                try:
                    convert(
                        target_font_path=str(target_font),
                        output_font_path=str(out_path),
                        subset_file_path=str(subset_path),
                        base_type=base,
                        condense_type=condense,
                        offset_height=0,
                        anonymize=True,
                    )
                    print(f"  -> Generated: {out_name}")
                except Exception as e:
                    print(f"  [ERROR]: {out_name} 失敗: {e}")

    print("\n--- 一括バリエーションフォントエクスポート処理が完了しました！ ---")


def action_run_batch_swf_export(work_dir: str, **_) -> None:
    # ラッパー側では font_name を受け取らず、関数内で解決させる
    run_batch_swf_export(work_dir=work_dir)


def run_batch_swf_export(work_dir: str) -> None:
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_name = font_dir.name

        # 【修正ポイント1】取得条件の変更
        # variant_exportで生成されたファイルには必ず base_type (every, book等) が含まれるので、
        # マトリックスにあるキーワードが含まれているか、
        # あるいは「-merged-」が含まれているものを対象にします。
        variant_fonts = [
            f
            for f in font_dir.glob("*.ttf")
            if "-merged-" in f.name  # variant_exportで生成されたファイル
        ]

        if not variant_fonts:
            continue

        print(f"\n[SWF EXPORT]: {font_name}")
        for ttf_path in variant_fonts:

            # 【修正ポイント2】判定用文字列のクリーニング
            # get_swf_nameの中で font_name("noto-sans") は除去されますが、
            # 余計な "-merged" も消してから渡すと、SWF名がより正確に判定されます。
            clean_name = ttf_path.name.replace("-merged", "")

            swf_filename = get_swf_name(font_name, clean_name)
            output_swf_path = font_dir / swf_filename

            #  SWF内のフォント名をファイル名と一致させる
            # 例: fonts_noto-sans_bold_every.swf -> noto-sans_bold_every
            internal_font_name = swf_filename.replace("fonts_", "").replace(".swf", "")

            print(f"  -> Generating: {swf_filename} (Internal: {internal_font_name})")

            # 結構な高負荷処理で失敗することがあるため、リトライを実施します。
            max_retries = 3
            for i in range(max_retries):
                try:
                    # 1. グリフの置換
                    replace_glyph_in_swf(
                        TEMPLATE_FONTSWF_PATH, output_swf_path, ttf_path
                    )

                    # 置換プロセスの完全終了を待つためのバッファ
                    time.sleep(1.0)

                    # 2. 内部名の書き換え (ここが失敗しやすい)
                    patch_swf_internal_fontname(output_swf_path, internal_font_name)

                    print(f"  [SUCCESS]: {swf_filename}")
                    break  # 両方成功したらループを抜ける

                except Exception as e:
                    if i < max_retries - 1:
                        print(
                            f"  [RETRY]: {swf_filename} 処理失敗（{e}）。{i+1}度目の再試行中..."
                        )
                        # 失敗時は少し長めに待機
                        time.sleep(2.0)
                    else:
                        print(
                            f"  [FATAL]: {swf_filename} が規定回数内に処理できませんでした。"
                        )
                        # ここで raise せずに continue すれば、次のフォントへ進めます

    print("\n--- 全てのSWFエクスポート処理が完了しました！ ---")


ACTION_MAP = {
    "run_batch_premerge_export": action_run_batch_premerge_export,
    "run_batch_variant_export": action_run_batch_variant_export,
    "run_batch_swf_export": action_run_batch_swf_export,
}

if __name__ == "__main__":
    main()
