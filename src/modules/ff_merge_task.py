import sys

import fontforge


def run_merge():
    # 引数の取得（script_path自体が0番目なので、実引数は1番目から）
    # fontforge -script task.py base interp out scale_x scale_y
    if len(sys.argv) < 4:
        print("Usage: base_path interp_path output_path [scale_x] [scale_y]")
        sys.exit(1)

    base_path = sys.argv[1]
    interp_path = sys.argv[2]
    output_path = sys.argv[3]

    print("[FF_SCRIPT] Opening base: " + base_path)
    base = fontforge.open(base_path)
    print("[FF_SCRIPT] Opening interp: " + interp_path)
    interp = fontforge.open(interp_path)

    # 既に batch_processor で位置調整済みなら、純粋にマージのみ行う
    # ※ もし将来的に FF 側でスケールしたい場合はここで sys.argv[4] 等を使う

    print("[FF_SCRIPT] Merging fonts...")
    base.mergeFonts(interp_path)  # 不足文字のみを埋める FontForge の標準機能

    print("[FF_SCRIPT] Generating: " + output_path)
    # 32bit loca などの整合性を FF が自動解決して書き出す
    base.generate(output_path)

    base.close()
    interp.close()
    print("[FF_SCRIPT] Done.")


if __name__ == "__main__":
    run_merge()
