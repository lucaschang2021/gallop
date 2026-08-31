import hashlib
import json
import os
from pathlib import Path

import pytest

from gallop.mobile import export_mobile


@pytest.fixture(params=["missing-reader", "existing-empty-reader"])
def paths(tmp_path, request):
    source = tmp_path / "Main"
    (source / ".obsidian").mkdir(parents=True)
    target = tmp_path / "Gallop-Reader"
    if request.param == "existing-empty-reader":
        target.mkdir()
    return source, target, tmp_path / "local-state"


def put(root, name, body):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


def test_privacy_and_source_unchanged(paths):
    source, target, state = paths
    allowed = ["01-Mathematics/Sessions/lesson.md", "Practice/learner/problem.md",
               "Papers/paper.md", "Research/idea.md", "Gallop/Sessions/session.md"]
    for name in allowed:
        put(source, name, "# Safe lesson\nA mathematical note.")
    rejected = {
        "00-System/DeepTutor/mastery-state.json": '{"mastery": 2}',
        "logs/run.md": "private log", "Papers/manifest.md": "private manifest",
        "Research/config.md": "private configuration",
        "Research/oauth.md": "private OAuth",
        "Research/.env": "private environment",
        "Research/file.pdf": "opaque attachment",
        "Research/secret.md": "private secret",
        "Research/normal.md": "access_token: FAKE_TEST_VALUE",
        "Research/hidden.md": "mobile_export: false\nPrivate note",
        "Practice/integration_tests/run.md": "Synthetic",
        "01-Mathematics/Concepts/Integration Tests/run.md": "Synthetic",
        "01-Mathematics/Practice/DeepTutor/run.md": "integration_test: true\nSynthetic",
        "Gallop/Practice/integration_tests/run.md": "Synthetic",
        "Research/DeepTutor/sessions/run.md": "Backend session",
        # Assemble the fake marker at runtime so repository auditing can remain strict.
        "Research/keymaterial.md": "-----BEGIN " + "PRIVATE KEY-----\nfake",
        "Research/json-note.md": '{"refresh_token": "FAKE"}',
    }
    for name, body in rejected.items():
        put(source, name, body)
    before = snapshot(source)
    report = export_mobile(*paths)
    assert report["reading_notes"] == len(allowed)
    assert set(snapshot(target)) == set(allowed) | {"Today.md", "Mobile Sync Check.md"}
    assert snapshot(source) == before
    assert not (target / "receipt.json").exists()
    assert (target / "Today.md").read_text(encoding="utf-8").startswith(f"# {target.name}\n")
    assert target.name in (target / "Mobile Sync Check.md").read_text(encoding="utf-8")


def test_repeat_and_mobile_conflict_main_wins(paths):
    source, target, state = paths
    put(source, "Research/note.md", "Canonical")
    export_mobile(*paths)
    assert export_mobile(*paths)["written"] == 0
    put(target, "Research/note.md", "Phone edit")
    export_mobile(*paths)
    assert (target / "Research/note.md").read_text() == "Canonical"
    assert any(p.read_text() == "Phone edit" for p in (state / "backups").rglob("note.md"))
    assert (source / "Research/note.md").read_text() == "Canonical"


def test_newly_sensitive_export_is_retired_to_local_backup(paths):
    source, target, state = paths
    put(source, "Research/note.md", "Safe original")
    export_mobile(*paths)
    put(target, "Personal.md", "Not owned")
    put(source, "Research/note.md", "password: FAKE")
    report = export_mobile(*paths)
    assert report["quarantined"] == 1
    assert not (target / "Research/note.md").exists()
    assert (target / "Personal.md").read_text() == "Not owned"
    assert all("FAKE" not in p.read_text(encoding="utf-8") for p in target.rglob("*.md"))


def test_new_name_conflict_backs_up_phone_and_main_wins(paths):
    source, target, state = paths
    export_mobile(*paths)
    put(target, "Research/new.md", "Phone only")
    put(source, "Research/new.md", "Main only")
    export_mobile(*paths)
    assert (target / "Research/new.md").read_text() == "Main only"
    assert any(p.read_text() == "Phone only" for p in (state / "backups").rglob("new.md"))


def test_dry_run_has_no_writes(paths):
    source, target, state = paths
    put(source, "Research/note.md", "Safe")
    existed = target.exists()
    before = snapshot(target)
    assert export_mobile(*paths, dry_run=True)["reading_notes"] == 1
    assert target.exists() == existed and snapshot(target) == before
    assert not state.exists()


def test_initial_nonempty_target_refused(paths):
    _, target, _ = paths
    put(target, "Personal.md", "Unowned")
    with pytest.raises(ValueError):
        export_mobile(*paths)


def test_overlap_refused(paths):
    source, target, state = paths
    with pytest.raises(ValueError):
        export_mobile(source, source / "Gallop-Reader", state)
    with pytest.raises(ValueError):
        export_mobile(source, target, target / "state")
    with pytest.raises(ValueError):
        export_mobile(source, target, source / "state")


def test_hardlinked_source_excluded(paths):
    source, target, _ = paths
    original = put(source, "00-System/private.md", "Private")
    (source / "Research").mkdir()
    os.link(original, source / "Research/alias.md")
    assert export_mobile(*paths)["reading_notes"] == 0
    assert not (target / "Research/alias.md").exists()


def test_managed_path_escape_refused(paths):
    _, _, state = paths
    export_mobile(*paths)
    receipt = state / "receipt.json"
    data = json.loads(receipt.read_text())
    data["files"].append("../outside.md")
    receipt.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        export_mobile(*paths)


def test_missing_source_root_does_not_prune(paths):
    source, target, state = paths
    export_mobile(*paths)
    before = snapshot(target)
    with pytest.raises(ValueError):
        export_mobile(source / "missing", target, state)
    assert snapshot(target) == before


def test_cli_skips_backend_configuration(paths, monkeypatch, tmp_path):
    from gallop.cli import main
    def forbidden(*args, **kwargs):
        raise AssertionError("Backend configuration must not be loaded")
    monkeypatch.setattr("gallop.cli.load_env", forbidden)
    args = ["mobile-export"]
    for flag, value in zip(("--source", "--target", "--state"), paths):
        args.extend([flag, str(value)])
    assert main(args) == 0


def test_lock_refuses_second_writer(paths):
    source, target, state = paths
    export_mobile(*paths)
    before = snapshot(target)
    put(state, "export.lock", "")
    with pytest.raises(FileExistsError):
        export_mobile(*paths)
    assert snapshot(target) == before


def test_no_settings_or_hidden_configuration_exported(paths):
    source, target, _ = paths
    put(source, ".obsidian/app.json", '{"theme":"dark"}')
    put(source, "Research/.obsidian/private.md", "Private settings")
    put(source, "Research/.hidden.md", "Private hidden note")
    put(source, "Research/.mobile-interrupted", "Interrupted temporary write")
    put(source, "Research/reading.md", "Reading")
    export_mobile(*paths)
    assert not (target / ".obsidian").exists()
    assert set(snapshot(target)) == {"Research/reading.md", "Today.md", "Mobile Sync Check.md"}
    assert (source / ".obsidian/app.json").exists()


def test_only_empty_legacy_mobile_settings_removed(paths):
    _, target, _ = paths
    (target / ".obsidian").mkdir(parents=True)
    assert export_mobile(*paths)["removed_empty_settings"] == 1
    assert not (target / ".obsidian").exists()
    put(target, ".obsidian/app.json", '{"phone":"settings"}')
    assert export_mobile(*paths)["removed_empty_settings"] == 0
    assert (target / ".obsidian/app.json").read_text() == '{"phone":"settings"}'


def test_temporary_files_never_created_inside_mobile(paths, monkeypatch):
    import gallop.mobile as mobile
    source, target, state = paths
    put(source, "Research/reading.md", "Reading")
    actual = mobile.tempfile.mkstemp
    locations = []
    def observe(*args, **kwargs):
        location = Path(kwargs["dir"]).resolve()
        assert target not in (location, *location.parents)
        locations.append(location)
        return actual(*args, **kwargs)
    monkeypatch.setattr(mobile.tempfile, "mkstemp", observe)
    export_mobile(*paths)
    assert state / "staging" in locations
    assert not list(target.rglob(".mobile-*"))


def test_unready_cloud_parent_stops_before_publishing(paths, monkeypatch):
    import gallop.mobile as mobile
    source, target, state = paths
    put(source, "Research/reading.md", "Reading")
    def reject(path):
        raise mobile.CloudNotReady("Provider parent missing")
    monkeypatch.setattr(mobile, "wait_cloud_directory", reject)
    with pytest.raises(mobile.CloudNotReady):
        export_mobile(*paths, icloud_safe=True)
    assert not list(target.rglob("*.md"))
    assert not (state / "receipt.json").exists()
    assert not (state / "export.lock").exists()


def test_cloud_parents_acknowledged_before_children(paths, monkeypatch):
    import gallop.mobile as mobile
    source, target, _ = paths
    put(source, "Research/Topic/reading.md", "Reading")
    confirmed = []
    def confirm(path):
        assert path.is_dir()
        assert not list(target.rglob("*.md"))
        if path != target:
            assert path.parent in confirmed
        confirmed.append(path)
    monkeypatch.setattr(mobile, "wait_cloud_directory", confirm)
    export_mobile(*paths, icloud_safe=True)
    assert confirmed == [target, target / "Research", target / "Research/Topic"]


def test_refresh_republishes_with_local_backup(paths):
    source, target, state = paths
    put(source, "Research/note.md", "Source")
    export_mobile(*paths)
    before = snapshot(source)
    result = export_mobile(*paths, refresh=True)
    assert result["written"] == 3
    assert result["unchanged"] == 0
    assert (target / "Research/note.md").read_text() == "Source"
    assert any(p.read_text() == "Source" for p in (state / "backups").rglob("note.md"))
    assert snapshot(source) == before


def test_failed_publish_preserves_old_reading_file(paths, monkeypatch):
    import gallop.mobile as mobile
    source, target, state = paths
    put(source, "Research/note.md", "Old")
    export_mobile(*paths)
    put(source, "Research/note.md", "New")
    original = mobile.os.replace
    def fail(src, dst):
        if Path(dst) == target / "Research/note.md":
            raise PermissionError("Simulated cloud file lock")
        return original(src, dst)
    monkeypatch.setattr(mobile.os, "replace", fail)
    with pytest.raises(PermissionError):
        export_mobile(*paths)
    assert (target / "Research/note.md").read_text() == "Old"
    assert not list((state / "staging").iterdir())
    assert not (state / "export.lock").exists()


@pytest.mark.parametrize("name", ["Research/invalid?.md", "Research/NUL.md",
                                    "Research/data.nosync/note.md", "Research/folder./note.md"])
def test_unsafe_cloud_names_rejected(paths, name):
    from gallop.mobile import cloud_safe_name
    with pytest.raises(ValueError):
        cloud_safe_name(paths[1], name)


def test_long_cloud_path_rejected(paths):
    from gallop.mobile import cloud_safe_name
    with pytest.raises(ValueError):
        cloud_safe_name(paths[1], "Research/" + "a" * 250 + ".md")


@pytest.mark.skipif(os.name != "nt", reason="Windows hidden file attributes")
def test_windows_hidden_attribute_excluded(paths):
    import ctypes
    from ctypes import wintypes
    source, target, _ = paths
    note = put(source, "Research/ordinary-name.md", "Hidden by filesystem attribute")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
    kernel.SetFileAttributesW.restype = wintypes.BOOL
    assert kernel.SetFileAttributesW(str(note), 2)
    try:
        assert export_mobile(*paths)["reading_notes"] == 0
        assert not (target / "Research/ordinary-name.md").exists()
    finally:
        kernel.SetFileAttributesW(str(note), 128)


def test_root_markdown_recreation_creates_fresh_file_object(paths):
    source, target, state = paths
    put(source, "Research/note.md", "Canonical reading")
    export_mobile(*paths)
    put(target, ".obsidian/app.json", '{"phone":"keep"}')
    original_receipt = json.loads((state / "receipt.json").read_text())
    other_before = {p.relative_to(target).as_posix(): (p.stat().st_ino, p.read_bytes())
                    for p in target.rglob("*") if p.is_file()
                    and p.name not in {"Today.md", "Mobile Sync Check.md"}}
    old_ids = {}
    # Keep old objects alive in an isolated test backup while new ones are created.
    for name in ("Today.md", "Mobile Sync Check.md"):
        path = target / name
        old_ids[name] = path.stat().st_ino
        path.rename(state / (name + ".old"))
    before_source = snapshot(source)
    result = export_mobile(*paths, create_root_notes=True)
    assert result["written"] == 2 and result["quarantined"] == 0
    assert all((target / name).stat().st_ino != old_id for name, old_id in old_ids.items())
    assert other_before == {p.relative_to(target).as_posix(): (p.stat().st_ino, p.read_bytes())
                            for p in target.rglob("*") if p.is_file()
                            and p.name not in old_ids}
    assert json.loads((state / "receipt.json").read_text()) == original_receipt
    assert snapshot(source) == before_source
    with pytest.raises(FileExistsError):
        export_mobile(*paths, create_root_notes=True)


def test_root_export_never_reuses_old_staging_or_sync_object(paths):
    from gallop.mobile import atomic_bytes
    source, target, state = paths
    export_mobile(*paths)
    stale = put(state, "staging/.mobile-interrupted", "STALE CORRUPT PAYLOAD")
    old_id = stale.stat().st_ino
    for name in ("Today.md", "Mobile Sync Check.md"):
        (target / name).unlink()
    export_mobile(*paths, create_root_notes=True)
    for name in ("Today.md", "Mobile Sync Check.md"):
        path = target / name
        assert path.stat().st_ino != old_id
        assert b"STALE CORRUPT PAYLOAD" not in path.read_bytes()
    assert stale.read_text() == "STALE CORRUPT PAYLOAD"
    before = (target / "Today.md").read_bytes()
    with pytest.raises(FileExistsError):
        atomic_bytes(target / "Today.md", b"must not overwrite", staging_dir=state / "staging", create_only=True)
    assert (target / "Today.md").read_bytes() == before


@pytest.mark.parametrize("options", [{}, {"dry_run": True}, {"refresh": True},
                                    {"create_root_notes": True}])
@pytest.mark.parametrize("populated", [False, True])
def test_retired_mobile_rejected_without_mutation(tmp_path, options, populated):
    source = tmp_path / "Main"
    (source / ".obsidian").mkdir(parents=True)
    put(source, "Research/note.md", "Canonical")
    target = tmp_path / "Gallop-Mobile"
    state = tmp_path / "old-state"
    if populated:
        put(target, "Today.md", "Keep old mirror")
        put(state, "receipt.json", json.dumps({"source": str(source),
            "target": str(target), "files": ["Today.md"]}))
    before = snapshot(tmp_path)
    existed = target.exists(), state.exists()
    with pytest.raises(ValueError, match="Export target must be Gallop-Reader"):
        export_mobile(source, target, state, **options)
    assert snapshot(tmp_path) == before
    assert (target.exists(), state.exists()) == existed
