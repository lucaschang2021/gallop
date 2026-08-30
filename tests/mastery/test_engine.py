import pytest

from gallop.core.mastery import MasteryEngine
from gallop.core.models import MasteryEvidence


def test_single_quiz_never_awards_level_five():
    decision = MasteryEngine().evaluate(4, MasteryEvidence(10, 10, independent=True))
    assert decision.current == 4


def test_guided_pass_reaches_basic_not_robust():
    decision = MasteryEngine().evaluate(1, MasteryEvidence(4, 6, hints_used=1))
    assert decision.current == 2


def test_weak_result_can_lower_overconfidence():
    decision = MasteryEngine().evaluate(3, MasteryEvidence(1, 5, independent=True))
    assert decision.current == 2


def test_zero_questions_does_not_change_mastery():
    decision = MasteryEngine().evaluate(2, MasteryEvidence(0, 0))
    assert decision.current == 2


def test_robust_mastery_requires_all_durable_evidence():
    evidence = MasteryEvidence(
        9, 10, independent=True, delayed_recall=True, transfer_success=True,
        oral_explanation=True, repeated_successes=2,
    )
    assert MasteryEngine().evaluate(4, evidence).current == 5


def test_invalid_evidence_is_rejected():
    with pytest.raises(ValueError, match="correct cannot exceed attempted"):
        MasteryEngine().evaluate(1, MasteryEvidence(2, 1))

