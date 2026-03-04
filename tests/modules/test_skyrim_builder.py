from pathlib import Path

import modules.skyrim_builder as skyrim_builder_module


def test_action_map_supports_merge_font_only():
    assert list(skyrim_builder_module.ACTION_MAP.keys()) == ["merge_font"]


def test_dispatch_action_calls_handler(monkeypatch):
    called: dict[str, object] = {}

    def fake_handler(**kwargs):
        called.update(kwargs)

    monkeypatch.setitem(skyrim_builder_module.ACTION_MAP, "merge_font", fake_handler)

    skyrim_builder_module.dispatch_action(
        action="merge_font", work_dir="dummy", debug=True, extra_flag=True
    )

    assert called["work_dir"] == "dummy"
    assert called["debug"] is True
    assert called["extra_flag"] is True


def test_dispatch_action_unknown_action_prints_message(capsys):
    skyrim_builder_module.dispatch_action(action="unknown_action")

    captured = capsys.readouterr()
    assert "未実装のアクションです: unknown_action" in captured.out


def test_merge_font_runs_copy_and_merge_rows(tmp_path, monkeypatch):
    work_dir = tmp_path / "work"
    work_dir.mkdir()

    base_path = work_dir / "base.ttf"
    sub_path = work_dir / "sub.ttf"
    copy_src_path = work_dir / "copy_src.ttf"
    base_path.write_bytes(b"base")
    sub_path.write_bytes(b"sub")
    copy_src_path.write_bytes(b"copy")

    merge_conf = work_dir / "merge_conf.csv"
    merge_conf.write_text(
        "base,sub,out\n" "copy_src.ttf,,copied.ttf\n" "base.ttf,sub.ttf,merged.ttf\n",
        encoding="utf-8",
    )

    called = {"value": False}

    def fake_action_merge_font(
        *, base_path: str, interpolation_path: str, output_path: str, debug: bool
    ):
        called["value"] = True
        assert Path(base_path).name == "base.ttf"
        assert Path(interpolation_path).name == "sub.ttf"
        Path(output_path).write_bytes(b"merged")

    monkeypatch.setattr(
        skyrim_builder_module, "action_merge_font", fake_action_merge_font
    )

    skyrim_builder_module.merge_font(
        str(work_dir), merge_conf=str(merge_conf), debug=True
    )

    assert (work_dir / "copied.ttf").read_bytes() == b"copy"
    assert (work_dir / "merged.ttf").read_bytes() == b"merged"
    assert called["value"] is True
