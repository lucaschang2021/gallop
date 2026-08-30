import json
import subprocess

import pytest

from gallop.adapters.deeptutor import DeepTutorAdapter, DeepTutorUnavailable


def test_extracts_result_from_metadata_json(tmp_path):
    executable = tmp_path / "deeptutor.exe"
    executable.touch()
    output = json.dumps({"metadata_json": json.dumps({"summary": {"results": [{"id": "q1"}]}})})

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, stdout=output, stderr="")

    practice = DeepTutorAdapter(executable, runner=runner).generate({"manifest_id": "m1"})
    assert practice["questions"] == [{"id": "q1"}]


def test_unavailable_executable_fails_loudly(tmp_path):
    with pytest.raises(DeepTutorUnavailable, match="unavailable"):
        DeepTutorAdapter(tmp_path / "missing").generate({"manifest_id": "m1"})


def test_nonzero_exit_preserves_recoverable_error(tmp_path):
    executable = tmp_path / "deeptutor.exe"
    executable.touch()

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 3, stdout="", stderr="offline")

    with pytest.raises(DeepTutorUnavailable, match="offline"):
        DeepTutorAdapter(executable, runner=runner).generate({"manifest_id": "m1"})

