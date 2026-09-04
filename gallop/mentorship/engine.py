"""Compatibility facade from application state to the pure progression domain."""
from gallop.progression import ProgressionContext, calculate_capability, decide
from gallop.progression.engine import weekly_feedback as domain_weekly_feedback

from .policy import READINESS_DIMENSIONS, subject_policy


def capability(state, subject, dimension):
    return calculate_capability(state, subject, dimension, READINESS_DIMENSIONS)


def plan(state, target_entry):
    subject = target_entry['record']['subject']
    return decide(ProgressionContext(state=state, target_entry=target_entry,
                                     subject_policy=subject_policy(subject),
                                     dimension_catalog=READINESS_DIMENSIONS))


def weekly_feedback(state, plans):
    del state  # Kept for the RC2 public-call shape; decisions depend only on plans.
    return domain_weekly_feedback(plans)
