"""Immutable vocabulary and explicit inputs for progression decisions."""
from dataclasses import dataclass
from typing import Mapping, Any

CAPABILITY_STATES = ('UNKNOWN', 'EXPOSED', 'GUIDED', 'PARTIALLY_INDEPENDENT',
                     'INDEPENDENT', 'TRANSFERRED', 'RETAINED', 'RESEARCH_USABLE')
ZONES = ('FOUNDATION', 'PRODUCTIVE', 'STRETCH', 'MONSTER_BENCHMARK')
SCAFFOLDING = ('S5', 'S4', 'S3', 'S2', 'S1', 'S0')
ACTIONS = ('MAINTAIN', 'REDUCE_SCAFFOLDING', 'INCREASE_NOVELTY', 'INCREASE_DIFFICULTY',
           'ADD_TRANSFER_TEST', 'ADD_RETENTION_TEST', 'REPAIR_PREREQUISITE', 'RETEST_TARGET',
           'REDUCE_TASK_SPAN', 'MOVE_TO_ASSESSMENT', 'MOVE_TO_RESEARCH_MODE')
STRUGGLE = ('PRODUCTIVE_FAILURE', 'PREREQUISITE_FAILURE', 'OVERCHALLENGE',
            'CARELESS_FAILURE', 'CONCEPTUAL_FAILURE', 'UNKNOWN')
MENTOR_ROLES = ('TEACHER', 'COACH', 'DOMAIN_MENTOR', 'RESEARCH_SUPERVISOR', 'EVALUATOR')
RESEARCH_STATES = ('RI0', 'RI1', 'RI2', 'RI3', 'RI4', 'RI5', 'RI6')


@dataclass(frozen=True)
class ProgressionContext:
    """All data needed by the domain; clocks, stores and adapters stay outside."""

    state: Mapping[str, Any]
    target_entry: Mapping[str, Any]
    subject_policy: Mapping[str, Any]
    dimension_catalog: Mapping[str, Any]
