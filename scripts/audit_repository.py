"""Scan tracked blobs across reachable history; report locations, never secrets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

MACHINE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
COMMIT_OID = re.compile(r"[0-9a-f]{40}")
ACCEPTED_DEBT_PATH = Path(__file__).with_name("privacy-accepted-debt.json")


def public_commit_email(address: str) -> bool:
    """Allow GitHub's public author identities and synthetic PR merge identity."""
    return address.endswith("@users.noreply.github.com") or address == "noreply" + "@github.com"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8", errors="replace")


def accepted_metadata_debt(path: Path = ACCEPTED_DEBT_PATH) -> set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (set(data) != {"schema_version", "accepted_non_noreply_commits"}
            or data["schema_version"] != "1.0"
            or not isinstance(data["accepted_non_noreply_commits"], list)
            or any(not isinstance(oid, str) or not COMMIT_OID.fullmatch(oid)
                   for oid in data["accepted_non_noreply_commits"])
            or len(set(data["accepted_non_noreply_commits"])) != len(data["accepted_non_noreply_commits"])):
        raise ValueError("Invalid privacy accepted-debt baseline")
    return set(data["accepted_non_noreply_commits"])


def metadata_findings(records: list[tuple[str, str, str]], accepted: set[str]) -> list[dict]:
    offenders = {
        oid for oid, author, committer in records
        if not public_commit_email(author) or not public_commit_email(committer)
    }
    findings = [
        {"path": "<commit-metadata>", "rule": "non-noreply-email", "commit": oid}
        for oid in sorted(offenders - accepted)
    ]
    findings.extend(
        {"path": "<commit-metadata>", "rule": "stale-accepted-metadata-debt", "commit": oid}
        for oid in sorted(accepted - offenders)
    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forbid", action="append", default=[])
    args = parser.parse_args()
    patterns = {
        "machine-path": MACHINE_PATH,
        "provider-secret": re.compile(r"(?:gh[pousr]_|github_pat_|sk-proj-)[A-Za-z0-9_-]{20,}"),
        "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    }
    findings = []
    seen = set()
    public_url = "https://github.com/" + "lucaschang2021/gallop"
    for line in git("rev-list", "--objects", "--all").splitlines():
        oid, _, path = line.partition(" ")
        if oid in seen or git("cat-file", "-t", oid).strip() != "blob":
            continue
        seen.add(oid)
        raw = subprocess.check_output(["git", "cat-file", "blob", oid])
        if len(raw) > 1_000_000 or b"\x00" in raw:
            findings.append({"path": path, "rule": "unexpected-binary-or-large-blob"})
            continue
        body = raw.decode("utf-8", errors="replace").replace(public_url, "")
        for rule, pattern in patterns.items():
            if pattern.search(body):
                findings.append({"path": path, "rule": rule})
        for forbidden in args.forbid:
            if forbidden.casefold() in body.casefold():
                findings.append({"path": path, "rule": "private-string"})
        if path.startswith(("data/", "vault/", "learning-os/")):
            findings.append({"path": path, "rule": "private-data-directory"})
    records = []
    for line in git("log", "--all", "--format=%H%x00%ae%x00%ce").splitlines():
        oid, author, committer = line.split("\0")
        records.append((oid, author, committer))
    try:
        accepted = accepted_metadata_debt()
    except (OSError, ValueError, json.JSONDecodeError):
        findings.append({"path": str(ACCEPTED_DEBT_PATH.name),
                         "rule": "invalid-accepted-metadata-debt"})
    else:
        findings.extend(metadata_findings(records, accepted))
    print(json.dumps({"blobs_scanned": len(seen), "findings": findings,
                      "scope": "all reachable refs; metadata email check"}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
