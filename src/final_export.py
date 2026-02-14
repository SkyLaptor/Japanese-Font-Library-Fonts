import subprocess
from pathlib import Path


def run_final_export():
    search_root = Path(r"build").resolve()

    # 定義：生成マトリックス
    # (Baseモード, Condense設定, Subsetファイル名, 識別ラベル)
    matrix = [
        # Everywhere シリーズ
        ("everywhere", "normal", "subset_jp_full.txt", "full"),
        ("everywhere", "condense", "subset_jp_full.txt", "full"),
        ("everywhere", "skinny", "subset_jp_full.txt", "full"),
        ("everywhere", "normal", "subset_jp_skyrim.txt", "skyrim"),
        ("everywhere", "condense", "subset_jp_skyrim.txt", "skyrim"),
        ("everywhere", "skinny", "subset_jp_skyrim.txt", "skyrim"),
        # Book シリーズ
        ("book", "normal", "subset_jp_full.txt", "full"),
        ("book", "normal", "subset_jp_skyrim.txt", "skyrim"),
        # Handwritten シリーズ
        ("handwritten", "normal", "subset_jp_full.txt", "full"),
        ("handwritten", "normal", "subset_jp_skyrim.txt", "skyrim"),
    ]

    # build ディレクトリ内の各フォルダを探索
    for font_dir in search_root.iterdir():
        if not font_dir.is_dir():
            continue

        # マージ済みファイル（-merged.ttf）を探す
        merged_fonts = list(font_dir.glob("*-merged.ttf"))
        if not merged_fonts:
            continue

        target_font = merged_fonts[0]
        print(f"\n[FINAL BUILD]: {font_dir.name}")

        for base, condense, subset_file, label in matrix:
            subset_path = Path(f"data/subsets/{subset_file}")

            # 出力ファイル名の組み立て
            # 例: fontname-merged-everywhere-normal-full.ttf
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

            print(f"  -> Generating: {out_name}...")

            try:
                # すでに batch_harmonize でパスの問題が解決していれば直接実行でOK
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"  [ERROR]: {out_name} の生成に失敗しました。")

    print("\n--- 全バリエーションのエクスポートが完了しました！ ---")


if __name__ == "__main__":
    run_final_export()
