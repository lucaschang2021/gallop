import json

from gallop.cli import run_demo


def test_demo_round_trip_does_not_touch_learner_state(tmp_path):
    report = run_demo(tmp_path)
    assert report["questions"] == 7
    assert report["score"] == "5/7"
    assert report["mastery"] == "1 -> 2"
    state = json.loads((tmp_path / ".gallop" / "mastery.json").read_text(encoding="utf-8"))
    assert "integration_tests" in state["topics"]
    assert "learner" not in state["topics"]
