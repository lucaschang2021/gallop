import json

import pytest

from gallop.adapters.mock import DemoPracticeEngine
from gallop.adapters.obsidian import ObsidianAdapter
from gallop.core.sync import GallopPipeline
from gallop.core.sync.logging import SyncLogger
from gallop.core.validation import ProtocolValidationError


def test_invalid_manifest_fails_before_practice_engine(tmp_path):
    pipeline = GallopPipeline(ObsidianAdapter(tmp_path), DemoPracticeEngine())
    with pytest.raises(ProtocolValidationError, match="validation failed"):
        pipeline.generate_practice({"manifest_id": "incomplete"})


def test_sync_log_contains_metadata_not_manifest_body(tmp_path):
    log_path = tmp_path / "sync.jsonl"
    pipeline = GallopPipeline(
        ObsidianAdapter(tmp_path / "vault"), DemoPracticeEngine(), logger=SyncLogger(log_path)
    )
    manifest = json.loads(
        (__import__("pathlib").Path(__file__).parents[2] / "examples" / "mathematics" / "practice-manifest.json").read_text(encoding="utf-8")
    )
    pipeline.generate_practice(manifest)
    record = json.loads(log_path.read_text(encoding="utf-8"))
    assert record["manifest_id"] == "manifest-public-demo-001"
    assert "quantifier-order" not in log_path.read_text(encoding="utf-8")
