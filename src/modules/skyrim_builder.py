# Dependencies: FFDec=True, FontForge=False
import csv
import shutil
from pathlib import Path

from modules.merge_font import action_merge_font
from utils.dprint import dprint

DEFAULT_MERGE_CONF_PATH = Path(__file__).resolve().parents[2] / "merge_conf.csv"


def dispatch_action(action, **kwargs):
    handler = ACTION_MAP.get(action)
    if handler:
        handler(**kwargs)
    else:
        print(f"未実装のアクションです: {action}")


def action_merge_fonts(
    work_dir: str,
    merge_conf: str = str(DEFAULT_MERGE_CONF_PATH),
    debug: bool = False,
    **_,
):
    merge_font(work_dir=work_dir, merge_conf=merge_conf, debug=debug)


def merge_font(
    work_dir: str, merge_conf: str = str(DEFAULT_MERGE_CONF_PATH), debug: bool = False
):
    if not Path(merge_conf).exists():
        print(f"[エラー] CSVファイルが見つかりません: {merge_conf}")
        return

    print(f"\n[マージ一括処理開始]: {merge_conf}")

    with open(merge_conf, "r", encoding="utf_8_sig") as f:
        reader = csv.reader(f)

        try:
            header = next(reader)
            dprint(f"ヘッダー '{header}' をスキップしました", debug)
        except StopIteration:
            return

        for row in reader:
            if not row or row[0].startswith("#") or len(row) < 3:
                continue

            vals = [s.strip() for s in row[:3]]
            base, sub, out = vals
            if not base or not out:
                continue

            is_copy_only = not sub

            base_path = (Path(work_dir) / base.lstrip("/\\")).resolve()
            sub_path = None
            if not is_copy_only:
                sub_path = (Path(work_dir) / sub.lstrip("/\\")).resolve()
            out_path = (Path(work_dir) / out.lstrip("/\\")).resolve()

            if is_copy_only:
                try:
                    print(f"\nコピー処理中: {base_path.name}")
                    shutil.copy2(str(base_path), str(out_path))
                    print(f">>  コピー先: {out_path.name}")
                    print("   [成功]")
                    continue
                except Exception as e:
                    print(f"   [失敗] {e}")
                    continue

            print(f"\nマージ処理中: {base_path.name} <- {sub_path.name}")
            print(f">>  出力先: {out_path.name}")

            try:
                action_merge_font(
                    base_path=str(base_path),
                    interpolation_path=str(sub_path),
                    output_path=str(out_path),
                    debug=debug,
                )
                print("   [成功]")
            except Exception as e:
                print(f"   [失敗] {e}")

    print("\n--- 全てのマージ処理が完了しました ---")


ACTION_MAP = {
    "merge_font": action_merge_fonts,
}
