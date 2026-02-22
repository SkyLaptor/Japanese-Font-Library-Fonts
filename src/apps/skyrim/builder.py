import argparse
import csv
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from fontTools.ttLib import TTFont

from apps.skyrim.optimizer import convert
from apps.skyrim.swf_patcher import (
    get_swf_name,
    patch_swf_internal_fontname,
    replace_glyph_in_swf,
)
from const import (
    BASE_LINE_TARGET,
    BUILD_DIR,
    ENCODE,
    FONTFORGE_PATH,
    MERGE_CONF_PATH,
    MERGE_FONT_FF_PATH,
    SKYRIM_BASE_KEYNAME,
    SKYRIM_EXPORT_MATRIX,
    TEMPLATE_FONTSWF_PATH,
)
from utils.common.dprint import dprint
from utils.inspector.get_offset_to_align_bottom import get_offset_to_align_bottom

OFFSET_HEIGHT_FILENAME = "offset_height.txt"


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
        "--base_line",
        type=int,
        default=BASE_LINE_TARGET,
        help=f"オフセット位置決めのためのベースライン デフォルト:{BASE_LINE_TARGET}",
    )
    parser.add_argument(
        "--merge_conf",
        type=str,
        default=MERGE_CONF_PATH,
        help=f"オフセット位置決めのためのベースライン デフォルト:{BASE_LINE_TARGET}",
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
    work_dir: str,
    base_line: int,
    anonymize: bool,
    output_font_info: bool,
    debug: bool = False,
    **_,
) -> None:
    run_batch_premerge_export(
        work_dir=work_dir,
        base_line=base_line,
        anonymize=anonymize,
        output_font_info=output_font_info,
        debug=debug,
    )


def run_batch_premerge_export(
    work_dir: str,
    base_line: int = BASE_LINE_TARGET,
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

        # 走査中のフォルダで_premerge.ttfを除いた.ttfファイルの一覧を取得する。
        font_files = [
            f
            for f in font_dir.glob("*.ttf")
            if not f.name.lower().endswith(f"{suffix.lower()}.ttf")
        ]

        # なければ次のフォルダへ
        if not font_files:
            continue

        print(f"\n[事前調整フォント出力]: {font_dir.name}")

        for font_path in font_files:
            # --- オフセット値の決定ロジック ---
            offset_height = 0
            offset_file = font_dir / OFFSET_HEIGHT_FILENAME

            if offset_file.exists():
                # 1. 設定ファイルがある場合は読み込みを優先
                try:
                    content = offset_file.read_text(encoding=ENCODE).strip()
                    offset_height = int(content)
                    print(
                        f"  [オフセット読込]: 設定ファイルから '{offset_height}' を採用します。"
                    )
                except ValueError:
                    print(
                        f"  [警告]: {offset_file.name} の内容が数値ではありません。自動計算に切り替えます。"
                    )
                    # 数値変換に失敗した場合は下の自動計算へ流れるように設定
                    offset_file_invalid = True
                else:
                    offset_file_invalid = False
            else:
                offset_file_invalid = True

            # 2. 設定ファイルがない（または無効な）場合は自動計算
            if offset_file_invalid:
                try:
                    with TTFont(str(font_path)) as tmp_font:
                        offset_height = get_offset_to_align_bottom(
                            tmp_font, base_line, debug
                        )
                    print(
                        f"  [オフセット自動計算]: ベースライン値: {base_line}, 計算結果: {offset_height}"
                    )
                except Exception as e:
                    print(
                        f"  [警告]: 自動計算に失敗しました。オフセット0で進めます。詳細: {e}"
                    )
                    offset_height = 0

            # 最適化処理ではeveryをベースにするだけでよいため、明記します。
            base = "every"

            # 1. まず小文字にする
            stem_lower = font_path.stem.lower()

            # 2. 末尾付近にある「区切り」として使われているハイフンをアンダースコアに置換
            # ウェイト名などの直前にあるハイフンだけを狙い撃ちします
            # 例: "noto-sans-bold" -> "noto-sans_bold"
            # 正規表現を使って、特定のウェイトキーワードの前のハイフンを置換します
            clean_stem = re.sub(
                r'-(bold|medium|normal|thin|light|regular|black|heavy|semibold|extrabold|extralight)',
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


def action_run_batch_merge_font(
    work_dir: str, merge_conf: str = MERGE_CONF_PATH, debug: bool = False, **_
):
    run_batch_merge_font(work_dir=work_dir, merge_conf=merge_conf, debug=debug)


def run_batch_merge_font(
    work_dir: str, merge_conf: str = MERGE_CONF_PATH, debug: bool = False
):
    if not Path(merge_conf).exists():
        print(f"[エラー] CSVファイルが見つかりません: {merge_conf}")
        return

    print(f"\n[マージ一括処理開始]: {merge_conf}")

    # UTF8(BOM付)にしないと、Excelで編集時に文字化けしてしまう。
    with open(merge_conf, "r", encoding="utf_8_sig") as f:
        reader = csv.reader(f)

        try:
            header = next(reader)
            dprint(f"ヘッダー '{header}' をスキップしました", debug)
        except StopIteration:
            return  # 空ファイルの場合

        for row in reader:
            # コメント行や空行、または列が足りない行をスキップ
            if not row or row[0].startswith("#") or len(row) < 3:
                continue

            # 最初の3列をストリップして取得
            vals = [s.strip() for s in row[:3]]
            base, sub, out = vals

            # [修正箇所] sub(補間)は空でもいいが、baseとoutは必須
            if not base or not out:
                continue

            # 1. パス変換の前に「補間フォント」の指定があるかチェック
            is_copy_only = not sub

            # 2. Pathオブジェクトに変換し、work_dirと結合した上で「絶対パス」にする
            # ここで resolve() を使うことで、'str' ではなく 'Path' として扱えます
            base_path = (Path(work_dir) / base.lstrip("/\\")).resolve()
            # 補間フォントがある場合だけsub_pathを生成
            sub_path = None
            if not is_copy_only:
                sub_path = (Path(work_dir) / sub.lstrip("/\\")).resolve()
            out_path = (Path(work_dir) / out.lstrip("/\\")).resolve()

            # もし補間フォント(sub)が空なら、ベースフォント(base)そのまま出力する。
            if is_copy_only:
                try:
                    print(f"\nコピー処理中: {base_path.name}")
                    shutil.copy2(str(base_path), str(out_path))
                    print(f">>  コピー先: {out_path.name}")
                    print("   [成功]")
                    continue
                except Exception as e:
                    print(f"   [失敗] {e}")
                    continue  # 無視して続けます

            print(f"\nマージ処理中: {base_path.name} <- {sub_path.name}")
            print(f">>  出力先: {out_path.name}")

            # # 3. FontForge用にスラッシュ区切りの文字列に変換
            # script_ptr = MERGE_FONT_FF_PATH.resolve().as_posix()
            # base_ptr = base_path.as_posix()
            # sub_ptr = sub_path.as_posix()
            # out_ptr = out_path.as_posix()

            # FontForge呼び出し
            cmd = [
                str(FONTFORGE_PATH),
                "-quiet",
                "-script",
                str(MERGE_FONT_FF_PATH),
                # build/font1/font1_every_premerge.ttf
                str(base_path),
                # build/font2/font2_every_premerge.ttf
                str(sub_path),
                "-o",
                str(out_path),
            ]

            try:
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                print("   [成功]")
            except Exception as e:
                # print(f"   [失敗] ステータスコード: {e.returncode}")
                # print(f"   [FontForgeの生の声]:\n{e.stderr}")
                # print(f"   [標準出力]:\n{e.stdout}")
                print(f"   [失敗] {e}")

    print("\n--- 全てのマージ処理が完了しました ---")


ACTION_MAP = {
    "run_batch_premerge_export": action_run_batch_premerge_export,
    "run_batch_variant_export": action_run_batch_variant_export,
    "run_batch_swf_export": action_run_batch_swf_export,
    "run_batch_merge_font": action_run_batch_merge_font,
}

if __name__ == "__main__":
    main()
