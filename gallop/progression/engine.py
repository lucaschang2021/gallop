"""Pure composition of progression decisions."""
from datetime import timedelta

from .capability import calculate_capability
from .evidence import entries_for
from .gains import calculate_gains
from .mentor_role import determine_mentor_role
from .models import ProgressionContext
from .prerequisites import diagnose_prerequisites
from .primitives import timestamp
from .struggle import classify_struggle
from .zones import determine_zone


def decide(context: ProgressionContext):
    target = context.target_entry['record']
    subject, dimension = target['subject'], target['dimension']
    current = calculate_capability(context.state, subject, dimension, context.dimension_catalog)
    entries = entries_for(context.state, subject, dimension, context.dimension_catalog)
    gaps = diagnose_prerequisites(context.state, context.target_entry, entries)
    struggles = classify_struggle(entries, gaps)
    state_name = current['current_state']
    action, zone, design = determine_zone(state_name, entries, gaps, struggles)
    return {'target': target, 'current_capability': current, 'training_zone': zone,
            'scaffolding_level': current['recommended_scaffolding'], 'progression_action': action,
            'progression_reason': f'Evidence-backed {state_name}; target {target["target_state"]} does not set current capability',
            'prerequisite_gaps': gaps, 'productive_struggle': struggles,
            'capability_gains': calculate_gains(context.state, subject, dimension, context.dimension_catalog),
            'mentor_role': determine_mentor_role(state_name, context.subject_policy),
            'research_independence': current['research_independence'],
            'task_design': {**design, 'independence_destination': 'INDEPENDENT'},
            'subject_policy_reference': {key: value for key, value in context.subject_policy.items()
                                         if key != 'mentor_labels'},
            'queue_mutation': 'NONE', 'north_star': target['north_star']}


def weekly_feedback(plans):
    gains = [gain for plan in plans for gain in plan['capability_gains']]
    if not gains:
        return {'heading': 'This Week You Gained', 'items': [], 'evidence_refs': []}
    end = max(timestamp(gain['at']) for gain in gains)
    start = end - timedelta(days=6)
    recent = [gain for gain in gains if timestamp(gain['at']) >= start]
    return {'heading': 'This Week You Gained', 'items': [gain['description'] for gain in recent],
            'evidence_refs': [ref for gain in recent for ref in gain['evidence_refs']]}
