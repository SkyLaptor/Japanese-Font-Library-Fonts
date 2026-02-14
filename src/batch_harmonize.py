import subprocess
from pathlib import Path


def run_batch_harmonize():
    """
    異なるフォント同士をマージする前の事前調整を一括で行う。

    以下の順で処理される。
    1. 空白グリフ削除: 先に消しておかないと、UPM変更時に正しい拡大縮小率を得られない。
    2. UPM変更:とりあえずバニラEverywhere(UPM1024)基準にする。他のheadタグ情報も書き換わるが本処理時に上書きされるため特に影響なし。
    なお、バニラフォントは全てUPM1024である。
    3. 上下オフセット適用: フォントによって適正値が異なるため、各フォントディレクトリ直下の `offset_height_everywhere.txt` を読んで設定する。
    オフセット値はバニラのフォントと合わせると上にずれるため、lore-friendly-everywhereとアウトラインの下部を揃えることを目標とする。
    オフセット値は大事なデータであるため不用意に消さない事。

    特定のディレクトリ（search_root）内のTTFを総当たりする。

    """
    # ベースフォントの定義
    base_fonts = {
        "everywhere": Path(r"data\basefonts\1_Skyrim_JP_EveryFont_0805.ttf").resolve(),
        # "book": Path(r"data\basefonts\22_Skyrim_JP_BookFont_0805.ttf").resolve(),
        # "handwritten": Path(
        #    r"data\basefonts\5_Skyrim_JP_HandWriteFont_0805.ttf"
        # ).resolve(),
    }

    # search_root = Path(r"assets\fonts").resolve()
    search_root = Path(r"build").resolve()

    for font_path in search_root.rglob("*.ttf"):
        # skyrim フォルダ除外
        # if "skyrim" in font_path.parts:
        #     continue

        # 生成済みファイル除外
        # if any(
        #     suffix in font_path.name
        #     for suffix in ["-everywhere", "-book", "-handwritten"]
        # ):
        #     continue

        print(f"\n[PROCESS]: {font_path.name}")

        for mode, base_path in base_fonts.items():
            # --- モード別オフセットの読み込み ---
            # 例: offset_height_everywhere.txt を探す
            offset_value = "0"
            config_filename = f"offset_height_{mode}.txt"
            offset_file = font_path.parent / config_filename

            if offset_file.exists():
                try:
                    content = offset_file.read_text().strip()
                    if content:
                        offset_value = content
                        print(
                            f"  [CONFIG]: {config_filename} を適用 -> Offset: {offset_value}"
                        )
                except Exception:
                    print(
                        f"  [WARNING]: {config_filename} の読み込みに失敗。0を使用します。"
                    )

            # output_name = f"{font_path.stem}-{mode}.ttf"
            output_name = f"{font_path.stem}-premerge.ttf"
            output_path = font_path.parent / output_name

            def long_path(p):
                return f"\\\\?\\{p}"

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
                offset_value,
            ]
            # print(f"command: {cmd}")

            print(f"  -> {mode} 生成開始...")

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"  [ERROR]: {output_name} 生成失敗")
                print(f"  {e.stderr[:200]}")

    print("\n--- 全ての個別オフセット処理が完了しました！ ---")


if __name__ == "__main__":
    run_batch_harmonize()
