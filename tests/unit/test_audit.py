import runpy
from pathlib import Path

AUDIT = runpy.run_path(str(Path(__file__).parents[2] / "scripts/audit_repository.py"))


def test_audit_distinguishes_urls_from_machine_paths():
    assert not AUDIT["MACHINE_PATH"].search("https://example.org/license")


def test_audit_detects_drive_paths():
    assert AUDIT["MACHINE_PATH"].search("X" + ":/example")


def test_github_merge_metadata_is_public_but_personal_email_is_rejected():
    assert AUDIT["public_commit_email"]("noreply" + "@github.com")
    assert AUDIT["public_commit_email"]("123+example" + "@users.noreply.github.com")
    assert not AUDIT["public_commit_email"]("example" + "@private.invalid")
