"""Scan tracked blobs across reachable history; report locations, never secrets."""

from __future__ import annotations

import argparse
import json
import re
import subprocess

MACHINE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True, encoding="utf-8", errors="replace")


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
    emails = git("log", "--all", "--format=%ae%n%ce").splitlines()
    if any(not address.endswith("@users.noreply.github.com") for address in emails):
        findings.append({"path": "<commit-metadata>", "rule": "non-noreply-email"})
    print(json.dumps({"blobs_scanned": len(seen), "findings": findings,
                      "scope": "all reachable refs; metadata email check"}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
