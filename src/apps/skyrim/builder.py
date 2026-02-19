import argparse
import re
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
    SKYRIM_BASE_KEYNAME,
    SKYRIM_EXPORT_MATRIX,
    TEMPLATE_FONTSWF_PATH,
)
from utils.common.dprint import dprint


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
        "--anonymize",
        action="store_true",
        help="フォントを匿名化するかどうか。 アクションによっては無視されます。",
    )
    parser.add_argument(
        "--output_font_info",
        action="store_true",
        help="処理後のフォント情報を出力するかどうか。 アクションによっては無視されます。",
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


def action_run_batch_premerge_export(
    work_dir: str, anonymize: bool, output_font_info: bool, debug: bool = False, **_
) -> None:
    run_batch_premerge_export(
        work_dir=work_dir,
        anonymize=anonymize,
        output_font_info=output_font_info,
        debug=debug,
    )


def run_batch_premerge_export(
    work_dir: str,
    anonymize: bool = False,
    output_font_info: bool = False,
    debug: bool = False,
) -> None:
    # 処理後のフォントには_premergeを末尾に付与します
    suffix = "_premerge"
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_files = [f for f in font_dir.glob("*.ttf") if suffix not in f.name]
        if not font_files:
            continue

        print(f"\n[事前調整フォント出力]: {font_dir.name}")

        for font_path in font_files:
            # ループを回さず、基本となる every 用の設定で1回だけ書き出します
            # bookおよびhandwriteは使用されるUIの特性上、ズレを感じないためです
            base = "every"

            offset_height = 0
            offset_config_file = font_dir / f"offset_height_{base}.txt"

            if offset_config_file.exists():
                try:
                    content = offset_config_file.read_text(encoding=ENCODE).strip()
                    offset_height = int(content) if content else 0
                    print(
                        f"  [設定]: オフセット設定ファイルから取得したオフセット値を適用します: {offset_height}"
                    )
                except Exception:
                    print(
                        "  [設定]: オフセット設定ファイルが存在しない/読み取れないため、オフセット0で実行します"
                    )

            # 1. まず小文字にする
            stem_lower = font_path.stem.lower()

            # 2. 末尾付近にある「区切り」として使われているハイフンをアンダースコアに置換
            # ウェイト名などの直前にあるハイフンだけを狙い撃ちします
            # 例: "noto-sans-bold" -> "noto-sans_bold"
            # 正規表現を使って、特定のウェイトキーワードの前のハイフンを置換します
            clean_stem = re.sub(
                r'-(bold|medium|thin|light|regular|black|heavy|semibold|extrabold|extralight)',
                r'_\1',
                stem_lower,
            )

            output_path = font_dir / f"{clean_stem}{suffix}.ttf"

            try:
                convert(
                    target_font_path=str(font_path),
                    output_font_path=str(output_path),
                    base_type=base,
                    offset_height=offset_height,
                    anonymize=anonymize,
                    output_font_info=output_font_info,
                )
                print(f"  [出力成功]: {output_path.name}")
            except Exception as e:
                print(f"  [エラー]: {font_path.name} 詳細: {e}")

    print("\n--- 全ての対象フォントの事前調整が完了しました ---")


def action_run_batch_variant_export(
    work_dir: str, anonymize: bool, output_font_info: bool, debug: bool = False, **_
) -> None:
    run_batch_variant_export(
        work_dir=work_dir, anonymize=anonymize, output_font_info=output_font_info
    )


def run_batch_variant_export(
    work_dir: str,
    anonymize: bool = False,
    output_font_info: bool = False,
    debug: bool = False,
) -> None:
    # 処理後のフォントには、バリアントを示す_every,_book,_handwriteが付与されます。
    # また、場合によりウェイト(_bold等)、長体(_condense等)、サブセット(_lightweight等)も付与されます。
    # 最後のSWF出力向けに、ここできちんと名前を設定してあげる必要があります。

    # 指定した作業ディレクトリ内を再帰的に処理します
    search_root = Path(work_dir).resolve()
    # ファイル名の末尾がmerged.ttfのものだけを処理対象にします
    # 結合処理を行ったフォント(または結合の必要のないフォント)は_merged.ttfとするルールになっています。
    target_pattern = "*_merged.ttf"

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        merged_fonts = list(font_dir.glob(target_pattern))
        if not merged_fonts:
            continue

        print(f"\n[バリアントフォント出力]: {font_dir.name}")

        for target_font in merged_fonts:
            dprint(f"元の名前: {target_font}", debug)
            # 元の名前 (例: test-font_bold_merged) からまずは "_merged" を取り除きます
            clean_base_name = target_font.stem.replace("_merged", "")
            dprint(f"_mergedを取り除いた名前: {clean_base_name}", debug)

            for item in SKYRIM_EXPORT_MATRIX:
                base = item["base"]  # every, book, handwrite 等
                condense = item["condense"]  # normal, condense, skinny 等
                label = item["label"]  # full, lightweight 等
                subset_path = item["path"]  # 使用するサブセットファイル

                dprint(f"マトリクス: {item}", debug)

                # --- 【ここから命名ロジック】 ---
                # 1. まず clean_base_name 自体を正規化する
                temp_name = clean_base_name
                # ウェイトのMediumは存在自体を消す
                temp_name = re.sub(r'[-_]medium', '', temp_name, flags=re.IGNORECASE)
                # その他ウェイト系をアンダースコア小文字に統一 多分他にないはず
                temp_name = re.sub(
                    r'[-_]regular', '_regular', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(r'[-_]thin', '_thin', temp_name, flags=re.IGNORECASE)
                temp_name = re.sub(
                    r'[-_]extralight', '_extralight', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]light', '_light', temp_name, flags=re.IGNORECASE
                )

                temp_name = re.sub(
                    r'[-_]semibold', '_semibold', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(r'[-_]bold', '_bold', temp_name, flags=re.IGNORECASE)
                temp_name = re.sub(
                    r'[-_]extrabold', '_extrabold', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]heavy', '_heavy', temp_name, flags=re.IGNORECASE
                )
                temp_name = re.sub(
                    r'[-_]black', '_black', temp_name, flags=re.IGNORECASE
                )

                # 必要なパーツだけを集める
                # すでに _bold が入っている可能性があるので、アンダースコアでバラして空要素を詰め直すと綺麗になります
                base_parts = [p for p in temp_name.split("_") if p]
                parts = base_parts

                # デフォルト値（長体:normal, サブセット:full）は名前に含めないようにしてパーツを構成
                if base:
                    parts.append(base)  # ベース（every,book,handwrite）は必須です。
                if condense not in ["normal"]:
                    parts.append(condense)
                if label not in ["full"]:
                    parts.append(label)

                # アンダースコアで結合 (例: test-font_bold_every)
                out_name_base = "_".join(parts)
                dprint(f"最終的な名前: {out_name_base}", debug)
                out_name = f"{out_name_base}.ttf"

                out_path = font_dir / out_name

                try:
                    convert(
                        target_font_path=str(target_font),
                        output_font_path=str(out_path),
                        subset_file_path=str(subset_path),
                        base_type=base,
                        condense_type=condense,
                        offset_height=0,
                        anonymize=anonymize,
                        output_font_info=output_font_info,
                    )
                    print(f"  -> [生成完了]: {out_name}")
                except Exception as e:
                    print(f"  [エラー]: {out_name} 詳細: {e}")

    print("\n--- 全ての対象フォントのバリアント化が完了しました ---")


def action_run_batch_swf_export(work_dir: str, debug: bool = False, **_) -> None:
    # ラッパー側では font_name を受け取らず、関数内で解決させる
    run_batch_swf_export(work_dir=work_dir)


def run_batch_swf_export(work_dir: str, debug: bool = False) -> None:
    # 指定した作業ディレクトリ内を再帰的に処理します
    search_root = Path(work_dir).resolve()

    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        font_name = font_dir.name
        dprint(f"フォント名(ディレクトリ名から取得): {font_name}")

        # 全てのTTFを拾うと事故るので、生成されたバリアント（_mergedを含まない等）に絞る
        # あるいは、SKYRIM_EXPORT_MATRIXにあるキーワードが含まれているかチェックするのが確実です
        variant_fonts = [
            f
            for f in font_dir.glob("*.ttf")
            if any(k in f.name for k in SKYRIM_BASE_KEYNAME)
            and "_merged" not in f.name
            and "_premerge" not in f.name
        ]

        if not variant_fonts:
            continue

        print(f"\n[フォントSWF出力]: {font_name}")
        for ttf_path in variant_fonts:
            # 例: "test-font_bold_book", "test-font_every"
            stem_name = ttf_path.stem

            swf_filename = get_swf_name(font_name, stem_name)
            output_swf_path = font_dir / swf_filename

            # SWF内のフォント名をファイル名と一致させる
            # 例: fonts_noto-sans_bold_every.swf -> noto-sans_bold_every
            internal_font_name = swf_filename.replace("fonts_", "").replace(".swf", "")
            print(f"  -> 変換元: {ttf_path.name}")
            print(f"  -> 処理後: {swf_filename} (内部フォント名: {internal_font_name})")

            # 結構な高負荷処理で失敗することがあるため、リトライを実施します。
            max_retries = 3
            for i in range(max_retries):
                try:
                    # 1. グリフの置換
                    replace_glyph_in_swf(
                        TEMPLATE_FONTSWF_PATH, output_swf_path, ttf_path
                    )

                    # 置換プロセスの完全終了を待つためのバッファ
                    time.sleep(0.5)

                    # 2. 内部名の書き換え (ここが失敗しやすい)
                    patch_swf_internal_fontname(output_swf_path, internal_font_name)

                    print(f"  [成功]: {swf_filename}")
                    break  # 両方成功したらループを抜ける

                except Exception as e:
                    if i < max_retries - 1:
                        print(
                            f"  [再試行]: {swf_filename} 処理失敗（{e}）。{i+1}度目の再試行中..."
                        )
                        # 失敗時は少し長めに待機
                        time.sleep(1.0)
                    else:
                        print(
                            f"  [失敗]: {swf_filename} が規定回数内に処理できませんでした。"
                        )
                        # ここで raise せずに continue すれば、次のフォントへ進めます

    print("\n--- 全ての対象フォントのSWF化が完了しました ---")


ACTION_MAP = {
    "run_batch_premerge_export": action_run_batch_premerge_export,
    "run_batch_variant_export": action_run_batch_variant_export,
    "run_batch_swf_export": action_run_batch_swf_export,
}

if __name__ == "__main__":
    main()
