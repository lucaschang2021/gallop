"""Evidence-backed capability gains."""
from .evidence import capability_state, entries_for
from .models import CAPABILITY_STATES, SCAFFOLDING
from .primitives import digest
from .scaffolding import recommended_scaffolding


def calculate_gains(state, subject, dimension, dimension_catalog):
    entries = entries_for(state, subject, dimension, dimension_catalog)
    result = []
    previous = 'UNKNOWN'
    previous_scaffold = 'S5'
    previous_hint = None
    previous_hint_event = None
    for index, entry in enumerate(entries):
        current, *_ = capability_state(entries[:index + 1])
        scaffold, _ = recommended_scaffolding(entries[:index + 1])
        if CAPABILITY_STATES.index(current) > CAPABILITY_STATES.index(previous):
            result.append({'gain_id': 'gain-' + digest([entry['event_id'], current])[:24],
                           'subject': subject, 'dimension': dimension, 'before': previous, 'after': current,
                           'description': f'{dimension} moved from {previous} to {current}',
                           'at': entry['record']['occurred_at'], 'evidence_refs': [entry['event_id']]})
            previous = current
        if SCAFFOLDING.index(scaffold) > SCAFFOLDING.index(previous_scaffold):
            result.append({'gain_id': 'gain-' + digest([entry['event_id'], scaffold])[:24],
                           'subject': subject, 'dimension': dimension, 'before': previous_scaffold, 'after': scaffold,
                           'description': f'Designed support faded from {previous_scaffold} to {scaffold}',
                           'at': entry['record']['occurred_at'], 'evidence_refs': [entry['event_id']]})
            previous_scaffold = scaffold
        hint = (entry['record'].get('hint_level')
                if entry['confirmed'] and entry['record']['result'] == 'PASS' else None)
        if hint is not None and previous_hint is not None and hint < previous_hint:
            result.append({'gain_id': 'gain-' + digest([entry['event_id'], 'hint', hint])[:24],
                           'subject': subject, 'dimension': dimension,
                           'before': f'HINT_{previous_hint}', 'after': f'HINT_{hint}',
                           'description': f'Observed hint use decreased from level {previous_hint} to level {hint}',
                           'at': entry['record']['occurred_at'],
                           'evidence_refs': [previous_hint_event, entry['event_id']]})
        if hint is not None:
            previous_hint, previous_hint_event = hint, entry['event_id']
    return result
