import json
import subprocess

import pytest

from gallop.adapters.deeptutor import DeepTutorAdapter, DeepTutorUnavailable


def test_extracts_real_161_metadata_and_uses_actual_cli(tmp_path, manifest):
    executable = tmp_path / "deeptutor.exe"
    executable.touch()
    questions = [{"qa_pair": {"question": f"Question {i}", "correct_answer": "A"}}
                 for i in range(7)]
    output = json.dumps({"type": "result", "metadata": {"summary": {"success": True, "results": questions}}})
    def runner(command, **kwargs):
        assert command[1:3] == ["run", "deep_question"]
        assert "--prompt" not in command and "--json" not in command
        assert command[-2:] == ["--format", "json"]
        assert json.loads(command[command.index("--config-json") + 1])["num_questions"] == 7
        assert "source_notes" not in command[3]
        assert kwargs["shell"] is False and kwargs["timeout"] == 900
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")
    practice = DeepTutorAdapter(executable, runner=runner).generate(manifest)
    assert len(practice["questions"]) == 7
    assert "correct_answer" not in practice["questions"][0]
    assert practice["answer_key"][0]["correct_answer"] == "A"


def test_unavailable_executable_fails_loudly(tmp_path, manifest):
    with pytest.raises(DeepTutorUnavailable, match="unavailable"):
        DeepTutorAdapter(tmp_path / "missing").generate(manifest)


def test_nonzero_exit_never_exposes_provider_stderr(tmp_path, manifest):
    executable = tmp_path / "deeptutor.exe"
    executable.touch()
    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 3, stdout="", stderr="PRIVATE_PROVIDER_VALUE")
    with pytest.raises(DeepTutorUnavailable) as error:
        DeepTutorAdapter(executable, runner=runner).generate(manifest)
    assert "PRIVATE_PROVIDER_VALUE" not in str(error.value)


@pytest.mark.parametrize("wrapper", ["metadata_json", "payload", "content", "data", "result"])
def test_result_wrappers(wrapper):
    value = {"summary": {"results": [{"qa_pair": {"question": "Synthetic?"}}]}}
    event = {wrapper: json.dumps(value) if wrapper.endswith("json") else value}
    assert len(DeepTutorAdapter._extract(json.dumps(event))["questions"]) == 1


def test_nonobjects_and_empty_questions_rejected():
    with pytest.raises(ValueError):
        DeepTutorAdapter._extract('null\n[]\n{"summary":{"results":[{"id":"empty"}]}}')


def test_timeout_has_safe_error(tmp_path, manifest):
    executable = tmp_path / "deeptutor"
    executable.touch()
    def runner(*args, **kwargs):
        raise subprocess.TimeoutExpired("private-command", 1)
    with pytest.raises(DeepTutorUnavailable, match="timed out"):
        DeepTutorAdapter(executable, runner=runner).generate(manifest)
