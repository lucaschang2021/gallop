import json
from pathlib import Path

from gallop.cli import main
from gallop.core.validation import validate_protocol

ROOT = Path(__file__).parents[2]


def test_quickstart_commands(tmp_path):
    session = ROOT / "examples/mathematics/session.json"
    result = ROOT / "examples/mathematics/practice-result.json"
    vault = tmp_path / "vault"
    manifest = tmp_path / "manifest.json"
    assert main(["sync-session", str(session), "--vault", str(vault)]) == 0
    assert main(["manifest", str(session), "--output", str(manifest)]) == 0
    validate_protocol("practice-manifest.schema.json", json.loads(manifest.read_text()))
    assert main(["import-result", str(result), "--vault", str(vault)]) == 0
    assert main(["import-result", str(result), "--vault", str(vault)]) == 0
    assert list((vault / "Gallop/Sessions").glob("*.md"))
    assert len(list((vault / "Gallop/Practice/integration_tests").glob("*.md"))) == 1


def test_invalid_cli_input_nonzero_without_echo(tmp_path, capsys):
    source = tmp_path / "invalid.json"
    source.write_text('{"private":"DO_NOT_PRINT_ME"}')
    assert main(["import-result", str(source), "--vault", str(tmp_path / "vault")]) == 1
    assert "DO_NOT_PRINT_ME" not in capsys.readouterr().err


def test_live_demo_requires_explicit_opt_in(tmp_path):
    assert main(["live-demo", "--output", str(tmp_path), "--deeptutor", "missing"]) == 1
    assert not (tmp_path / "practice.json").exists()
