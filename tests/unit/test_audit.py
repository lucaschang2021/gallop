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


def test_accepted_metadata_debt_is_exact_and_does_not_allow_new_violations():
    old = "1" * 40
    new = "2" * 40
    records = [
        (old, "historical" + "@private.invalid", "noreply" + "@github.com"),
        (new, "new" + "@private.invalid", "noreply" + "@github.com"),
    ]
    assert AUDIT["metadata_findings"](records, {old}) == [
        {"path": "<commit-metadata>", "rule": "non-noreply-email", "commit": new}
    ]


def test_resolved_metadata_debt_must_be_removed_from_baseline():
    old = "1" * 40
    records = [(old, "noreply" + "@github.com", "noreply" + "@github.com")]
    assert AUDIT["metadata_findings"](records, {old}) == [
        {"path": "<commit-metadata>", "rule": "stale-accepted-metadata-debt", "commit": old}
    ]
