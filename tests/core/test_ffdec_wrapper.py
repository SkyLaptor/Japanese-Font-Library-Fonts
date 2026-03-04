import zipfile
from pathlib import Path

import pytest

from const import FFDEC_ARCHIVE_URL, JAVA_ARCHIVE_URL
from core.ffdec_wrapper import (
    build_ffdec_command,
    detect_ffdec_jar,
    detect_java_executable,
    ensure_ffdec_runtime,
    ensure_java_runtime,
)


def test_detect_java_executable_prefers_bundled_java(tmp_path, monkeypatch):
    java_path = tmp_path / "data" / "java" / "bin" / "java"
    java_path.parent.mkdir(parents=True, exist_ok=True)
    java_path.write_text("", encoding="utf-8")
    monkeypatch.setattr("core.ffdec_wrapper.shutil.which", lambda _: "C:/Java/bin/java")
    monkeypatch.setattr("core.ffdec_wrapper._is_java_executable_usable", lambda _: True)
    resolved = detect_java_executable(project_root=tmp_path)
    assert Path(resolved) == java_path


def test_detect_java_executable_fallbacks_to_system_java(tmp_path, monkeypatch):
    monkeypatch.setattr("core.ffdec_wrapper.shutil.which", lambda _: "C:/Java/bin/java")
    monkeypatch.setattr(
        "core.ffdec_wrapper._is_java_executable_usable",
        lambda path: path == "C:/Java/bin/java",
    )

    resolved = detect_java_executable(project_root=tmp_path)
    assert resolved == "C:/Java/bin/java"


def test_detect_java_executable_raises_when_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("core.ffdec_wrapper.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "core.ffdec_wrapper._is_java_executable_usable", lambda _: False
    )
    with pytest.raises(FileNotFoundError):
        detect_java_executable(project_root=tmp_path)


def test_detect_java_executable_fallbacks_when_bundled_unusable(tmp_path, monkeypatch):
    java_path = tmp_path / "data" / "java" / "bin" / "java"
    java_path.parent.mkdir(parents=True, exist_ok=True)
    java_path.write_text("", encoding="utf-8")

    monkeypatch.setattr("core.ffdec_wrapper.shutil.which", lambda _: "C:/Java/bin/java")
    monkeypatch.setattr(
        "core.ffdec_wrapper._is_java_executable_usable",
        lambda path: path == "C:/Java/bin/java",
    )

    resolved = detect_java_executable(project_root=tmp_path)
    assert resolved == "C:/Java/bin/java"


def test_detect_ffdec_jar_prefers_data_ffdec(tmp_path):
    ffdec_jar = tmp_path / "data" / "ffdec" / "ffdec.jar"
    ffdec_jar.parent.mkdir(parents=True, exist_ok=True)
    ffdec_jar.write_text("", encoding="utf-8")

    resolved = detect_ffdec_jar(project_root=tmp_path)
    assert resolved == ffdec_jar


def test_build_ffdec_command_with_explicit_values(tmp_path):
    ffdec_jar = tmp_path / "ffdec.jar"
    ffdec_jar.write_text("", encoding="utf-8")

    cmd = build_ffdec_command(
        ffdec_args=["-replace", "in.swf", "out.swf", "1", "font.ttf"],
        java_executable="java",
        ffdec_jar_path=ffdec_jar,
    )
    assert cmd[:3] == ["java", "-jar", str(ffdec_jar.resolve())]
    assert cmd[3:] == ["-replace", "in.swf", "out.swf", "1", "font.ttf"]


def test_ensure_ffdec_runtime_returns_existing_install(tmp_path):
    ffdec_root = tmp_path / "data" / "ffdec"
    ffdec_root.mkdir(parents=True, exist_ok=True)
    (ffdec_root / "ffdec.jar").write_text("dummy", encoding="utf-8")
    lib_dir = ffdec_root / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    (lib_dir / "dep.jar").write_text("dummy", encoding="utf-8")

    resolved = ensure_ffdec_runtime(project_root=tmp_path)
    assert resolved == ffdec_root / "ffdec.jar"


def test_ensure_ffdec_runtime_downloads_and_deploys(tmp_path, monkeypatch):
    archive_file = tmp_path / "ffdec_test.zip"
    with zipfile.ZipFile(archive_file, "w") as archive:
        archive.writestr("ffdec/ffdec.jar", "jar")
        archive.writestr("ffdec/lib/dependency.txt", "dep")

    def fake_download_file(*, url, output_path, log=None, chunk_size=1024 * 128):
        del url, log, chunk_size
        output_path.write_bytes(archive_file.read_bytes())

    monkeypatch.setattr("core.ffdec_wrapper._download_file", fake_download_file)

    resolved = ensure_ffdec_runtime(project_root=tmp_path, ffdec_archive_url="dummy")

    assert resolved == tmp_path / "data" / "ffdec" / "ffdec.jar"
    assert (tmp_path / "data" / "ffdec" / "ffdec.jar").exists()
    assert (tmp_path / "data" / "ffdec" / "lib").is_dir()
    assert (tmp_path / "data" / "ffdec" / "lib" / "dependency.txt").exists()


def test_ensure_java_runtime_returns_existing_install(tmp_path, monkeypatch):
    java_path = tmp_path / "data" / "java" / "bin" / "java"
    java_path.parent.mkdir(parents=True, exist_ok=True)
    java_path.write_text("dummy", encoding="utf-8")
    monkeypatch.setattr("core.ffdec_wrapper._is_java_executable_usable", lambda _: True)

    resolved = ensure_java_runtime(project_root=tmp_path)
    assert resolved == java_path


def test_ensure_java_runtime_downloads_and_deploys(tmp_path, monkeypatch):
    archive_file = tmp_path / "java_test.zip"
    with zipfile.ZipFile(archive_file, "w") as archive:
        archive.writestr("jdk/bin/java.exe", "java")
        archive.writestr("jdk/lib/dummy.txt", "dep")

    def fake_download_file(*, url, output_path, log=None, chunk_size=1024 * 128):
        del url, log, chunk_size
        output_path.write_bytes(archive_file.read_bytes())

    monkeypatch.setattr("core.ffdec_wrapper._download_file", fake_download_file)
    monkeypatch.setattr("core.ffdec_wrapper._is_java_executable_usable", lambda _: True)

    resolved = ensure_java_runtime(project_root=tmp_path, java_archive_url="dummy")

    assert resolved == tmp_path / "data" / "java" / "bin" / "java.exe"
    assert (tmp_path / "data" / "java" / "bin" / "java.exe").exists()
    assert (tmp_path / "data" / "java" / "lib").is_dir()
    assert (tmp_path / "data" / "java" / "lib" / "dummy.txt").exists()


def test_default_urls_are_loaded_from_const():
    assert FFDEC_ARCHIVE_URL
    assert JAVA_ARCHIVE_URL
