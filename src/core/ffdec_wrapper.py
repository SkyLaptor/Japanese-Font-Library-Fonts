import os
import shlex
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Callable
from urllib import request

from const import FFDEC_ARCHIVE_URL, JAVA_ARCHIVE_URL


def _get_project_root(project_root: str | Path | None = None) -> Path:
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[2]


def _is_windows() -> bool:
    return os.name == "nt"


def _candidate_java_paths(java_root: Path) -> list[Path]:
    candidates = [
        java_root / "bin" / "java.exe",
        java_root / "bin" / "java",
    ]
    if _is_windows():
        candidates.append(java_root / "java.exe")
    else:
        candidates.append(java_root / "java")
    return candidates


def _is_java_executable_usable(java_executable: str) -> bool:
    try:
        result = subprocess.run(
            [java_executable, "-version"],
            check=False,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except OSError:
        return False


def _ffdec_runtime_ready(ffdec_root: Path) -> bool:
    ffdec_jar = ffdec_root / "ffdec.jar"
    ffdec_lib = ffdec_root / "lib"
    if not ffdec_jar.exists():
        return False
    if not ffdec_lib.exists() or not ffdec_lib.is_dir():
        return False
    return any(ffdec_lib.iterdir())


def _java_runtime_ready(java_root: Path) -> bool:
    for java_path in _candidate_java_paths(java_root):
        if java_path.exists() and _is_java_executable_usable(str(java_path)):
            return True
    return False


def _download_file(
    *,
    url: str,
    output_path: Path,
    log: Callable[[str], None] | None = None,
    chunk_size: int = 1024 * 128,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url) as response, output_path.open("wb") as output_file:
        total = int(response.headers.get("Content-Length", "0") or "0")
        downloaded = 0

        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            output_file.write(chunk)
            downloaded += len(chunk)
            if log is not None and total > 0:
                percent = int((downloaded / total) * 100)
                log(f"[起動] 実行環境を準備中... FFDecダウンロード {percent}%")


def _deploy_ffdec_archive(
    *, archive_path: Path, ffdec_root: Path, log: Callable[[str], None] | None = None
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)

        candidates = sorted(
            extract_dir.rglob("ffdec.jar"), key=lambda path: len(str(path))
        )
        if not candidates:
            raise FileNotFoundError(
                "ダウンロードしたアーカイブ内に ffdec.jar が見つかりません。"
            )

        discovered_jar = candidates[0]
        source_root = discovered_jar.parent
        source_lib = source_root / "lib"
        if not source_lib.exists() or not source_lib.is_dir():
            raise FileNotFoundError(
                "ダウンロードしたアーカイブ内に FFDec 依存ライブラリ(lib)が見つかりません。"
            )

        ffdec_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(discovered_jar, ffdec_root / "ffdec.jar")
        shutil.copytree(source_lib, ffdec_root / "lib", dirs_exist_ok=True)

        optional_files = ["ffdec-cli.jar", "ffdec-cli.exe", "ffdec.exe", "ffdec.bat"]
        for file_name in optional_files:
            source_file = source_root / file_name
            if source_file.exists() and source_file.is_file():
                shutil.copy2(source_file, ffdec_root / file_name)

        if log is not None:
            log("[起動] FFDec 配備完了: data/ffdec")


def _deploy_java_archive(
    *, archive_path: Path, java_root: Path, log: Callable[[str], None] | None = None
) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_dir)

        java_candidates = sorted(
            [
                path
                for path in extract_dir.rglob("*")
                if path.is_file() and path.name.lower() in {"java.exe", "java"}
            ],
            key=lambda path: len(str(path)),
        )

        if not java_candidates:
            raise FileNotFoundError(
                "ダウンロードしたアーカイブ内に Java 実行ファイルが見つかりません。"
            )

        preferred_java = next(
            (path for path in java_candidates if path.parent.name.lower() == "bin"),
            java_candidates[0],
        )

        source_root = (
            preferred_java.parent.parent
            if preferred_java.parent.name.lower() == "bin"
            else preferred_java.parent
        )

        if java_root.exists():
            shutil.rmtree(java_root)
        shutil.copytree(source_root, java_root)

        if not _java_runtime_ready(java_root):
            raise FileNotFoundError(
                "ダウンロードしたJavaランタイムの展開後に Java 実行ファイルを利用できません。"
            )

        if log is not None:
            log("[起動] Javaランタイム 配備完了: data/java")

    for java_path in _candidate_java_paths(java_root):
        if java_path.exists() and _is_java_executable_usable(str(java_path)):
            return java_path

    raise FileNotFoundError(
        "展開後のJavaランタイムに有効な Java 実行ファイルが見つかりません。"
    )


def ensure_ffdec_runtime(
    project_root: str | Path | None = None,
    *,
    ffdec_archive_url: str | None = None,
    log: Callable[[str], None] | None = None,
) -> Path:
    root = _get_project_root(project_root)
    ffdec_root = root / "data" / "ffdec"

    if _ffdec_runtime_ready(ffdec_root):
        if log is not None:
            log("[起動] FFDec 確認: 配備済み")
        return ffdec_root / "ffdec.jar"

    url = ffdec_archive_url or os.environ.get(
        "JFL_FFDEC_ARCHIVE_URL", FFDEC_ARCHIVE_URL
    )

    if log is not None:
        log("[起動] 実行環境を準備中... FFDecを自動ダウンロードします")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "ffdec.zip"
        _download_file(url=url, output_path=archive_path, log=log)
        _deploy_ffdec_archive(archive_path=archive_path, ffdec_root=ffdec_root, log=log)

    if not _ffdec_runtime_ready(ffdec_root):
        raise FileNotFoundError(
            "FFDecの自動配備後も ffdec.jar / lib が不足しています。"
        )

    return ffdec_root / "ffdec.jar"


def ensure_java_runtime(
    project_root: str | Path | None = None,
    *,
    java_archive_url: str | None = None,
    log: Callable[[str], None] | None = None,
) -> Path:
    root = _get_project_root(project_root)
    java_root = root / "data" / "java"

    if _java_runtime_ready(java_root):
        if log is not None:
            log("[起動] Javaランタイム 確認: 配備済み (data/java)")
        for java_path in _candidate_java_paths(java_root):
            if java_path.exists() and _is_java_executable_usable(str(java_path)):
                return java_path

    url = java_archive_url or os.environ.get("JFL_JAVA_ARCHIVE_URL", JAVA_ARCHIVE_URL)

    if log is not None:
        log("[起動] 実行環境を準備中... Javaランタイムを自動ダウンロードします")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        archive_path = temp_path / "java_runtime.zip"
        _download_file(url=url, output_path=archive_path, log=log)
        java_path = _deploy_java_archive(
            archive_path=archive_path,
            java_root=java_root,
            log=log,
        )

    return java_path


def detect_java_executable(project_root: str | Path | None = None) -> str:
    root = _get_project_root(project_root)
    bundled_java_root = root / "data" / "java"
    unusable_candidates: list[str] = []

    for java_path in _candidate_java_paths(bundled_java_root):
        if java_path.exists() and _is_java_executable_usable(str(java_path)):
            return str(java_path)
        if java_path.exists():
            unusable_candidates.append(str(java_path))

    system_java = shutil.which("java")
    if system_java and _is_java_executable_usable(system_java):
        return system_java

    if system_java:
        unusable_candidates.append(system_java)

    raise FileNotFoundError(
        "Java実行ファイルが見つかりません。data/java/bin/java(.exe) を配置するか、"
        "フォールバック用にシステムPATHへJavaを追加してください。"
        + (
            f" 使用不能な候補: {', '.join(unusable_candidates)}"
            if unusable_candidates
            else ""
        )
    )


def detect_ffdec_jar(project_root: str | Path | None = None) -> Path:
    root = _get_project_root(project_root)
    ffdec_jar_path = root / "data" / "ffdec" / "ffdec.jar"
    if ffdec_jar_path.exists():
        return ffdec_jar_path

    raise FileNotFoundError(
        "ffdec.jar が見つかりません。data/ffdec/ffdec.jar に配置してください。"
    )


def build_ffdec_command(
    ffdec_args: list[str],
    project_root: str | Path | None = None,
    java_executable: str | None = None,
    ffdec_jar_path: str | Path | None = None,
) -> list[str]:
    resolved_java = java_executable or detect_java_executable(project_root)
    resolved_jar = (
        Path(ffdec_jar_path).resolve()
        if ffdec_jar_path is not None
        else detect_ffdec_jar(project_root)
    )
    # ヒープ不足回避のため、環境変数からJavaオプションを差し込めるようにする。
    # 優先度: JFL_JAVA_OPTS > JFL_JAVA_MAX_HEAP_MB
    java_opts: list[str] = []
    opts_env = os.environ.get("JFL_JAVA_OPTS")
    if opts_env:
        try:
            java_opts = shlex.split(opts_env)
        except Exception:
            # 単純分割の後方互換
            java_opts = [x for x in opts_env.split(" ") if x]
    else:
        max_mb = os.environ.get("JFL_JAVA_MAX_HEAP_MB") or os.environ.get(
            "_JAVA_MAX_HEAP_MB"
        )
        if max_mb:
            try:
                mb_val = int(max_mb)
                if mb_val > 0:
                    java_opts.append(f"-Xmx{mb_val}m")
            except Exception:
                pass

    return [resolved_java, *java_opts, "-jar", str(resolved_jar), *ffdec_args]


def run_ffdec(
    ffdec_args: list[str],
    project_root: str | Path | None = None,
    java_executable: str | None = None,
    ffdec_jar_path: str | Path | None = None,
    check: bool = True,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    cmd = build_ffdec_command(
        ffdec_args=ffdec_args,
        project_root=project_root,
        java_executable=java_executable,
        ffdec_jar_path=ffdec_jar_path,
    )
    if os.environ.get("JFL_LOG_FFDEC_CMD"):
        try:
            print("[FFDec] Command:", " ".join(cmd))
        except Exception:
            pass
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture_output,
        text=text,
    )


def ffdec_replace(
    input_swf_path: str,
    output_swf_path: str,
    character_id: int,
    input_font_path: str,
    project_root: str | Path | None = None,
    java_executable: str | None = None,
    ffdec_jar_path: str | Path | None = None,
) -> subprocess.CompletedProcess:
    return run_ffdec(
        ffdec_args=[
            "-replace",
            input_swf_path,
            output_swf_path,
            str(character_id),
            input_font_path,
        ],
        project_root=project_root,
        java_executable=java_executable,
        ffdec_jar_path=ffdec_jar_path,
    )


def ffdec_export(
    export_item: str,
    output_dir: str,
    input_swf_path: str,
    project_root: str | Path | None = None,
    java_executable: str | None = None,
    ffdec_jar_path: str | Path | None = None,
) -> subprocess.CompletedProcess:
    return run_ffdec(
        ffdec_args=["-export", export_item, output_dir, input_swf_path],
        project_root=project_root,
        java_executable=java_executable,
        ffdec_jar_path=ffdec_jar_path,
    )
