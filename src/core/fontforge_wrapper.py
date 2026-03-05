import subprocess
from pathlib import Path


def _get_project_root() -> Path:
    # ファイル位置からプロジェクトルート (src/utils/.. -> root) を取得
    return Path(__file__).resolve().parents[2]


def detect_fontforge_executable(project_root: Path | None = None) -> Path:
    """
    data/fontforge/bin/fontforge.exe を検出します。
    """
    root = project_root or _get_project_root()
    ff_exe = root / "data" / "fontforge" / "bin" / "fontforge.exe"

    if ff_exe.exists():
        return ff_exe

    raise FileNotFoundError(
        f"FontForgeが見つかりません: {ff_exe}\n"
        "data/fontforge/ 配下にポータブル版を展開してください。"
    )


def run_fontforge_script(
    script_path: str | Path,
    args: list[str],
    project_root: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    ff_exe = detect_fontforge_executable(project_root)

    # パスに含まれるバックスラッシュをスラッシュに置換（FontForge内部でのエスケープ誤認防止）
    cmd = [
        str(ff_exe),
        "-quiet",
        "-lang=py",
        "-script",
        str(Path(script_path).resolve()).replace("\\", "/"),
    ] + [str(a).replace("\\", "/") for a in args]

    # encoding="cp932", errors="replace" でデコード失敗による停止を確実に防ぐ
    return subprocess.run(
        cmd,
        check=check,
        capture_output=True,
        text=True,
        encoding="cp932",
        errors="replace",
    )


def ff_merge_fonts(
    base_path: str | Path,
    interp_path: str | Path,
    output_path: str | Path,
    scale_x: float = 1.0,
    scale_y: float = 1.0,
    project_root: Path | None = None,
) -> subprocess.CompletedProcess:
    """
    指定したスクリプトを使用してフォントをマージします。
    """
    root = project_root or _get_project_root()
    # マージ用スクリプトのパス
    task_script = root / "src" / "modules" / "ff_merge_task.py"

    if not task_script.exists():
        raise FileNotFoundError(f"マージスクリプトが見つかりません: {task_script}")

    # スクリプトに渡す引数（すべて文字列にする必要がある）
    script_args = [
        str(Path(base_path).resolve()),
        str(Path(interp_path).resolve()),
        str(Path(output_path).resolve()),
        str(scale_x),
        str(scale_y),
    ]

    print("[FontForge] マージを開始します...")
    return run_fontforge_script(task_script, script_args, project_root=root)


def _main_test():
    """
    python -m src.utils.fontforge_wrapper で実行される動作確認用テスト
    """
    import sys

    print("=== FontForge Wrapper Self-Test ===")

    try:
        # 1. 実行ファイルの検出テスト
        exe_path = detect_fontforge_executable()
        print(f"✅ Found FontForge: {exe_path}")

        # 2. バージョン取得テスト (直接 -version を叩く)
        print("--- Testing Version Check ---")
        res = subprocess.run(
            [str(exe_path), "-version"], capture_output=True, text=True
        )
        print(f"FontForge Output:\n{res.stdout.strip()}")

        # 3. 内部スクリプト実行テスト (インラインで簡易スクリプトを投げる)
        print("--- Testing Script Execution ---")
        # 一時的にインラインスクリプトを作成して実行
        test_py = "import fontforge; print('SUCCESS: FontForge Python is alive!')"
        test_script_path = Path("temp_ff_test.py")
        test_script_path.write_text(test_py, encoding="utf-8")

        try:
            res_script = run_fontforge_script(test_script_path, [])
            print(res_script.stdout.strip())
        finally:
            if test_script_path.exists():
                test_script_path.unlink()

        print("=== Wrapper Test Passed! ===")

    except Exception as e:
        print(f"❌ Wrapper Test Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    _main_test()
